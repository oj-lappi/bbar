import argparse
import pprint
from bbar.bbarfile import read_bbarfile, BBARFile_Error
from bbar.constants import default_bbarfile_name
from bbar.state_machine import BBAR_FSM
from bbar.logging import set_verbosity


def analyze(bbar_project):
    bbar_project.scan_for_results()
    state = bbar_project.state
    print()

def main():
    command_choices = ["generate", "run", "purge", "archive", "list", "status", "show_config"]

    parser = argparse.ArgumentParser(description='Generates and runs benchmarks for you automatically')
    parser.add_argument("command", choices=command_choices, metavar=f"command", help='{ '+' | '.join(command_choices)+' }')
    parser.add_argument("-f", help="don't ask for confirmation when overwriting or deleting files", action='store_true')
    parser.add_argument("-p", help="command line parameters that override bbarfile parameters.", nargs='+')
    parser.add_argument("--bbarfile", help=f"the bbarfile is a TOML file containing benchmark configuration, (default='{default_bbarfile_name}')")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v","--verbose", help="verbose level, add more v's for more verbosity", action="count", default=0)
    group.add_argument("-q","--quiet", help="negative verbose level, add more q's for more quietude", action="count", default=0)

    args = parser.parse_args()
 
    set_verbosity(args.verbose - args.quiet)

    try:
        bbar_project = read_bbarfile(args.bbarfile, args.p)
    except BBARFile_Error as e:
        parser.error(e)

    state_machine = BBAR_FSM(bbar_project, interactive = not args.f)
    state_machine.try_system_task("scan")
 

    try:
        if args.command in ["generate","run","cancel","purge"]:
            state_machine.try_command(args.command)
        elif args.command == "analyze":
            analyze(bbar_project)
        elif args.command == "status":
            state_machine.print_status()
        elif args.command == "archive":
            bbar_project.archive_output()
        elif args.command == "list":
            bbar_project.list_files()
        elif args.command == "show_config":
            pprint.pprint(bbar_project)
    #except Exception as e:
    #    parser.error(f"Error running command {args.command}:\n\t{e}")
    except KeyboardInterrupt:
        print("\nCaught interrupt signal, exiting")
