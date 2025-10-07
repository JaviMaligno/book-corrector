.PHONY: help install dev fmt lint test run docker-build docker-run

help:
	@echo "Targets: install dev fmt lint test run docker-build docker-run"

install:
	pip install --upgrade pip
	pip install .

dev:
	pip install --upgrade pip
	pip install .[dev]

fmt:
	black .
	ruff check --fix .

lint:
	ruff check .
	black --check .

test:
	pytest -q

run:
	uvicorn server.main:app --reload

docker-build:
	docker build -t corrector-api:dev .

docker-run:
	docker run --rm -p 8000:8000 \
	  -e DEMO_PLAN=$${DEMO_PLAN:-free} \
	  -e SYSTEM_MAX_WORKERS=$${SYSTEM_MAX_WORKERS:-2} \
	  corrector-api:dev

