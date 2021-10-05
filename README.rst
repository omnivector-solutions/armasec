.. image:: https://img.shields.io/github/workflow/status/omnivector-solutions/armasec/test_on_push/main?label=main-build&logo=github&style=plastic
   :alt: main build
.. image:: https://img.shields.io/github/issues/omnivector-solutions/armasec?label=issues&logo=github&style=plastic
   :alt: github issues
.. image:: https://img.shields.io/github/issues-pr/omnivector-solutions/armasec?label=pull-requests&logo=github&style=plastic
   :alt: pull requests
.. image:: https://img.shields.io/github/contributors/omnivector-solutions/armasec?logo=github&style=plastic
   :alt: github contributors

.. image:: https://img.shields.io/pypi/pyversions/armasec?label=python-versions&logo=python&style=plastic
   :alt: python versions
.. image:: https://img.shields.io/pypi/v/armasec?label=pypi-version&logo=python&style=plastic
   :alt: pypi version

.. image:: https://img.shields.io/pypi/l/armasec?style=plastic
   :alt: license

.. figure:: https://github.com/omnivector-solutions/armasec/blob/main/docs-source/_static/logo.png?raw=true
   :alt: Logo
   :align: center
   :width: 80px

   An Omnivector Solutions initiative

=========
 Armasec
=========

Adding a security layer on top of your API can be difficult, especially when working with an OIDC
platform. It's hard enough to get your OIDC provider configured correctly. Armasec aims to take the
pain out of securing your APIs routes.

Armasec is an opinionated library that attemtps to use the most obvious and commonly used workflows
when working with OIDC and making configuration as simple as possible.

When using the
`Armasec <https://github.com/omnivector-solutions/armasec/blob/main/armasec/armasec.py>`_ helper
class, you only need two configuration settings to get going:

#. Domain: the domain of your OIDC provider
#. Audience: An optional setting that restricts tokens to those intended for your API.

That's it! Once you have those settings dialed in, you can just worry about checking the permissions
scopes of your endpoints


Documentation
=============

Documentation is hosted hosted on ``github.io`` at
`the Armasec homepage <https://omnivector-solutions.github.io/armasec/>`_


Quickstart
==========

#. Install ``armasec`` and ``uvicorn``:

   $ pip install armasec


#. Minimal Example (example.py)

.. code-block:: python

   import os

   from armasec import Armasec
   from fastapi import FastAPI, Depends


   app = FastAPI()
   armasec = Armasec(
       os.environ.get("ARMASEC_DOMAIN"),
       audience=os.environ.get("ARMASEC_AUDIENCE"),
   )

   @app.get("/stuff", dependencies=[Depends(armasec.lockdown("read:stuff"))])
   async def check_access():
       return dict(message="Successfully authenticated!")

#. Run the app

   $ uvicorn --host 0.0.0.0 example:app


License
=======

Distributed under the MIT License. See `LICENSE` for more information.
