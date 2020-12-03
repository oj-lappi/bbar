import importlib
from collections import namedtuple
from bbar.logging import debug

#Reports

ReportPlugin = namedtuple("ReportPlugin", ("name", "report"))
system_reports_plugin_importpath="bbar.analysis.reports"
_ANALYZER_PLUGINS = {system_reports_plugin_importpath:{}}

def register_report(name):
    """Decorator factory for registering a new plugin"""
    def decorator(report):
        debug(f"Registering report {name}")
        _PLUGINS[system_plugin_importpath][name] = ReportPlugin(name=name, report=report)
        return report
    return decorator

def register_custom_report(name):
    """Decorator factory for registering user plugins """
    #Not implemented yet, checkout https://realpython.com/python-import/#example-a-package-of-plugins
    pass

def list_reports():
    """List all reports"""
    return sorted(list(_ANALYZER_PLUGINS))

def get_report(name, importpath=system_reports_plugin_importpath):
    """Get a given plugin"""
    debug(f"Trying to register report {importpath}.{name}")
    importlib.import_module(f"{importpath}.{name}")
    return _ANALYZER_PLUGINS[importpath][name].report


#Metrics

MetricPlugin = namedtuple("MetricPlugin", ("name", "metric"))
system_metrics_plugin_importpath="bbar.analysis.metrics"
_METRICS = {system_metrics_plugin_importpath:{}}

def register_metric(name):
    """Decorator factory for registering a new plugin"""
    def decorator(metric):
        debug(f"Registering metric {name}")
        _PLUGINS[system_plugin_importpath][name] = MetricPlugin(name=name, metric=metric)
        return metric
    return decorator

def register_custom_metric(name):
    """Decorator factory for registering user plugins """
    #Not implemented yet, checkout https://realpython.com/python-import/#example-a-package-of-plugins
    pass

def list_metrics():
    """List all metrics"""
    return sorted(list(_METRICS))

def get_metric(name, importpath=system_metrics_plugin_importpath):
    """Get a given plugin"""
    debug(f"Trying to register metric {importpath}.{name}")
    importlib.import_module(f"{importpath}.{name}")
    return _METRICS[importpath][name].metric
