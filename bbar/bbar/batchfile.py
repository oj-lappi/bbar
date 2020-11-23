from .generators import generator_from_config
from pathlib import Path


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
        self.n_procs = n_procs
        self.param_dict["n"] = self.n_procs
        #TODO(DOCUMENT): hardcoded allocation semantics, according to assumption #2, change?
        self.param_dict["N"] = ((self.n_procs+3)//self.max_procs_per_node)    
        self.procs_on_node = min(self.n_procs, self.max_procs_per_node)

        
        if "job-name" not in self.param_dict:
            self.param_dict["job-name"] = SLURM_batch_params.default_job_name
        if "output" not in self.param_dict:
            self.param_dict["output"] = f"{self.param_dict['job-name']}-{self.n_procs}-%j.out"
            
        self.format_params = {f"SBATCH_{k}":v for k,v in self.param_dict.items()}
        #DOCUMENT:sbatch parameters with format params can only refer to parameters declared earlier than them (and "n","N","jobname","output")
        for key, value in self.param_dict.items():
            if isinstance(value, str):
                self.param_dict[key] = value.format(**self.format_params, procs_on_node = self.procs_on_node)
            self.format_params[f"SBATCH_{key}"] = self.param_dict[key]
        
    def __repr__(self):
        return "\n".join([f"#SBATCH --{k}={v}" for k,v in self.param_dict.items() if len(k) > 1])+"\n"\
                + "\n".join([f"#SBATCH -{k} {v}" for k,v in self.param_dict.items() if len(k) == 1])\
    
    
class LMOD_modules:
    def __init__(self,cfg):
        self.module_list = cfg["modules"] if "modules" in cfg else []
        
    def __repr__(self):
        if self.module_list:
            return f"module load {' '.join(self.module_list)}"
        return ""
    
class Environment_variables:
    def __init__(self,var_dict):
        self.var_dict = {k:v for k,v in var_dict.items()}
        
    def __repr__(self):
        if self.var_dict:
            return f"{' '.join([f'{k}={v}' for k,v in self.var_dict.items()])}"
        return ""
    
class SLURM_jobstep:
    def __init__(self, workdir, command_dir, command, arguments, env_vars, sbatch_format_params, use_subshell):
        self.env_vars = Environment_variables(env_vars)
        self.workdir = workdir
        self.command_dir = command_dir.format(**env_vars, **sbatch_format_params, arguments=arguments)
        self.command = (Path(command_dir) / command).absolute()
        self.arguments = [self.command]+arguments
        self.use_subshell = use_subshell
        
    def __repr__(self):
        buf = f"pushd {self.workdir} &>/dev/null && {self.env_vars} {' '.join([str(v) for v in self.arguments])} && popd &> /dev/null"
        if self.use_subshell:
            return f"echo $({buf})"
        return buf

       
class SLURM_jobstep_list:
    def __init__(self, config, sbatch_format_params):
        workdir_pattern = config["workdir"]
        command_dir = config["command_dir"] if "command_dir" in config else "."
        command = config["command"]
        use_subshell = True
        if "use_subshell" in config:
            use_subshell_str =str(config["use_subshell"]).lower()
            if use_subshell_str in ["no","false","f","0","off"]:
                use_subshell=False

        num_settings = int(config["num_settings"])
        if "arguments" in config:
            try:
                argument_generators = [generator_from_config(i,v,num_settings) for i,v in enumerate(config["arguments"])]
            except Exception as e:
                raise Exception("ERROR generating arguments for benchmarks:", e)
        else:
            argument_generators = []


        if "env_vars" in config:
            try:
                env_var_generators = {
                    k:generator_from_config(k,v,num_settings)
                    for k,v in config["env_vars"].items()
                }
            except Exception as e:
                raise Exception("ERROR generating environment variables for benchmarks:", e)
        else:
            env_var_generators = {}
        
        self.commands = []
        self.workdirs = []

        for _ in range(num_settings):
            arguments = [next(a) for a in argument_generators]
            env_vars = {k:next(v) for k,v in env_var_generators.items()}
            workdir = workdir_pattern.format(**env_vars, **sbatch_format_params, arguments=arguments)
            self.workdirs.append(workdir)
            self.commands.append(SLURM_jobstep( workdir, command_dir, command, arguments, env_vars, sbatch_format_params, use_subshell = use_subshell))
            
    def __repr__(self):
        return "\n".join([f"{c}" for c in self.commands])
    
class SLURM_batchfile:
    def __init__(self, config, n_procs):
                                                   
        self.sbatch_params = SLURM_batch_params(config, n_procs)
        self.modules = LMOD_modules(config)
        self.commands = SLURM_jobstep_list(config["benchmarks"], self.sbatch_params.format_params)
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
            "\n#this file was generated from a configuration file\n\n"\
            f"{self.setup+newline if self.setup else ''}"\
            f"{self.modules}\n\n"\
            f"{self.commands}\n"\
            f"{newline+self.cleanup if self.cleanup else ''}"

