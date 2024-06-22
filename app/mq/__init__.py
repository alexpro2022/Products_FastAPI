from app.mq.rabbitmq import RabbitMQ


class MQ:
    def __init__(
        self,
    ) -> None:
        self.rabbitmq: RabbitMQ = RabbitMQ()


mq: MQ = MQ()


def get_rabbitmq() -> RabbitMQ:
    return mq.rabbitmq
