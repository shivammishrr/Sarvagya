# Makefile convenience targets
.PHONY: install run dev test fmt lint docker-build docker-up docker-down

install:
	pip install -U pip
	pip install -e .[dev]

run:
	uvicorn src.main:app --host 0.0.0.0 --port 8000

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

fmt:
	black src tests

lint:
	ruff check src tests

docker-build:
	docker build -t multi-agent-app:latest .

docker-up:
	docker compose up --build

docker-down:
	docker compose down
