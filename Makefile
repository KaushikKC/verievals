.PHONY: install lint fmt type test cov check clean build

install:
	pip install -e ".[dev]"

fmt:
	ruff format src tests
	ruff check --fix src tests

lint:
	ruff check src tests
	ruff format --check src tests

type:
	mypy

test:
	pytest

cov:
	pytest --cov=verievals --cov-report=term-missing --cov-report=xml

check: lint type test

build:
	python -m build

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
