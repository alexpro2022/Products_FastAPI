FROM python:3.11-slim

WORKDIR /app

COPY poetry.lock pyproject.toml /app/
RUN python -m pip install --no-cache-dir poetry==1.8.3 && \
    poetry config virtualenvs.create false && \
    poetry install --without dev --no-interaction --no-ansi && \
    rm -rf $(poetry config cache-dir)/{cache,artifacts}

COPY tests/requirements.txt requirements.txt
RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt --no-cache-dir
COPY tests/pytest.ini .

COPY . .
