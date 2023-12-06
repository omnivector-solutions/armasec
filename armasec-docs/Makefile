# SETTINGS
# Use one shell for all commands in a target recipe
.ONESHELL:
.DEFAULT_GOAL:=help
SHELL:=/bin/bash

install:
	poetry install

build: install
	poetry run mkdocs build --config-file=mkdocs.yaml

serve: install
	poetry run mkdocs serve --config-file=mkdocs.yaml --dev-addr=localhost:10000

.PHONY: clean
clean:
	@find . -iname '*.pyc' -delete
	@find . -iname '*.pyo' -delete
	@find . -iname '*~' -delete
	@find . -iname '*.swp' -delete
	@find . -iname '__pycache__' -delete
	@rm -fr build/
	@rm -fr dist/
	@rm -fr *.egg-info
