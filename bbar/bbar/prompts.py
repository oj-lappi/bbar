import os
import toml
import shutil
import subprocess
import tempfile
from bbar.persistence import BBAR_Store

#Utilities for user input

def yesno_prompt(prompt=None, default=False):
    if prompt is None:
        prompt = "Do you really want to do this?"
    if default:
        prompt = f"{prompt} [Y/n] "
    else:
        prompt = f"{prompt} [N/y] "

    while True:
        answer = input(prompt).lower()
        if not answer:
            return default
        if answer in ["y","yes"]:
            return True
        elif answer in ["n","no"]:
            return False
        print("please enter either y or n")
            
#Generator functions

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

#Four parameters are guaranteed to be in the SBATCH configuration:
# --n
# --N
# --job-name
# --output
class SBatch_params:
    def __init__(self,config, n_procs):
        self.param_dict = {k:v for k,v in config["sbatch_params"].items()}
        self.max_procs_per_node = config["max_procs_per_node"] if "max_procs_per_node" else default_procs_per_node
        self.n_procs = n_procs
        self.param_dict["n"] = self.n_procs
        self.param_dict["N"] = (self.n_procs+3//self.max_procs_per_node)    
        self.procs_on_node = min(self.n_procs, self.max_procs_per_node)

        self.format_params = {f"SBATCH_{k}":v for k,v in self.param_dict.items()}
        
        if "job-name" not in self.param_dict:
            self.param_dict["job-name"] = default_job_name
        if "output" not in self.param_dict:
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
    def __init__(self, workdir, command_dir, command, arguments, env_vars, sbatch_format_params, subshell=True):
        self.env_vars = Environment_variables(env_vars)
        self.workdir = workdir
        self.command_dir = command_dir.format(**env_vars, **sbatch_format_params, arguments=arguments)
        self.command = (Path(command_dir) / command).absolute()
        self.arguments = [self.command]+arguments
        self.subshell = subshell
        
    def __repr__(self):
        buf = f"pushd {self.workdir} &>/dev/null && {self.env_vars} {' '.join([str(v) for v in self.arguments])} && popd &> /dev/null"
        if self.subshell:
            return f"echo $({buf})"
        return buf

        
class Benchmark_command_set:
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

        try:
            argument_generators = [generator_from_config(i,v,num_settings) for i,v in enumerate(config["arguments"])]
        except Exception as e:
            print("ERROR generating arguments for benchmarks:", e)
            return 
        try:
            env_var_generators = {
                k:generator_from_config(k,v,num_settings)
                for k,v in config["env_vars"].items()
            }
        except Exception as e:
            print("ERROR generating environment variables for benchmarks:", e)
            return 
        
        self.commands = []
        self.workdirs = []

        for _ in range(num_settings):
            arguments = [next(a) for a in argument_generators]
            env_vars = {k:next(v) for k,v in env_var_generators.items()}
            workdir = workdir_pattern.format(**env_vars, **sbatch_format_params, arguments=arguments)
            self.workdirs.append(workdir)
            self.commands.append(Benchmark_command( workdir, command_dir, command, arguments, env_vars, sbatch_format_params, subshell = use_subshell))
            
    def __repr__(self):
        return "\n".join([f"{c}" for c in self.commands])
    
class SLURM_batch_configuration:
    def __init__(self, config, n_procs):
                                                   
        self.sbatch_params = SBatch_params(config, n_procs)
        self.modules = LMod_modules(config)
        self.commands = Benchmark_command_set(config["benchmarks"], self.sbatch_params.format_params)
        self.setup = config["setup"] if "setup" in config else ""
        self.cleanup = config["cleanup"] if "cleanup" in config else ""
        filename_pattern = config["batchfile_name"] if "batchfile_name" in config else "{SBATCH_job-name}-{SBATCH_n}.batch"
        self.filename = filename_pattern.format(**self.sbatch_params.format_params)

    def create_file(self):
        with open(self.filename,"w") as f:
            f.write(str(self))
    
    def run_file(self):
        pass

    def __repr__(self):
        newline = "\n"
        return  "#!/bin/bash\n"\
            f"{self.sbatch_params}\n"\
            "\n#this file was generated from a configuration file\n\n"\
            f"{self.setup+newline if self.setup else ''}"\
            f"{self.modules}\n\n"\
            f"{self.commands}\n"\
            f"{newline+self.cleanup if self.cleanup else ''}"
    
   
class BenchmarkSet:
    def __init__(self, config, config_file_name=None):
        self.initialized = False
        self.config = config
        self.state = BBAR_Store()
        self.slurm_batch_configs = [SLURM_batch_configuration(config, n_procs)  for n_procs in scale_up_generator(config["scaleup"])]
        #TODO: read archive name from config file
        self.archive_name = "bbar"
        self.initialized = True
        
    def create_directories(self):
        for batch_cfg in self.slurm_batch_configs:
            for wd in batch_cfg.commands.workdirs:
                try:
                    path = Path(wd).relative_to(Path('.').resolve())
                except:
                    path = Path(wd)
                
                for p in reversed(path.parents):
                    if not p.exists():
                        self.state.add_generated_dir(str(p.resolve()))
                        os.mkdir(p)
                
                if not path.exists():
                    self.state.add_generated_dir(str(path.resolve()))
                    os.mkdir(path)
                #os.makedirs(wd,exist_ok=True)
        
    def create_batchfiles(self, interactive=False):
        for batch_cfg in self.slurm_batch_configs:
            if interactive and os.path.isfile(batch_cfg.filename):
                if not yesno_prompt("Generated batchfiles will overwrite old ones, is this ok?"):
                    return
                else:
                    interactive=False
            self.state.add_generated_batchfile(batch_cfg.filename)
            batch_cfg.create_file()
         
    #TODO:rewrite delete routines to match semantics of rm -i (ask before every file, instead of just once)?
    #ALT: rewrite to ask if there are outputs in the dirs
    def delete_directories(self):
        for d in self.state.get_generated_dirs():
            if os.path.exists(d):
                shutil.rmtree(d)

    def delete_batchfiles(self):
        for f in self.state.get_generated_batchfiles():
            if os.path.exists(f):
                os.remove(f)

    #cmd:generate
    def generate_files(self, interactive=False):
        #TODO: check status, make state diagram of possible transitions, when do things need to be deleted etc
        self.create_directories()
        self.create_batchfiles(interactive)

    #cmd:delete        
    def delete_files(self, interactive=False):
        if not interactive or yesno_prompt("Delete all generated files, and work dirs, possibly including results?"):
            self.delete_directories()
            self.delete_batchfiles()
    
    #cmd:list
    def list_files(self):
        dirs = self.state.get_generated_dirs()
        batchfiles = self.state.get_generated_batchfiles()
        outputs = self.state.get_output_files()
        if batchfiles or dirs:
            print("BBAR has generated the following files:")
        else:
            print("BBAR has generated no files for the current configuration")
        if dirs:
            print()
            print("Worktrees:")
        #TODO: store and print generated dirs as trees
        for d in dirs:
            print("\t",d)

        if batchfiles:
            print()
            print("Batch files:")
            for f in batchfiles:
                print("\t",f)

        if outputs:
            print()
            print("Output files detected in workdirs:")
            for o in outputs:
                print("\t",o)

        #TODO: list files, in case someone wants to make sure before deleting 

    #TODO: allow more than one runner? sbatch is kind of hard coded now, but it's also hard coded in the model
    #cmd:run
    def run_benchmarks(self):
        self.generate_files()
        for batch_cfg in self.slurm_batch_configs:
            filename = batch_cfg.filename
            if os.path.exists(filename):
                subprocess.run(["sbatch",filename])

    #cmd:archive
    def archive_output(self):
        archive_name = self.archive_name
        with tempfile.TemporaryDirectory() as tmpdir:
            for batch_cfg in self.slurm_batch_configs:
                for wd in batch_cfg.commands.workdirs:
                    try:
                        path = Path(wd).relative_to(Path('.').resolve())
                    except:
                        path = Path(wd)
                    tmpwd = str(Path(tmpdir)/wd)

                    os.makedirs(tmpwd, exist_ok=True)
                    for f in os.listdir(wd):
                        shutil.copy(Path(wd)/f, tmpwd)
                with open(Path(tmpdir)/"bbar.toml","w") as f:
                    toml.dump(self.config,f)
                shutil.make_archive(archive_name,'gztar', tmpdir)
                

    def scan_for_results(self):
        pass

    #cmd:test (TODO:change to better tests)
    def show_files(self):
        for batch_cfg in self.slurm_batch_configs:
            print(batch_cfg,"\n")

