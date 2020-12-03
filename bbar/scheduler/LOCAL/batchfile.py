from bbar.generic import Environment_variables, LMOD_modules
from bbar.generic import Commands
from bbar.scheduler.base import BaseBatchfile
from bbar.scheduler.SLURM.batchfile import SLURM_batch_params

#DOCUMENT: Assumptions for sbatch files:
#   1. sbatch files mainly differ by process count in a benchmark case, for scale benchmarks
#   2. we want full nodewise allocation, not balanced allocation    
#   e.g. if max_procs_per_node is 4, and we have 6 procs:
#       node 1 gets 4
#       node 2 gets 2
#   instead of the balanced 3 and 3

#DOCUMENT:Four parameters are guaranteed to be in the SBATCH configuration:
# --n
# --N
# --job-name
# --output

class FAKE_SLURM_batch_params(SLURM_batch_params):
    BATCHFILE_PREFIX="LOCAL_TEST"

class Shellscript_Batchfile(BaseBatchfile):
    def __init__(self, config, n_procs):
                                                   
        self.batch_params = FAKE_SLURM_batch_params(config, n_procs)
        self.output = self.batch_params.param_dict["output"]
        self.jobname = self.batch_params.param_dict["job-name"]
        format_params = self.batch_params.format_params

        self.modules = LMOD_modules(config)
        self.commands = Commands(config["benchmarks"], format_params)
        self.setup = config["setup"]
        self.cleanup = config["cleanup"]
        self.filename = config["batchfile_name"].format(**format_params)

    def __repr__(self):
        newline = "\n"
        return  "#!/bin/bash\n"\
            f"{self.batch_params}\n"\
            "\n#this file was generated from a configuration file\n"\
            f"{self.setup+newline if self.setup else ''}"\
            f"{str(self.modules)+newline if self.modules else ''}\n"\
            f"{self.commands}\n"\
            f"{newline+self.cleanup if self.cleanup else ''}"
