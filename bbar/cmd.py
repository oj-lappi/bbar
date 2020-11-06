import sys
import os
import argparse
import toml
import pprint
from bbar import BenchmarkSet

default_config_file="bbar.toml"

def check_valid_file(f, parser):
    if not os.path.isfile(f):
        #TODO: set a flag when benchmark generation file is supplied instead of checking for a value, user may provide default on cmdline, this is misleading then
        if file == default_config_file:
            parser.error(f"Error reading benchmark config file:\n\t No filename provided, and default config file \"{f}\" does not exist")
        else:
            parser.error(f"Error reading benchmark config file \"{f}\":\n\t File \"{f}\" does not exist")

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
                argparser.error(f"Error parsing command line benchmark generation parameter \"-p {override}\":\n\t{e}")

            config = override_dict(override_config, config)
    return config

def main():
    command_choices = ["show_config", "test", "generate", "run", "delete", "archive", "list"]

    parser = argparse.ArgumentParser(description='Generates and runs benchmarks for you automatically')
    parser.add_argument("command", choices=command_choices, metavar=f"command", help='{ '+' | '.join(command_choices)+' }')
    parser.add_argument("-f", help="don't ask for confirmation when overwriting or deleting files", action='store_false')
    parser.add_argument("-p", help="command line parameters for benchmark generation. Overrides file parameters.", nargs='+')
    #TODO: change the config file argument to an option instead of a positional arg
    #TODO: change name of config file => benchmark control file? benchmark config file? benchmark generation file?
    config_file_arg = parser.add_argument("config_file", nargs="?",default=default_config_file, help=f"a TOML file containing benchmark configurations, (default='{default_config_file}')")

    args = parser.parse_args()
    
    check_valid_file(args.config_file, parser)

    try:
        config = toml.load(args.config_file)
        config = parse_overrides(args.p, config, parser)
        bset = BenchmarkSet(config)
        if not bset.initialized:
            raise("Unknown error")
    except toml.decoder.TomlDecodeError as e:
        parser.error(f"Error parsing TOML in \"{args.config_file}\":\n\t{e}")
    except Exception as e:
        raise(e)
        parser.error(f"Error reading benchmark config file \"{args.config_file}\":\n\t{e}")

    try:
        if args.command == "test":
            bset.show_files()
        elif args.command == "generate":
            bset.generate_files(args.f)
        elif args.command == "delete":
            bset.delete_files(args.f)
        elif args.command == "run":
            bset.run_benchmarks()
        elif args.command == "archive":
            bset.archive_output()
        elif args.command == "list":
            bset.list_files()
        elif args.command == "show_config":
            pprint.pprint(config)
    except Exception as e:
        print(f"{sys.argv[0]}: Error running command {args.command}:",e)
        raise e
    except KeyboardInterrupt:
        print("\nCaught interrupt signal, exiting")
