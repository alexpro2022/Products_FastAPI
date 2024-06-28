# MP_FastAPI_Products

[![Run pytest](https://github.com/Salfa-marketplace/MP_FastAPI_Products/actions/workflows/test.yml/badge.svg)](https://github.com/Salfa-marketplace/MP_FastAPI_Products/actions/workflows/test.yml)


<div align="center">
  <h1>MP_FastAPI_Products</h1>
</div>
<h3 align="center">Как запустить для разработки</h3>
<details>
  <p align="center"><summary align="center"><ins>Через Docker</ins></summary></p>
  <ul>
    <li align="center">
      <p>1. Установить poetry <code>pip install poetry</code>.</p>
    </li>
    <li align="center">
      <p>2. Создать и активировать виртуальную оболочку <code>poetry shell</code>.</p>
    </li>
    <li align="center">
      <p>3. Установить зависимости <code>poetry install</code>.</p>
    </li>
    <li align="center">4. Создать и заполнить файл <code>.env</code> в
      <b>корневой папке</b> по шаблону 
        <a href="https://github.com/salfa-ru/MP_FastAPI_Products/blob/develop/.env.sample"><code>.env.example</code></a>.
    </li>
    <li align="center">
      <p>5. Если имеется утилита <code>Make</code>, в <b>корне проекта</b> выполнить команду <code>make service-init-dev</code>,</p>
      <p>иначе</p>
      <p>выполнить команды:</p>
<p>

```bash
docker compose -f docker-compose-dev.yml down --volumes
docker compose -f docker-compose-dev.yml up -d
poetry run python prestart.py
poetry run alembic upgrade head
poetry run python populate_db/populate_db.py
poetry run uvicorn app.main:app --reload --host=0.0.0.0 --port=5051
```

</p>
<p><b>Итог выполнения команд</b></p>
  <p>Соберутся контейнеры с <code>postgreSQL</code>, <code>Redis</code> и <code>RabbitMQ</code>, создаcтся <b>схема</b>, выполнятся <b>миграции</b>, <b>БД</b> заполнится <code>moke-данными</code>,</p>
  <p>и сервер будет доступен по адрессу <code>http://127.0.0.1:5051/</code>.</p>
    </li>
    <li align="center">
      <p><b>Примечание</b></p>
      <p>В дальнейшем запускать проект через команду <code>make service-start-dev</code>.</p>
      <p>или</p>
<p>
          
```bash
docker compose -f docker-compose-dev.yml up -d
poetry run uvicorn app.main:app --reload --host=0.0.0.0 --port=5051
```

</p>
    </li>
  </ul>
</details>

<details>
  <p align="center"><summary align="center"><ins>Через консоль</ins></summary></p>
  <ul>
    <li align="center">1. Создать и заполнить файл <code>.env</code> в
      <b>корневой папке</b> по шаблону 
        <a href="https://github.com/salfa-ru/MP_FastAPI_Products/blob/develop/.env.sample"><code>.env.example</code></a>.
    </li>
    <li align="center">
      <p>2. Создать БД в <code>postgreSQL</code>.</p>
    </li>
    <li align="center">
      <p>3. Подключить <code>RabbitMQ</code> и <code>Redis</code>.</p>
    </li>
    <li align="center">
      <p>4. Установить poetry <code>pip install poetry</code>.</p>
    </li>
    <li align="center">
      <p>5. Создать и активировать виртуальную оболочку <code>poetry shell</code>.</p>
    </li>
    <li align="center">
      <p>6. Установить зависимости <code>poetry install</code>.</p>
    </li>
    </li>
        <li align="center">
      <p>7. Создать схему в БД <code>poetry run python prestart.py</code>.</p>
    </li>
    <li align="center">
      <p>8. Выполнить миграцию БД <code>poetry run alembic upgrade head</code>.</p>
    </li>
        <li align="center">
      <p>9. Заполнить БД тестовыми данными <code>poetry run python populate_db/populate_db.py</code><code>poetry run python populate_db/moke_data_db.py</code>.</p>
    </li>
    </li>
        <li align="center">
      <p>10. Запустить сервер <code>poetry run uvicorn app.main:app --reload --host=0.0.0.0 --port=5051</code>.</p>
    </li>
    <li align="center">
      <p>11. Сервер будет доступен по адрессу: <code>http://127.0.0.1:5051/</code>.</p>
    </li>
  </ul>
</details>

## Запуск тестов:
Из корневой директории проекта выполните команду запуска тестов:
```bash
docker compose -f tests/docker/test.docker-compose.yml --env-file tests/env_test up --build --abort-on-container-exit && \
docker compose -f tests/docker/test.docker-compose.yml --env-file tests/env_test down -v && \
docker rmi test_run
```
После прохождения тестов в консоль будет выведен отчет pytest и coverage.
