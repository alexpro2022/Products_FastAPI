from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_host: str | None = "test"
    service_port: str | None = "80"
    service_version: str | None = "v3"
    service_name: str | None = "products"

    api_key: str = ""

    database_username: str
    database_password: str
    database_host: str
    database_port: str
    database_name: str

    redis_host: str
    redis_port: str
    redis_db_name: str = "test_redis"
    redis_password: str = "redispw"

    # sqlalchemy_database_url: str = "sqlite:///test_database.db"

    @property
    def test_service_dsn(
        self,
    ) -> str:
        return "http://test"
        """return "http://{}:{}/{}/api/{}".format(
            self.service_host,
            self.service_port,
            self.service_name,
            self.service_version,
        )"""

    @property
    def sqlalchemy_database_url(self) -> str:
        return "postgresql+asyncpg://{}:{}@{}:{}/{}".format(
            self.database_username, self.database_password, self.database_host, self.database_port, self.database_name
        )

    @property
    def redis_dsn(self) -> str:
        return "redis://{}:{}".format(self.redis_host, self.redis_port)
        """return "redis://:{}@{}:{}/{}".format(
            self.redis_password,
            self.redis_host,
            self.redis_port,
            self.redis_db_name
        )"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow", env_prefix="TEST_")


settings: Settings = Settings()
