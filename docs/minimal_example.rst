Minimal Example
===============

The following is a minimal example of how to configure your API to enforce security on endpoints
using tokens issued by Auth0:

.. literalinclude:: ../examples/basic.py
   :language: python

In this example, you would have set two environment variables for your project settings:

* ARMASEC_DOMAIN

  This would be your Auth0 domain, like: ``my-auth.us.auth0.com``

* ARMASEC_AUDIENCE

  You would get this from your Auth0 API App, like: ``https://my-api.my-domain.com``

When you run your app, access to the ``/stuff`` endpoint would be restricted to authenticated users
whose access tokens carried the permission scope "read:stuff".

For a step-by-step walkthrough of how to set up Auth0 for the minimal example, see the
`"Getting Started with Auth0" <tutorials/gettings_started_with_auth0>`_ page.

The above code can be found in `examples/basic.py
<https://github.com/omnivector-solutions/armasec/blob/main/examples/basic.py>`_.
