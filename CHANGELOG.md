# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

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
