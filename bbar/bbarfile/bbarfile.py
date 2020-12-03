import os
import toml
from bbar.bbar import BBAR_Project
from bbar.constants import default_bbarfile_name
from .defaults import bbarfile_defaults
from bbar.logging import debug

class BBARFile_Error(Exception):
    pass

#TODO: do some fancy error messages printing out the offending lines

def check_valid_file(f):
    if not os.path.isfile(f):
        raise BBARFile_Error(f"Error reading bbarfile \"{f}\":\n\t File \"{f}\" does not exist")

def deep_dict_union(original_dict, override_dict):
    for k,v in override_dict.items():
        if k in original_dict:
            if isinstance(original_dict[k],dict) and isinstance(v,dict):
                deep_dict_union(v, original_dict[k])        
                continue
        original_dict[k] = v
    return original_dict

def apply_user_overrides(original, overrides):
    if overrides:
        for override in overrides:
            try:
                override_config = toml.loads(override)
            except toml.decoder.TomlDecodeError as e:
                raise BBARFile_Error(f"Error parsing command line bbarfile override parameter \"-p {override}\":\n\t{e}")

            original = deep_dict_union(original,override_config)
    return original
 

def read_bbarfile( bbarfile_path, overrides):

    debug(f"Using bbarfile \"{bbarfile_path}\"", condition=bbarfile_path)
    bbarfile_path = bbarfile_path or default_bbarfile_name
    debug(f"Command line override parameters: {overrides}", condition=overrides)

    check_valid_file(bbarfile_path)
    defaults = toml.loads(bbarfile_defaults)
    
    try:
        bbarfile_data = toml.load(bbarfile_path)
        bbarfile_data = deep_dict_union(defaults, bbarfile_data)
        bbarfile_data = apply_user_overrides(bbarfile_data, overrides)
        bset = BBAR_Project(bbarfile_data)
        if not bset.initialized:
            raise("Unknown error")
    except toml.decoder.TomlDecodeError as e:
        raise BBARFile_Error(f"Error parsing bbarfile TOML in \"{bbarfile_path}\":\n\t{e}")
    except Exception as e:
        raise(e)
        #raise BBARFile_Error(f"Error reading or parsing bbarfile \"{bbarfile_path}\":\n\t{e}")

    return bset
