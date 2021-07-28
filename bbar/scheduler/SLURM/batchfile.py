from bbar.generic import LMOD_modules, Commands
from bbar.scheduler.base import BaseBatchfile
from bbar.logging import debug
import subprocess

#DOCUMENT: Assumptions for sbatch files:
#   1. sbatch files mainly differ by process count in a benchmark case, for scale benchmarks
#   2. we want full nodewise allocation, not balanced allocation    
#   e.g. if max_procs_per_node is 4, and we have 6 procs:
#       node 1 gets 4
#       node 2 gets 2
#   instead of the balanced 3 and 3
#DOCUMENT:formatted values can only refer to parameters declared earlier than them (and "n","N","jobname","output")

#DOCUMENT:Four parameters are guaranteed to be in the SBATCH configuration:
# --n
# --N
# --job-name
# --output
class SLURM_batch_params:
    FORMAT_PREFIX="SBATCH"
    BATCHFILE_PREFIX="SBATCH"
    def __init__(self,config, n_procs):
        self.param_dict = {k:v for k,v in config["sbatch_params"].items()}

        max_procs_per_node = int(config["max_procs_per_node"])
        self.n_procs = self.param_dict["n"] = n_procs
        self.n_nodes = self.param_dict["N"] = ((n_procs+(max_procs_per_node-1))//max_procs_per_node)    
        self.procs_on_node = min(self.n_procs, max_procs_per_node)

        #TODO: this will probably fail spectacularily if referring to later batch params
        #      restrict this to only non-formatted params somehow, how to detect? regex? maybe python provides?
        self.format_params = {f"{self.FORMAT_PREFIX}_{k}":v for k,v in self.param_dict.items()}
        for k, v in self.param_dict.items():
            if isinstance(v, str):
                self.param_dict[k] = v.format(**self.format_params, procs_on_node = self.procs_on_node)
            self.format_params[f"{self.FORMAT_PREFIX}_{k}"] = self.param_dict[k]
        
    def __repr__(self):
        return "\n".join([f"#{self.BATCHFILE_PREFIX} --{k}={v}" for k,v in self.param_dict.items() if len(k) > 1])+"\n"\
                + "\n".join([f"#{self.BATCHFILE_PREFIX} -{k} {v}" for k,v in self.param_dict.items() if len(k) == 1])\

class SLURM_commands(Commands):
    def __repr__(self):
        return "\n".join([f"pushd {c.workdir} &>/dev/null && {c.env_vars} srun {c.argv_string} && popd &> /dev/null" for c in self.commands])
    
class SLURM_Batchfile(BaseBatchfile):
    def __init__(self, config, n_procs):                                        
        self.sbatch_params = SLURM_batch_params(config, n_procs)
        self.output = self.sbatch_params.param_dict["output"]
        self.jobname = self.sbatch_params.param_dict["job-name"]
        format_params = self.sbatch_params.format_params

        self.modules = LMOD_modules(config)
        self.commands = SLURM_commands(config["benchmarks"], format_params)
        self.setup = config["setup"]
        self.cleanup = config["cleanup"]
        self.filename = config["batchfile_name"].format(**format_params)
        self.env_vars = [f"{e}={val.format(**format_params)}" for e,val in config["env_vars"].items()]

    def get_stats(self):
        if "jobid" not in self.__dict__ or not self.jobid:
            return {}
        sacct_output = suprocess.run(["sacct","-p","-j",f"{self.jobid}"]).stdout.decode()
        lines = sacct_output.split("\n")
        header = lines[0].split("|")
        lines = lines[1:]
        data = [{k:v for k,v in zip(header,l.split("|")) if v != ""} for l in lines if l]
        return data

    def run(self):
        pass
    def __repr__(self):
        newline = "\n"
        return  "#!/bin/bash\n"\
            f"{self.sbatch_params}\n"\
            "\n#this file was generated from a configuration file\n"\
            f"{self.setup+newline if self.setup else ''}"\
            f"{str(self.modules)+newline if self.modules else ''}\n"\
            f"{newline.join(['export '+e for e in self.env_vars])}\n"\
            f"{self.commands}\n"\
            f"{newline+self.cleanup if self.cleanup else ''}"
