from bbar.analysis.plugins import register_metric

@register_metric("zero")
def exit_code(batchfile, job):
    stats = job.get_stats()
    return stats["exit_code"]
