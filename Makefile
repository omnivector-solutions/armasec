SHELL:=/bin/bash
PACKAGE_NAME:=armasec
ROOT_DIR:=$(shell dirname $(shell pwd))

install:
	uv sync --group dev

test: install
	uv run pytest

mypy: install
	uv run mypy ${PACKAGE_NAME} --pretty

lint: install
	uv run ruff check ${PACKAGE_NAME} tests armasec_cli

qa: test mypy lint
	echo "All quality checks pass!"

format: install
	uv run ruff check --fix ${PACKAGE_NAME} tests armasec_cli
	uv run ruff format ${PACKAGE_NAME} tests armasec_cli

example: install
	uv run uvicorn --host 0.0.0.0 --app-dir=examples basic:app --reload

publish: install
	git tag v$(uv run python -c "import toml; print(toml.load('pyproject.toml')['project']['version'])")
	git push origin v$(uv run python -c "import toml; print(toml.load('pyproject.toml')['project']['version'])")

docs: install
	uv run mkdocs build --config-file=docs/mkdocs.yaml

docs-serve: install
	uv run mkdocs serve --config-file=docs/mkdocs.yaml

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
