# Writing Plugins

Armasec provides a plugin system for adding additional token validators. These
validators are applied at auth time on every route that applies auth checks.

In order to include the custom validators, they need only be installed along-side
Armasec. The Armasec package will automatically detect the installed plugin and include
it in the auth checks.


## Implementation

Armasec uses [Pluggy](https://pluggy.readthedocs.io/en/stable/) to provide plugins. To
build a custom validator, a method named `armasec_plugin_check` needs to be implemented
and deocorated with the `hookimpl` decorator that you import from `armasec.pluggable`.

Here is an example implementation:

```python title="plugin/main.py" linenums="1"
from armasec import TokenPayload
from armasec.exceptions import ArmasecError
from armasec.pluggable import hookimpl

subscribers = set()

class PluginError(ArmasecError):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    detail = "User is not subscribed."

@hookimpl
def armasec_plugin_check(token_payload: TokenPayload):
    logger.debug("Applying check from example plugin")
    PluginError.require_condition(
        getattr(token_payload, "email") in subscribers,
        "User is not subscribed!",
    )
```

In this example, the email provided by the auth token's payload is checked against an
in-memory store of active subscribers. If it is not found, an exception is raised with
a `status_code` of 402. This will cause any endpoint protected by `Armasec` to return
a `402` status code indicating that payment is required.

2 things are critical in this implementation:

  1. The `hookimpl` decorator wraps the function that applies the check logic
  2. If the check fails, a derived class of `ArmasecError` is raised to indicate that
     the check Failed

Beyond these two things, the implementation is left to the imagination and creativity of
the user.


## Setup

In order for the plugin to be recognized by Armasec, it must be registered under the
`entry_points` group "armasec". To read more on `entry_points` and their significance in
python packaging, please read the
[Entry points specification](https://packaging.python.org/en/latest/specifications/entry-points/)
documentation.

Entrypoints are specified differently according to the packaging tool your project uses.

Suppose that your project implements a plugin named `my-plugin` and the source for your
`hookimpl` functions is in the module `plugin/main`.

For a project that uses `setuptools`, the entrypoint for the plugin should be indicated
like this:

```python title="setup.py"
setup(
    ...
    entry_points={"armasec": ["my-plugin=plugin.main"]},
    ...
)
```

For a project that uses `pyproject.toml` (uv, poetry, etc.), you need to include an entry
for the plugin like so:

```toml title="pyproject.toml"
[project.entry-points.'armasec']
my-plugin = 'plugin.main'
```

For legacy poetry configurations, you can also use:

```toml title="pyproject.toml"
[tool.poetry.plugins.'armasec']
my-plugin = 'plugin.main'
```


## Usage

Once your plugin is installed in the environment where you need to extend Armasec's
functionality, its `hookimpl` decorated `armasec_plugin_check()` method will
automatically be called by Armasec for every secured route.

Note that you may skip plugins in any routes that include a skip parameter to Armasec's
`lockdown()` method. For example, if you have a route that should be exempted from
processing any plugin validations, you should use the dependency injection like so:

```python title="routers.py"
@app.get(
    "/secured",
    dependencies=[Depends(armasec.lockdown("my:permission", skip_plugins=True))],
)
async def secured():
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

For this route, only the core Armasec validations will be applied and all plugins will
be skipped.


## Complete Example

For a complete example of an implementation of an Armasec plugin, see the
[armasec-subscriptions](https://github.com/omnivector-solutions/armasec-subscriptions)
plugin.
