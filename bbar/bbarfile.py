import os
import toml
from bbar.bbar import BBAR_Project
from bbar.constants import default_bbarfile_name

def check_valid_file(f, parser, default):
    if not os.path.isfile(f):
        if default:
            parser.error(f"Error reading bbarfile:\n\t No filename provided, and default \"{default_bbarfile_name}\" does not exist")
        else:
            parser.error(f"Error reading bbarfile \"{f}\":\n\t File \"{f}\" does not exist")

def override_dict(overriding_dict, original_dict):
    for k,v in overriding_dict.items():
        if k in original_dict:
            if isinstance(original_dict[k],dict) and isinstance(v,dict):
                override_dict(v, original_dict[k])        
                continue
        original_dict[k] = v
    return original_dict

def parse_overrides(overrides, config, argparser):
    if overrides:
        for override in overrides:
            try:
                override_config = toml.loads(override)
            except toml.decoder.TomlDecodeError as e:
                argparser.error(f"Error parsing command line bbarfile override parameter \"-p {override}\":\n\t{e}")

            config = override_dict(override_config, config)
    return config
 
def read_bbarfile(bbarfile_path, parser, overrides):
    
    default_file_used = False if bbarfile_path else True
    bbarfile_path = bbarfile_path or default_bbarfile_name
    check_valid_file(bbarfile_path, parser, default_file_used)

    try:
        bbarfile_data = toml.load(bbarfile_path)
        bbarfile_data = parse_overrides(overrides, bbarfile_data, parser)
        bset = BBAR_Project(bbarfile_data)
        if not bset.initialized:
            raise("Unknown error")
    except toml.decoder.TomlDecodeError as e:
        parser.error(f"Error parsing bbarfile TOML in \"{args.config_file}\":\n\t{e}")
    except Exception as e:
        raise(e)
        parser.error(f"Error reading or parsing bbarfile \"{args.config_file}\":\n\t{e}")

    return bset
