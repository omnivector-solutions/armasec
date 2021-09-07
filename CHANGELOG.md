# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

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
- Initial release of armada-security
- Added TokenManager and TokenSecurity
- Included unit tests
- Configured code formatting
- Setup github actions
- Added a README and this CHANGELOG
