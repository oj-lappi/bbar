from bbar.analysis.plugins import register_metric

@register_metric("zero")
def zero(**kwargs):
    return 0
