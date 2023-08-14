!!! example "An [Omnivector Solutions](https://www.omnivector.io/){:target="_blank"} initiative"

    [![omnivector-logo](https://omnivector-public-assets.s3.us-west-2.amazonaws.com/branding/omnivector-logo-text-black-horz.png)](https://www.omnivector.io/){:target="_blank"}


# Armasec Documentation

Armasec is a security package that simplifies OIDC security for FastAPI apps.


## Overview

Adding a security layer on top of your API can be difficult, especially when working with an OIDC
platform. It's hard enough to get your OIDC provider configured correctly. Armasec aims to take the
pain out of securing your APIs routes.

Armasec is an opinionated library that attemtps to use the most obvious and commonly used workflows
when working with OIDC and making configuration as simple as possible.

When using the
[Armasec](https://github.com/omnivector-solutions/armasec/blob/main/armasec/armasec.py) helper
class, you only need two configuration settings to get going:

1. Domain: the domain of your OIDC provider
2. Audience: An optional setting that restricts tokens to those intended for your API.

That's it! Once you have those settings dialed in, you can just worry about checking the permissions
scopes of your endpoints


## Inception

Armasec was originally developed as an internal tool to add security in tandem with
[Auth0](https://auth0.com/). Since its inception, Armasec has been used in production with both
Auth0 and [Keycloak](https://www.keycloak.org/). It should work with other OIDC providers, assuming
they are configured correctly, but the developers of Armasec make no guarantees for other platforms.
