import os
import toml

default_job_name = "benchmark_job"

#Assumption: sbatch files mainly differ by process count in a benchmark case

def stepper(start, step, num_steps=None):
    if num_steps:
        for _ in range(num_steps):
            yield start
            start+=step
    else:
        while True:
            yield start
            start+=step
    
def multiplicator(start,step_factor,num_steps):
    for _ in range(num_steps):
        yield start
        start*=step_factor

def const_generator(const):
    while True:
        yield const
        
def list_generator(l):
    for i in l:
        yield l
        
def generator_from_config(name, config, num_steps):
    if isinstance(config, dict):
        if "start" in config and "step" in config:
            return stepper(config["start"],config["step"])
        
    elif isinstance(config, list):
        if len(config) < num_steps:
            raise Exception(f"Too few items in list provided for {name}, needed {num_steps}, length was {len(config)}")
        return list_generator(config)

    else:
        return const_generator(config)
    
def scale_up_generator(config):
    if isinstance(config, dict):
        if "start" in config and "step" in config and "num_steps" in config:
            return stepper(config["start"],config["step"],config["num_steps"])
        elif "start" in config and "step_factor" in config and "num_steps" in config:
            return multiplicator(config["start"], config["step_factor"], config["num_steps"])
        
    elif isinstance(config, list):
        return list_generator(config)
    
    else:
        return const_generator(config)

class SBatch_params:
    def __init__(self,p_dict, n_procs, max_procs_per_node):
        self.param_dict = {k:v for k,v in p_dict.items()}
        self.n_procs = n_procs
        self.param_dict["n"] = self.n_procs
        self.param_dict["N"] = (self.n_procs+3//max_procs_per_node)    
        self.procs_on_node = min(self.n_procs,max_procs_per_node)

        self.format_params = {f"SBATCH_{k}":v for k,v in self.param_dict.items()}
        
        if "job-name" not in p_dict:
            self.param_dict["job-name"] = default_job_name
        if "output" not in p_dict:
            self.param_dict["output"] = f"{self.param_dict['job-name']}-{self.n_procs}-%j.out"
            
        for k in self.param_dict:
            self.format_and_replace(k)
            
    
    def format_and_replace(self, key):
        if isinstance(self.param_dict[key],str):
            self.param_dict[key] = self.param_dict[key].format(**self.format_params, procs_on_node = self.procs_on_node)
        self.format_params[f"SBATCH_{key}"] = self.param_dict[key]
        
    def __repr__(self):
        return "\n".join([f"#SBATCH --{k}={v}" for k,v in self.param_dict.items()])
    
    
class LMod_modules:
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
    
class Benchmark_command:
    def __init__(self, workdir, command, arguments, env_vars, subshell=True):
        self.env_vars = Environment_variables(env_vars)
        self.workdir = workdir
        self.arguments = [command]+arguments
        self.subshell = subshell
        
    def __repr__(self):
        buf = f"pushd {self.workdir} && {self.env_vars} {' '.join([str(v) for v in self.arguments])} && popd"
        if self.subshell:
            return f"$({buf})"
        return buf

        
class Benchmark_commands:
    def __init__(self, config, argument_generators, env_var_generators, sbatch_params, subshell=True):
        #Loop over generators until one of them is done, can we do constants?
        self.commands = []
        self.workdirs = []
        workdir_pattern = config["workdir"]
        command = config["command"]
        num_settings = int(config["num_settings"])
        for _ in range(num_settings):
            arguments = [next(a) for a in argument_generators]
            env_vars = {k:next(v) for k,v in env_var_generators.items()}
            workdir = workdir_pattern.format(** env_vars, **sbatch_params, arguments=arguments)
            self.workdirs.append(workdir)
            self.commands.append(Benchmark_command( workdir, command, arguments, env_vars,subshell ))
            
    def __repr__(self):
        return "\n".join([f"{c}" for c in self.commands])
    
class SLURM_batch_configuration:
    def __init__(self, sbatch_params, modules,  setup, cleanup, benchmark_commands, filename_pattern, format_sbatch_params):
        self.sbatch_params = sbatch_params
        self.modules = modules
        self.setup = setup
        self.cleanup = cleanup
        self.commands = benchmark_commands
        self.filename = filename_pattern.format(**format_sbatch_params)
    
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
            "#THIS FILE WAS AUTOGENERATED BY A SCRIPT\n\n"\
            f"{self.commands}\n"\
            f"{newline+self.cleanup if self.cleanup else ''}"
    
   
class BenchmarkSet:
    def __init__(self, config=None, config_file=None):
        #TODO: some orthogonal data structure? from benchmark to sbatch config?
        if not config:
            if config_file:
                config = toml.load(config_file)
            else:
                raise("No config for benchmark set")
        
        
        self.initialized = False
        self.slurm_batch_configs = []

        modules = LMod_modules(config)
        bench_cfg = config["benchmarks"]
        num_settings = int(bench_cfg["num_settings"])
        
        max_procs_per_node = config["max_procs_per_node"] if "max_procs_per_node" else 4
        
        for n_procs in scale_up_generator(config["scaleup"]):
            
            sbatch_params = SBatch_params(config["sbatch_params"], n_procs, max_procs_per_node)
            #TODO: move generators into command initialization
            try:
                argument_generators = [generator_from_config(i,v,num_settings) for i,v in enumerate(bench_cfg["arguments"])]
            except Exception as e:
                print("ERROR generating arguments for benchmarks:", e)
                return 
            try:
                env_var_generators = {
                    k:generator_from_config(k,v,num_settings)
                    for k,v in bench_cfg["env_vars"].items()
                }
            except Exception as e:
                print("ERROR generating environment variables for benchmarks:", e)
                return 
            
            benchmark_cmds = Benchmark_commands(bench_cfg, argument_generators,
                                            env_var_generators,
                                            sbatch_params.format_params)
            
            setup = config["setup"] if "setup" in config else ""
            cleanup = config["cleanup"] if "cleanup" in config else ""
        
            
            batch_conf = SLURM_batch_configuration(sbatch_params, modules, setup, cleanup, benchmark_cmds,
                                                   config["batchfile_name"], sbatch_params.format_params)
            
            self.slurm_batch_configs.append(batch_conf)
            
        self.initialized = True
        
    def create_directories(self):
        for batch_cfg in self.slurm_batch_configs:
            for wd in batch_cfg.commands.workdirs:
                os.makedirs(wd,exist_ok=True)
        
    def create_batchfiles(self):
        #TODO: check if exists and ask user
        for batch_cfg in self.slurm_batch_configs:
            batch_cfg.create_file()
        
    def generate_files(self):
        self.create_directories()
        self.create_batchfiles()
        
    def run_benchmarks(self):
        self.generate_files()
        
    
    def show_files(self):
        for batch_cfg in self.slurm_batch_configs:
            print(batch_cfg)
            print()
