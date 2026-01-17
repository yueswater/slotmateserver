.PHONY: install run migrations migrate superuser shell format

install:
	poetry install

run:
	poetry run python manage.py runserver

migrations:
	poetry run python manage.py makemigrations

migrate:
	poetry run python manage.py migrate

superuser:
	poetry run python manage.py createsuperuser

shell:
	poetry run python manage.py shell

format:
	poetry run black .
	poetry run isort .

tree:
	tree -I "migrations|__pycache__|*.jpg"