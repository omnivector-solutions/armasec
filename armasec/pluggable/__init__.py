"""
Manage plugins from armasec.
"""

import pluggy
from armasec.pluggable import hookspecs

hookimpl = pluggy.HookimplMarker("armasec")
plugin_manager = pluggy.PluginManager("armasec")
plugin_manager.add_hookspecs(hookspecs)
plugin_manager.load_setuptools_entrypoints("armasec")
