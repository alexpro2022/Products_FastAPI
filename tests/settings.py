from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow", env_prefix="TEST_")

    database_username: str
    database_password: str
    database_host: str
    database_port: str
    database_name: str

    redis_host: str
    redis_port: str

    @property
    def test_service_dsn(
        self,
    ) -> str:
        return "http://test"

    @property
    def sqlalchemy_database_url(self) -> str:
        return "postgresql+asyncpg://{}:{}@{}:{}/{}".format(
            self.database_username, self.database_password, self.database_host, self.database_port, self.database_name
        )

    @property
    def redis_dsn(self) -> str:
        return "redis://{}:{}".format(self.redis_host, self.redis_port)


settings: Settings = Settings()
