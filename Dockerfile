###############################################
# Base Stage
###############################################
FROM python:3.11-slim as base

ARG APP_SERVICE_HOSTNAME \
    APP_API_KEY \
    APP_WSGI_APP_PATH \
    APP_WSGI_HOST \
    APP_WSGI_PORT \
    APP_WSGI_RELOAD \
    APP_WSGI_WORKERS \
    APP_DOCS_USERNAME\
    APP_DOCS_PASSWORD \
    REDIS_HOST \
    REDIS_PORT \
    REDIS_DB_NAME \
    REDIS_PASSWORD \
    MQ_HOST \
    MQ_USERNAME \
    MQ_PASSWORD \
    MQ_PORT \
    POSTGRES_HOST \
    POSTGRES_USERNAME \
    POSTGRES_PASSWORD \
    POSTGRES_PORT \
    POSTGRES_DB_NAME \
    POSTGRES_SCHEMA_NAME \
    USER_ADDRESS_URL \
    USER_PROFILE_URL \
    CART_PRODUCTS \
    S3_URL \
    S3_REGION \
    S3_ACCESS_KEY \
    S3_SECRET_KEY \
    S3_BUCKET_PRIVATE \
    S3_BUCKET_PUBLIC \
    S3_LOCAL_FOLDER \
    ECOM_SELLER_CHECK_URL \
    ECOM_SELLER_DATA_URL \
    ECOM_PRODUCT_STORAGE_AMOUNT_URL

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv" \
    APP_SERVICE_HOSTNAME=${APP_SERVICE_HOSTNAME} \
    APP_API_KEY=${APP_API_KEY} \
    APP_WSGI_APP_PATH=${APP_WSGI_APP_PATH:-app.main:app} \
    APP_WSGI_HOST=${APP_WSGI_HOST:-0.0.0.0} \
    APP_WSGI_PORT=${APP_WSGI_PORT:-80} \
    APP_WSGI_RELOAD=${APP_WSGI_RELOAD:-false} \
    APP_WSGI_WORKERS=${APP_WSGI_WORKERS:-1} \
    APP_DOCS_USERNAME=${APP_DOCS_USERNAME:-"admin"} \
    APP_DOCS_PASSWORD=${APP_DOCS_PASSWORD:-"password"} \
    REDIS_HOST=${REDIS_HOST:-0.0.0.0} \
    REDIS_PORT=${REDIS_PORT:-6379} \
    REDIS_DB_NAME=${REDIS_DB_NAME:-0} \
    REDIS_PASSWORD=${REDIS_PASSWORD} \
    MQ_HOST=${MQ_HOST} \
    MQ_USERNAME=${MQ_USERNAME} \
    MQ_PASSWORD=${MQ_PASSWORD} \
    MQ_PORT=${MQ_PORT}\
    POSTGRES_HOST=${POSTGRES_HOST} \
    POSTGRES_USERNAME=${POSTGRES_USERNAME} \
    POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
    POSTGRES_PORT=${POSTGRES_PORT} \
    POSTGRES_DB_NAME=${POSTGRES_DB_NAME} \
    POSTGRES_SCHEMA_NAME=${POSTGRES_SCHEMA_NAME} \
    USER_ADDRESS_URL=${USER_ADDRESS_URL} \
    USER_PROFILE_URL=${USER_PROFILE_URL} \
    CART_PRODUCTS=${CART_PRODUCTS} \
    S3_URL=${S3_URL} \
    S3_REGION=${S3_REGION} \
    S3_ACCESS_KEY=${S3_ACCESS_KEY} \
    S3_SECRET_KEY=${S3_SECRET_KEY} \
    S3_BUCKET_PRIVATE=${S3_BUCKET_PRIVATE} \
    S3_BUCKET_PUBLIC=${S3_BUCKET_PUBLIC} \
    S3_LOCAL_FOLDER=${S3_LOCAL_FOLDER} \
    ECOM_SELLER_CHECK_URL=${ECOM_SELLER_CHECK_URL} \
    ECOM_SELLER_DATA_URL=${ECOM_SELLER_DATA_URL} \
    ECOM_PRODUCT_STORAGE_AMOUNT_URL=${ECOM_PRODUCT_STORAGE_AMOUNT_URL}

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

###############################################
# Build Stage
###############################################
FROM base as build

# RUN sed -i -e 's/http:\/\/deb\.debian\.org\/debian/http:\/\/mirror\.yandex\.ru\/debian/g' /etc/apt/sources.list

RUN BUILD_DEPS="build-essential libpq-dev curl" \
    && apt-get update \
    && apt-get install --no-install-recommends -y $BUILD_DEPS \
    && apt-get clean all

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -sSL https://install.python-poetry.org | python - \
    && chmod a+x "$POETRY_HOME/bin/poetry"

WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./

RUN poetry install --only main --no-root --verbose

###############################################
# Development Stage
###############################################
FROM base as development

ARG USER_UID \
    USER_GID

ENV USER_UID=${USER_UID:-1500} \
    USER_GID=${USER_GID:-1500} \
    APP_ENVIRONMENT=development

COPY --from=build $PYSETUP_PATH $PYSETUP_PATH
COPY --from=build $POETRY_HOME $POETRY_HOME
COPY --from=build $VENV_PATH $VENV_PATH

COPY ./docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh
RUN groupadd -g $USER_GID app \
    && useradd -m -u $USER_UID -g app app

WORKDIR $PYSETUP_PATH
RUN poetry install --no-root --verbose

COPY --chown=app:app . /workspace
USER app
WORKDIR /workspace/

EXPOSE 5050
ENTRYPOINT /docker-entrypoint.sh $0 $@
CMD ["uvicorn", "app.main:app", "--reload", "--host=0.0.0.0", "--port=5050"]

###############################################
# Lint Stage
###############################################
FROM build AS lint

ENV APP_ENVIRONMENT=linting

WORKDIR $PYSETUP_PATH
RUN poetry install --no-root --quiet

WORKDIR /app/
COPY . .

CMD ["make", "lint"]

###############################################
# Test Stage
###############################################
FROM build AS test

ENV APP_ENVIRONMENT=testing

WORKDIR $PYSETUP_PATH
RUN poetry install --no-root --quiet

WORKDIR /app/
COPY . .

CMD ["make", "test"]

###############################################
# Production Stage
###############################################
FROM base as production

ARG USER_UID \
    USER_GID

ENV USER_UID=${USER_UID:-1500} \
    USER_GID=${USER_GID:-1500} \
    APP_ENVIRONMENT=production

COPY --from=build $VENV_PATH $VENV_PATH

COPY gunicorn.conf.py docker-entrypoint.sh /

RUN chmod +x /docker-entrypoint.sh
RUN groupadd -g $USER_GID app \
    && useradd -m -u $USER_UID -g app app

COPY --chown=app:app . /app
USER app
WORKDIR /app

EXPOSE 80
ENTRYPOINT /docker-entrypoint.sh $0 $@
CMD ["gunicorn", "app.main:app", "--config=/gunicorn.conf.py"]
