import os
import toml
import shutil
import subprocess
import tempfile

from pathlib import Path

from bbar.persistence import BBAR_Store
from .batchfile import SLURM_batchfile
from .generators import scale_up_generator
from .prompts import yesno_prompt
from bbar.constants import default_bbarfile_name


class BBAR_Project:
    def __init__(self, bbarfile_data, bbarfile_path=None):
        self.initialized = False
        self.bbarfile_data = bbarfile_data
        self.state = BBAR_Store()
        self.slurm_batchfiles = [SLURM_batchfile(bbarfile_data, n_procs)  for n_procs in scale_up_generator(bbarfile_data["scaleup"])]
        #TODO: read archive name from bbarfile
        self.archive_name = "bbar"
        self.initialized = True
        
    def create_directories(self):
        for batch_cfg in self.slurm_batchfiles:
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
        for batch_cfg in self.slurm_batchfiles:
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
            self.state.clear_generated_files()
    
    #cmd:list
    def list_files(self):
        dirs = self.state.get_generated_dirs()
        batchfiles = self.state.get_generated_batchfiles()
        outputs = self.state.get_output_files()
        if batchfiles or dirs:
            print("BBAR has generated the following files:")
        else:
            print("BBAR has generated now files from bbarfile")
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
        for batch_cfg in self.slurm_batchfiles:
            filename = batch_cfg.filename
            if os.path.exists(filename):
                subprocess.run(["sbatch",filename])

    #cmd:archive
    def archive_output(self):
        archive_name = self.archive_name
        with tempfile.TemporaryDirectory() as tmpdir:
            for batch_cfg in self.slurm_batchfiles:
                for wd in batch_cfg.commands.workdirs:
                    try:
                        path = Path(wd).relative_to(Path('.').resolve())
                    except:
                        path = Path(wd)
                    tmpwd = str(Path(tmpdir)/wd)

                    os.makedirs(tmpwd, exist_ok=True)
                    for f in os.listdir(wd):
                        shutil.copy(Path(wd)/f, tmpwd)
                with open(Path(tmpdir)/default_bbarfile_name, "w") as f:
                    toml.dump(self.bbarfile_data,f)
                shutil.make_archive(archive_name,'gztar', tmpdir)
                

    def scan_for_results(self):
        pass

    #cmd:test (TODO:change to better tests)
    def show_files(self):
        for batch_cfg in self.slurm_batchfiles:
            print(batch_cfg,"\n")

