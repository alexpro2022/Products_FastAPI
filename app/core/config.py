from multiprocessing import cpu_count

from dotenv import load_dotenv
from pydantic import ValidationInfo, field_validator
from pydantic.networks import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from app import __version__ as version

load_dotenv()


class Base(BaseSettings):
    model_config = SettingsConfigDict(extra="allow", env_file=".env", env_file_encoding="utf-8")


class AppSettings(Base):
    environment: str = "development"
    is_debug: bool | None = None
    log_level: str | None = None
    wsgi_app_path: str = "app.main:app"
    wsgi_host: str = "0.0.0.0"
    wsgi_port: str = "80"
    wsgi_reload: bool = False
    wsgi_workers: int = cpu_count()
    docs_name: str = "products"
    docs_version: str = version
    docs_username: str | None = None
    docs_password: str | None = None
    docs_basic_credentials: str | None = None
    pagination_default_size: int = 100
    pagination_maximum_size: int = 1000
    mix_code_length: int = 2
    max_code_length: int = 4
    code_length: int = 4
    code_expires: int = 20
    api_key: str = "HJSDhjhsdjakKJHKJ387^RhjskdJGkk2809jsalhd24="
    secret_key: str = "jhkjhaksjhdkjasdhkshd738687e&^W#KHjHhKCbh1127y6=="
    algoritm: str = "HS256"
    cache_expire: int = 86400

    @property
    def service_name(
        self,
    ) -> str:
        return self.docs_name

    @field_validator("is_debug", mode="before")
    @classmethod
    def build_is_debug(
        cls,
        value: bool | None,
        info: ValidationInfo,
    ) -> bool:
        if value is not None:
            return value

        return bool(info.data["environment"] == "development")

    @field_validator("log_level", mode="before")
    @classmethod
    def build_log_level(
        cls,
        value: str | None,
        info: ValidationInfo,
    ) -> str:
        if value is not None:
            return value

        return "DEBUG" if info.data["is_debug"] else "INFO"

    @field_validator("docs_basic_credentials", mode="before")
    @classmethod
    def build_basic_credentials(
        cls,
        value: str | None,
        info: ValidationInfo,
    ) -> str:
        if value is not None:
            return value

        credentials: list[str] = []

        if info.data["docs_username"]:
            credentials.append(
                info.data["docs_username"],
            )

        if info.data["docs_password"]:
            credentials.append(
                info.data["docs_password"],
            )

        return ":".join(credentials)

    model_config = SettingsConfigDict(env_prefix="APP_")


class RedisSettings(Base):
    protocol: str = "redis"
    host: str = "0.0.0.0"
    port: str = "6379"
    db_name: str = "0"
    password: str | None = None
    dsn: RedisDsn | str = ""

    @field_validator("dsn", mode="before")
    @classmethod
    def build_dsn(
        cls,
        value: RedisDsn | None,
        info: ValidationInfo,
    ) -> RedisDsn:
        if value is not None and value != "":
            return value

        redis_dsn: RedisDsn = RedisDsn(
            url="{}://:{}@{}:{}/{}".format(
                info.data["protocol"],
                info.data["password"],
                info.data["host"],
                info.data["port"],
                info.data["db_name"],
            )
        )

        return redis_dsn.unicode_string()

    model_config = SettingsConfigDict(env_prefix="REDIS_")


class PostgresSettings(Base):
    protocol: str = "postgresql+asyncpg"
    host: str = "0.0.0.0"
    port: str = "5432"
    db_name: str = ""
    schema_name: str = "products"
    username: str | None = None
    password: str | None = None
    extensions: list[str] | None = []
    dsn: str | None = ""

    @field_validator("dsn", mode="before")
    @classmethod
    def build_dsn(
        cls,
        value: PostgresDsn | None,
        info: ValidationInfo,
    ) -> PostgresDsn:
        if value is not None and value != "":
            return value

        postgres_dsn: PostgresDsn = PostgresDsn(
            url="{}://{}:{}@{}:{}/{}".format(
                info.data["protocol"],
                info.data["username"],
                info.data["password"],
                info.data["host"],
                info.data["port"],
                info.data["db_name"],
            ),
        )

        return str(postgres_dsn)

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")


class MQSettings(Base):
    host: str = "0.0.0.0"
    username: str | None = None
    password: str | None = None
    model_config = SettingsConfigDict(env_prefix="MQ_")


class ECOMSettings(Base):
    auth_url: str = "https://auth.sarawan.ru/api/v1/users/check-token"
    seller_check_url: str = "container link"
    search_service_url: str = "https://elastic.sarawan.ru/price"
    base_share_url: str = "https://prod.sarawan.ru/shopping_list/api/v1/share"
    model_config = SettingsConfigDict(env_prefix="ECOM_")


class S3Settings(Base):
    url: str = "0.0.0.0"
    region: str | None = None
    access_key: str | None = None
    secret_key: str | None = None
    bucket_private: str | None = None
    bucket_public: str | None = None
    model_config = SettingsConfigDict(env_prefix="S3_")


default_image_url = "https://s3.timeweb.cloud/48111b17-8a18978c-3998-45e6-a5d4-3d47d3e3cc72/default.svg"
image_sizes = {
    "preview_url": (680, 680),
    "mini_url": (64, 64),
    "small_url": (380, 380),
}


class Settings(BaseSettings):
    app_settings: AppSettings = AppSettings()
    postgres_settings: PostgresSettings = PostgresSettings()
    mq_settings: MQSettings = MQSettings()
    ecom_settings: ECOMSettings = ECOMSettings()
    s3_settings: S3Settings = S3Settings()
    redis_settings: RedisSettings = RedisSettings()


settings: Settings = Settings()
