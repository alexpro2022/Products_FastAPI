import json
from logging import ERROR
from typing import Any

from aio_pika import DeliveryMode, Exchange, ExchangeType, Message, connect_robust
from aio_pika.abc import AbstractIncomingMessage, AbstractRobustConnection
from backoff import expo, on_exception

from app.core.config import settings


class RabbitMQ:
    def __init__(self) -> None:
        self.host: str = settings.mq_settings.host
        self.username: str | None = settings.mq_settings.username
        self.password: str | None = settings.mq_settings.password

        self.message: None

    async def get_connection(self) -> AbstractRobustConnection:
        params: dict[str, Any] = {
            "host": self.host,
            "timeout": 10,
        }

        if self.username and self.password:
            params["login"] = self.username
            params["password"] = self.password

        return await connect_robust(**params)

    async def get_channel(self, connection) -> Any:
        return await connection.channel()

    async def connect(self) -> None:
        self.connection = await self.get_connection()
        self.channel = await self.get_channel(self.connection)

    async def close_connections(self) -> None:
        await self.connection.close()

    @on_exception(
        wait_gen=expo,
        exception=(Exception,),
        max_tries=5,
        backoff_log_level=ERROR,
    )
    async def send_message(
        self,
        body: bytes,
        headers: dict[str, Any] | None = None,
        routing_key: str | None = None,
    ) -> None:
        connection = await self.get_connection()
        channel = await self.get_channel(connection=connection)
        name: str = routing_key or "parse_xml.updated"
        body_str = json.dumps(body)
        body_bytes = body_str.encode("utf-8")

        message: Message = Message(
            body=body_bytes,
            headers=headers,
            delivery_mode=DeliveryMode.PERSISTENT,
        )

        exchange: Exchange = await channel.declare_exchange(
            name="exchange",
            type=ExchangeType.DIRECT,
            auto_delete=False,
            durable=True,
        )

        queue1 = await channel.declare_queue(name, durable=True)
        queue2 = await channel.declare_queue("prod_comparison.updated", durable=True)

        # Bind the queue to the exchange
        await queue1.bind(exchange, routing_key=name)
        await queue2.bind(exchange, routing_key="prod_comparison.updated")

        # Publish the message
        if routing_key == name and routing_key == "prod_comparison.updated":
            await exchange.publish(message, routing_key=name)
            await exchange.publish(message, routing_key="prod_comparison.updated")
        elif routing_key == "prod_comparison.updated":
            await exchange.publish(message, routing_key="prod_comparison.updated")

    async def on_message(self, message: AbstractIncomingMessage) -> None:
        print(" [x] Received message %r" % message)
        print("Message body is: %r" % message.body)
        self.message = (message.body).decode("utf-8")

    async def consume(self) -> None:
        connection = await self.get_connection()
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue("parse_xml.updated", durable=True)
            await queue.consume(self.on_message, no_ack=True)
            print(" [*] Waiting for messages. To exit press CTRL+C")
