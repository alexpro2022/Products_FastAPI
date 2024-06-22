ifdef OS
   command = python
else
   command = python3
endif

# Для dev
volumes-clear-dev: # Удаление Volumes для dev
	docker compose -f docker-compose-dev.yml down --volumes

container-start-dev: # Запуск контейнеров для dev
	docker compose -f docker-compose-dev.yml up -d;
	@sleep 5;

db-init-dev: # Инициализация БД для dev
	poetry run $(command) prestart.py
	poetry run alembic upgrade head
	poetry run $(command) populate_db/populate_db.py
	poetry run $(command) populate_db/mock_data_db.py

fastapi-start-dev: # Запуск FastAPI для dev
	poetry run uvicorn app.main:app --reload --host=0.0.0.0 --port=5051

service-init-dev: # Инициализация сервиса для dev
	make volumes-clear-dev container-start-dev db-init-dev fastapi-start-dev

service-start-dev: # Запуск сервиса для dev
	make container-start-dev fastapi-start-dev
