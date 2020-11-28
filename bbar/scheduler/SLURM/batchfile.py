from bbar.generic import LMOD_modules, Commands
from bbar.scheduler.base import BaseBatchfile

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
class SLURM_batch_params:
    default_job_name = "benchmark_job"
    default_procs_per_node = 4

    def __init__(self,config, n_procs):
        self.param_dict = {k:v for k,v in config["sbatch_params"].items()}
        self.max_procs_per_node = int(config["max_procs_per_node"]) if "max_procs_per_node" in config else SLURM_batch_params.default_procs_per_node
        self.param_dict["n"] = n_procs
        self.n_procs = self.param_dict["n"]
        #TODO(DOCUMENT): hardcoded allocation semantics, according to assumption #2, change?
        self.param_dict["N"] = ((self.n_procs+3)//self.max_procs_per_node)    
        self.n_nodes = self.param_dict["N"]

        
        if "job-name" not in self.param_dict:
            self.param_dict["job-name"] = SLURM_batch_params.default_job_name
        if "output" not in self.param_dict:
            self.param_dict["output"] = f"{self.param_dict['job-name']}-{self.n_procs}-%j.out"

        self.procs_on_node = min(self.n_procs, self.max_procs_per_node)
        self.format_params = {f"SBATCH_{k}":v for k,v in self.param_dict.items()}
        #DOCUMENT:sbatch parameters with format params can only refer to parameters declared earlier than them (and "n","N","jobname","output")
        for key, value in self.param_dict.items():
            if isinstance(value, str):
                self.param_dict[key] = value.format(**self.format_params, procs_on_node = self.procs_on_node)
            self.format_params[f"SBATCH_{key}"] = self.param_dict[key]

        self.job_name = self.param_dict["job-name"]
        self.output = self.param_dict["output"]
        
    def __repr__(self):
        return "\n".join([f"#SBATCH --{k}={v}" for k,v in self.param_dict.items() if len(k) > 1])+"\n"\
                + "\n".join([f"#SBATCH -{k} {v}" for k,v in self.param_dict.items() if len(k) == 1])\

class SLURM_commands(Commands):
    def __repr__(self):
        return "\n".join([f"pushd {c.workdir} &>/dev/null && {c.env_vars} srun {c.argv_string} && popd &> /dev/null" for c in self.commands])
    
class SLURM_Batchfile(BaseBatchfile):
    def __init__(self, config, n_procs):
                                                   
        self.sbatch_params = SLURM_batch_params(config, n_procs)
        self.output = self.sbatch_params.output
        format_params = self.sbatch_params.format_params

        self.modules = LMOD_modules(config)
        self.commands = SLURM_commands(config["benchmarks"], self.sbatch_params.format_params)
        self.setup = config["setup"] if "setup" in config else ""
        self.cleanup = config["cleanup"] if "cleanup" in config else ""
        filename_pattern = config["batchfile_name"] if "batchfile_name" in config else "{SBATCH_job-name}-{SBATCH_n}.batch"
        self.filename = filename_pattern.format(**self.sbatch_params.format_params)

    #TODO: only functions that should maybe be moved out, then we would have a pure data object
    def create_file(self):
        with open(self.filename,"w") as f:
            f.write(str(self))

    def __repr__(self):
        newline = "\n"
        return  "#!/bin/bash\n"\
            f"{self.sbatch_params}\n"\
            "\n#this file was generated from a configuration file\n"\
            f"{self.setup+newline if self.setup else ''}"\
            f"{str(self.modules)+newline if self.modules else ''}\n"\
            f"{self.commands}\n"\
            f"{newline+self.cleanup if self.cleanup else ''}"
