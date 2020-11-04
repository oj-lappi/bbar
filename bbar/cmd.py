import sys
import os
import argparse
import toml
from bbar import BenchmarkSet

default_config_file="bbar.toml"

def check_valid_file(file, parser):
    if not os.path.isfile(file):
        #raise argparse.ArgumentTypeError(arg, f"Trying to use non-existent file {file} as config")
        if file == default_config_file:
            parser.error(f"Error generating benchmarks from config file:\n\t No filename provided, and default config file \"{file}\" does not exist")
        else:
            parser.error(f"Error generating benchmarks from config file \"{file}\":\n\t File \"{file}\" does not exist")

def main():
    parser = argparse.ArgumentParser(description='Generates and runs benchmarks for you automatically')
    command_choices = ["test","generate","run"]
    parser.add_argument("command", choices=command_choices, metavar=f"command", help='{ '+' | '.join(command_choices)+' }')
    config_file_arg = parser.add_argument("config_file", nargs="?",default=default_config_file, help=f"a TOML file containing benchmark configurations, (default='{default_config_file}')")
    args = parser.parse_args()
    
    check_valid_file(args.config_file, parser)

    try:
        bset = BenchmarkSet(config_file=args.config_file)
        if not bset.initialized:
            raise("Unknown error")
    except toml.decoder.TomlDecodeError as e:
        parser.error(f"Error parsing TOML in \"{args.config_file}\":\n\t{e}")
    except Exception as e:
        parser.error(f"Error generating benchmarks from config file \"{args.config_file}\":\n\t{e}")


    try:
        if args.command == "test":
            bset.show_files()
        elif args.command == "generate":
            bset.generate_files()
        elif args.command == "run":
            bset.run_benchmarks()
    except Exception as e:
        print(f"{sys.argv[0]}: Error while running command {args.command}:",e)
