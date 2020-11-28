from functools import partial

class BaseScheduler:
    Batchfile            = None
    schedule_batchjob    = None
    get_stats            = None
    name                 = "Unknown scheduler"

    def __init__(self):
        pass
