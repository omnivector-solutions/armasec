SHELL:=/bin/bash
ROOT_DIR:=$(shell dirname $(shell pwd))
LAMBDA_TARGET:=${ROOT_DIR}/function.zip

install:
	poetry install

test: install
	poetry run pytest

mypy: install
	poetry run mypy armasec --pretty

lint: install
	poetry run black --check armasec tests
	poetry run isort --check armasec tests
	poetry run flake8 --max-line-length=100

qa: test mypy lint
	echo "All tests pass! Ready for deployment"

format: install
	poetry run black armasec tests
	poetry run isort armasec tests

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
