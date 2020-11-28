import importlib
from collections import namedtuple
from bbar.logging import debug

debug(f"plugin __file__: {__file__}")

SchedulerPlugin = namedtuple("Plugin", ("name", "scheduler"))
system_plugin_importpath="bbar.scheduler"
_PLUGINS = {system_plugin_importpath:{}}


def register_scheduler(name):
    """Decorator factory for registering a new plugin"""
    def decorator(scheduler):
        debug(f"Registering scheduler {name}")
        _PLUGINS[system_plugin_importpath][name] = SchedulerPlugin(name=name, scheduler=scheduler)
        return scheduler
    return decorator

def register_custom_scheduler(name):
    """Decorator factory for registering user plugins """
    #Not implemented yet, checkout https://realpython.com/python-import/#example-a-package-of-plugins
    pass

def list_plugins():
    """List all plugins"""
    return sorted(list(_PLUGINS))

def get(name, importpath=system_plugin_importpath):
    """Get a given plugin"""
    debug(f"Trying to register scheduler {importpath}.{name}")
    importlib.import_module(f"{importpath}.{name}")
    return _PLUGINS[importpath][name].scheduler
