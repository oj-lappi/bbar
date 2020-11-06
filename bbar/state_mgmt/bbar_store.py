from .toml_store import TOML_Store
bbar_default_storage_path = ".bbar_state"

class BBAR_Store(TOML_Store):
    generated_dirs_key = "generated_dirs"
    generated_batchfiles_key = "generated_batchfiles"
    output_files_key = "output_files"
    state_counter_key = "STATE_COUNTER"
    
    def __init__(self, storage_path=bbar_default_storage_path):
        super().__init__(storage_path)

    def get_state_counter(self):
        return self.get(BBAR_Store.state_counter_key) or 0

    def get_generated_dirs(self):
        return self.get(BBAR_Store.generated_dirs_key) or []

    def get_generated_batchfiles(self):
        return self.get(BBAR_Store.generated_batchfiles_key) or []

    def get_output_files(self):
        return self.get(BBAR_Store.output_files_key) or []

    def add_generated_dir(self, new_dir):
        dirs = self.get_generated_dirs()
        dirs.append(new_dir)
        self.increment_state_counter()
        self.store_value(BBAR_Store.generated_dirs_key, dirs)
    
    def add_generated_batchfile(self, new_file):
        files = self.get_generated_batchfiles()
        files.append(new_file)
        self.increment_state_counter()
        self.store_value(BBAR_Store.generated_batchfiles_key, files)
    
    def add_output_file(self, new_file):
        files = self.get_output_files()
        files.append(new_file)
        self.increment_state_counter()
        self.store_value(BBAR_Store.output_files_key, files)
    
    def increment_state_counter(self):
        counter = self.get_state_counter()
        self.set(BBAR_Store.state_counter_key, counter+1)
