import argparse
import pprint
from bbar.bbarfile import read_bbarfile
from bbar.constants import default_bbarfile_name

def main():
    command_choices = ["show_config", "test", "generate", "run", "delete", "archive", "list"]

    parser = argparse.ArgumentParser(description='Generates and runs benchmarks for you automatically')
    parser.add_argument("command", choices=command_choices, metavar=f"command", help='{ '+' | '.join(command_choices)+' }')
    parser.add_argument("-f", help="don't ask for confirmation when overwriting or deleting files", action='store_false')
    parser.add_argument("-p", help="command line parameters that override bbarfile parameters.", nargs='+')
    parser.add_argument("--bbarfile", help=f"the bbarfile is a TOML file containing benchmark configuration, (default='{default_bbarfile_name}')")
    args = parser.parse_args()
 
    bbar_project = read_bbarfile(args.bbarfile, parser, args.p)

    try:
        if args.command == "test":
            bbar_project.show_files()
        elif args.command == "generate":
            bbar_project.generate_files(args.f)
        elif args.command == "delete":
            bbar_project.delete_files(args.f)
        elif args.command == "run":
            bbar_project.run_benchmarks()
        elif args.command == "archive":
            bbar_project.archive_output()
        elif args.command == "list":
            bbar_project.list_files()
        elif args.command == "show_config":
            pprint.pprint(bbar_project)
    except Exception as e:
        parser.error(f"Error running command {args.command}:\n\t{e}")
    except KeyboardInterrupt:
        print("\nCaught interrupt signal, exiting")
