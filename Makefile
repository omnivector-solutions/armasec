SHELL:=/bin/bash
ROOT_DIR:=$(shell dirname $(shell pwd))
PACKAGE_NAME:=${PACKAGE_NAME}

install:
	poetry install

test: install
	poetry run pytest

mypy: install
	poetry run mypy ${PACKAGE_NAME} --pretty

lint: install
	poetry run black --check ${PACKAGE_NAME} tests
	poetry run isort --check ${PACKAGE_NAME} tests
	poetry run flake8 --max-line-length=100

qa: test mypy lint
	echo "All tests pass! Ready for deployment"

format: install
	poetry run black ${PACKAGE_NAME} tests
	poetry run isort ${PACKAGE_NAME} tests

clean: clean-eggs clean-build
	@find . -iname '*.pyc' -delete
	@find . -iname '*.pyo' -delete
	@find . -iname '*~' -delete
	@find . -iname '*.swp' -delete
	@find . -iname '__pycache__' -delete

clean-eggs:
	@find . -name '*.egg' -print0|xargs -0 rm -rf --
	@rm -rf .eggs/

clean-build:
	@rm -fr build/
	@rm -fr dist/
	@rm -fr *.egg-info
