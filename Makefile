SHELL:=/bin/bash
PACKAGE_NAME:=armasec
ROOT_DIR:=$(shell dirname $(shell pwd))

install:
	poetry install --extras=cli

test: install
	poetry run pytest

mypy: install
	poetry run mypy ${PACKAGE_NAME} --pretty

lint: install
	poetry run ruff check ${PACKAGE_NAME} tests armasec_cli

qa: test mypy lint
	echo "All quality checks pass!"

format: install
	poetry run ruff check --fix ${PACKAGE_NAME} tests armasec_cli
	poetry run ruff format ${PACKAGE_NAME} tests armasec_cli

example: install
	poetry run uvicorn --host 0.0.0.0 --app-dir=examples basic:app --reload

publish: install
	git tag v$(poetry version --short)
	git push origin v$(poetry version --short)

docs: install
	poetry run mkdocs build --config-file=docs/mkdocs.yaml

docs-serve: install
	poetry run mkdocs serve --config-file=docs/mkdocs.yaml

clean: clean-eggs clean-build
	@find . -iname '*.pyc' -delete
	@find . -iname '*.pyo' -delete
	@find . -iname '*~' -delete
	@find . -iname '*.swp' -delete
	@find . -iname '__pycache__' -delete
	@rm -r .mypy_cache
	@rm -r .pytest_cache

clean-eggs:
	@find . -name '*.egg' -print0|xargs -0 rm -rf --
	@rm -rf .eggs/

clean-build:
	@rm -fr build/
	@rm -fr dist/
	@rm -fr *.egg-info
