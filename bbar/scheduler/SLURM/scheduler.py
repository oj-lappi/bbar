from bbar.scheduler.base import BaseScheduler
from bbar.scheduler.plugins import register_scheduler
from .batchfile import SLURM_Batchfile

import subprocess

@register_scheduler("SLURM")
class SLURM_Scheduler(BaseScheduler):
    Batchfile         = SLURM_Batchfile
    jobs              = []

    def __init__(self):
        #TODO: import state from BBAR_Store
        pass
        

    def schedule_job(batchfile):
        args = ["sbatch", batchfile.filename]
        subprocess.check_call(args)

    def get_stats():
        pass
