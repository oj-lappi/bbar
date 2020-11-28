import os
import toml
import shutil
import tempfile

from pathlib import Path

from bbar.persistence import BBAR_Store
from bbar.constants import default_bbarfile_name, BBAR_SUCCESS, BBAR_FAILURE
from bbar.logging import error, warning, info, debug
from bbar.scheduler.plugins import get as get_scheduler

from bbar.util.generators import scale_up_generator
from bbar.util.prompts import yesno_prompt
from bbar.util.boolean_parse import human_to_bool


class BBAR_Project:
    "BBAR_Project is a control object that captures all model data and ties actions to those data"
    def __init__(self, bbarfile_data, bbarfile_path=None):
        self.initialized = False

        self.bbarfile_data = bbarfile_data
        self.state = BBAR_Store()
        self.scheduler_name = "SLURM"
        if "scheduler" in bbarfile_data:
            self.scheduler_name = bbarfile_data["scheduler"]

        self.scheduler = get_scheduler(self.scheduler_name)
        
        self.batchfiles = [self.scheduler.Batchfile(bbarfile_data, n_procs)  for n_procs in scale_up_generator(bbarfile_data["scaleup"])]

        #TODO: read archive name from bbarfile
        self.archive_name = "bbar"
        self.initialized = True
 
    def __repr__(self):
        return toml.dumps(self.bbarfile_data)

    def create_directories(self):
        for batch_cfg in self.batchfiles:
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
        
    #Currently, no distinction between failing generation after generating some files, and no files
    #Weird state if only some created: should be special garbage state, or automatically rolled back
    def create_batchfiles(self, interactive=False):
        for batch_cfg in self.batchfiles:
            if interactive and os.path.isfile(batch_cfg.filename):
                if not yesno_prompt("Generated batchfiles will overwrite old ones, is this ok?"):
                    return BBAR_FAILURE
                else:
                    interactive=False
            self.state.add_generated_batchfile(batch_cfg.filename)
            batch_cfg.create_file()
        return BBAR_SUCCESS
         
    #MAYBE: rewrite to ask if there are outputs in the dirs
    def delete_directories(self):
        for d in self.state.get_generated_dirs():
            if os.path.exists(d):
                shutil.rmtree(d)

    def delete_batchfiles(self):
        for f in self.state.get_generated_batchfiles():
            if os.path.exists(f):
                os.remove(f)

    def generate_files(self, interactive=False, **kwargs):
        "called by the generate command"
        self.create_directories()
        return self.create_batchfiles(interactive)

    def delete_files(self, interactive=False, **kwargs):
        "called by the delete command"
        if not interactive or yesno_prompt("Delete all generated files, and work dirs, possibly including results?"):
            self.delete_directories()
            self.delete_batchfiles()
            self.state.clear_generated_files()
            return BBAR_SUCCESS
        else:
            return BBAR_FAILURE
    
    def list_generated_files(self):
        dirs = self.state.get_generated_dirs()
        batchfiles = self.state.get_generated_batchfiles()
        if batchfiles or dirs:
            print("BBAR has generated the following files:")
        else:
            print("BBAR hasn't generated any files yet")
        if dirs:
            print("\nWorktrees:")
        #TODO: store and print generated dirs as trees
        for d in dirs:
            print("\t",d)

        if batchfiles:
            print("\nBatch files:")
            for f in batchfiles:
                print("\t",f)

    def list_output(self):
        outputs = self.state.get_output_files()
        if outputs:
            print("\nDetected output files:")
            for o in outputs:
                print("\t",o)

    def list_files(self):
        "called by the list query command"
        self.list_generated_files()
        self.list_output()
        
    def run_batchfiles(self, **kwargs):
        "called by the run command"
        info(f"Using scheduler {self.scheduler_name}")

        for batchfile in self.batchfiles:
            filename = batchfile.filename
            if os.path.exists(filename):
                try:
                    self.scheduler.schedule_job(batchfile)
                except BaseException as e:
                    error(f"Exception in scheduler {self.scheduler}, calling schedule_job('{filename}'):\n\t{e}\n")
                    #TODO: cancel existing jobs
                    return BBAR_FAILURE
            else:
                error(f"Batch file {filename} doesn't exist")
                #TODO: cancel existing jobs
                return BBAR_FAILURE
        return BBAR_SUCCESS

    def archive_output(self, **kwargs):
        "called by the archive command"
        archive_name = self.archive_name
        with tempfile.TemporaryDirectory() as tmpdir:
            for batch_cfg in self.batchfiles:
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
        for batchfile in self.batchfiles:
            output_file = batchfile.output
            #TODO: match SLURM patterns
            #REQUIRES: capture SLURM job ids and other SLURM parameters that could be part of this
            #job id should be enough, the rest can be acquired through sstat
            if os.path.isfile(output_file):
                self.state.add_output_file(output_file)
            #for workdir in batchfile.commands.workdirs:
            #    #TODO: check contents of workdir, needed for programs that generate files as output
