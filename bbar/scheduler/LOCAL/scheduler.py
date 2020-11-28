from bbar.scheduler.base import BaseScheduler
from bbar.scheduler.plugins import register_scheduler
from .batchfile import Shellscript_Batchfile
import subprocess

#TODO: maybe change bash to sh
@register_scheduler("LOCAL")
class Local_Scheduler(BaseScheduler):
    Batchfile         = Shellscript_Batchfile
    jobs              = []

    def __init__(self):
        #TODO: import state from BBAR_Store (do that in super)
        pass

    def schedule_job(batchfile):
        args = ["/usr/bin/bash", "-c", f"source {batchfile.filename}"]
        subprocess.check_call(args)

    def get_stats():
        pass
