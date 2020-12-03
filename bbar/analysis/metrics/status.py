from bbar.analysis.plugins import register_metric

@register_metric("status")
def status(batchfile, job):
    stats = job.get_stats()
    return stats["status"]
