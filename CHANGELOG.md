# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/),
and this project adheres to [Semantic Versioning](http://semver.org/).

## Unreleased

## v1.4.0 - 2024-04-01

- Added plugin support
- Included original token in TokenPayload object
- Added default messages to ArmasecError classes
- Formatted source files with ruff
- Added examples for Keycloak and Auth0

## v1.3.0 - 2023-12-19

- Added Python 3.12 support by updating to Pendulum 3.0
- Updated dependencies in poetry.lock

## v1.2.1 - 2023-09-14

- Fixed CLI sub-package problem with installing via pip

## v1.2.0 - 2023-09-14

- Added payload_claim_mapping to allow mapping claims to payload items
- Added optional CLI for trying out logins and exploring tokens

## v1.1.1 - 2023-08-14

- Converted docs to use public branding images

## v1.1.0 - 2023-08-11

- Converted docs build to use mkdocs-material
- Converted project docs to markdown
- Added new action to automatically build docs

## v1.0.0 - 2023-07-26

- Dropped support for Python 3.6 and 3.7
- Added support for pytest 7.x
- Replaced pytest-freezegun with plummet for unit tests
- Added pendulum to increase readability of timestamps in unit tests
- Used pytest-asyncio auto mode for async tests and fixtures


## v0.11.3 - 2022-11-10

- Loosened version constraints on fastapi.


## v0.11.2 - 2022-11-04

- Loosened constraints in dependencies.


## v0.11.1 - 2022-08-30

- Loosened requirements for urls in schemas (to allow no TLD).


## v0.11.0 - 2022-07-11

- Refactored code for supporting multiple OIDC domains.


## v0.10.2 - 2022-05-28

- Exposed `use_https` in TokenSecurity and Armasec classes.


## v0.10.1 - 2022-05-04

- Added `use_https` flag


## v0.10.0 - 2022-04-26

- Added support for python 3.6


## v0.9.0 - 2022-03-14

- Included `client_id` in TokenPayload (loaded from `azp` claim)
- Upgraded `black` to ^22.0


## v0.8.0 - 2022-02-22

- Updated to use py-buzz 3.0
- Changed to use pyproject-flake8 for linting


## v0.7.3 - 2021-11-16

- Fixed faulty set logic in lockdown_all()


## v0.7.2 - 2021-10-06

- Covers changes for v0.7.1 as well (debugging README render on pypi)
- Fixed broken logo link in README


## v0.7.0 - 2021-09-27

- Added support for different permission modes SOME and ALL
- Updated README
- Added a license, code of conduct, and contribution guide.


## v0.6.1 - 2021-09-28

- Changed `from_dict` method for building the token payload with all possible keys


## v0.6.0 - 2021-09-23

- Dropped support for HS256
- Made TokenSecurity class lazy load TokenManager
- Reorganized a bit to make it work better with OpenAPI swagger


## v0.5.1 - 2021-09-22

- Made the Armasec helper class lazy load elements (to allow easier testing)
- Add github action to publish on tag push


## v0.5.0 - 2021-09-20

- Renamed package to "armasec"
- Major refactor for imporoved testability
- Moved TokenDecoders into their own class heirarchy
- Real tests for RS256 decoding
- Pytest extension for improved testability in client code
- OpenidConfigLoader for fetching OIDC configuration
- Added mock_openid_server for test loading of OIDC config
- Added Armasec helper/convenience class


## v0.4.1 - 2021-09-13

- Adjustments to expose jwt.decode() options for testing overrides


## v0.4.0 - 2021-09-10

- Made audience optional
- Added pytest extension to allow use of a mock openid server
- Improved compatibility with OIDC providers


## v0.3.3 - 2021-09-02

- Eliminated TestTokenManager and moved logic to utilities instead


## v0.3.2 - 2021-09-02

- Included type hints
- Applied formatting and flak8 compliance


## v0.3.1 - 2021-08-30

- Updated .gitignore to ignore dotenv files
- Added additional logging for debugging
- Corrected grammar in some docstrings
- Fixed bug where TokenPayload breaks if you don't provide it a "permissions" field
- Added `decode` cli tool

## v0.3.0 - 2021-08-26

- Added AsymmetricManager for use with RS256 tokens
- Included unit tests
- Updated the README


## v0.2.0 - 2021-08-24

- Initial release of armasec
- Added TokenManager and TokenSecurity
- Included unit tests
- Configured code formatting
- Setup github actions
- Added a README and this CHANGELOG
