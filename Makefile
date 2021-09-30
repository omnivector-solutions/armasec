SHELL:=/bin/bash
PACKAGE_NAME:=armasec
ROOT_DIR:=$(shell dirname $(shell pwd))

install:
	poetry install

test: install
	poetry run pytest

mypy: install
	poetry run mypy ${PACKAGE_NAME} --pretty

lint: install
	poetry run black --check ${PACKAGE_NAME} tests
	poetry run isort --check ${PACKAGE_NAME} tests
	poetry run flake8 --max-line-length=100 ${PACKAGE_NAME} tests

qa: test mypy lint
	echo "All tests pass! Ready for deployment"

format: install
	poetry run black ${PACKAGE_NAME} tests
	poetry run isort ${PACKAGE_NAME} tests

example: install
	poetry run uvicorn --host 0.0.0.0 --app-dir=examples basic:app --reload

publish: install
	git tag v$(poetry version --short)
	git push origin v$(poetry version --short)

docs: install
	poetry run sphinx-apidoc --output-dir=docs-source/ --no-toc --separate armasec
	poetry run sphinx-build docs-source/ docs/
	cp -r docs-source/_static docs/_static
	cp -r docs-source/_templates docs/_templates

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
