import toml
import os
from bbar.logging import debug

default_storage_path = ".toml_store"

class TOML_Store:
    def __init__(self, storage_path=default_storage_path):

        if storage_path is not None:
            self.storage_path = storage_path
        if os.path.isfile(self.storage_path):
            debug(f"Loading {self.storage_path}")
            self.state = toml.load(self.storage_path)
        else:
            self.state = {}
 
    def get_state(self):
        return self.state

    def get_stored_state(self):
        return toml.load(self.storage_path)

    def load(self):
        self.state = self.get_stored_state()
   
    def store(self):
        with open(self.storage_path,"w") as f:
            toml.dump(self.state, f)

    def set(self, key, value):
        self.state[key] = value

    def get(self, key):
        if key in self.state:
            return self.state[key]
        else:
            return None

    def store_value(self, key, value):
        self.set(key,value)
        self.store()
