from statemachine import StateMachine, State
from statemachine import exceptions as statemachine_exceptions
from bbar.persistence import BBAR_Store
from bbar.logging import info, debug, error
from bbar.constants import BBAR_SUCCESS

#TODO: save state in store, requires init()?

#WARNING: don't define a transition called run
#run is part of the interface to StateMachine used by this class
class BBAR_FSM(StateMachine):
    init = State("init", initial =True)
    generated = State("generated")
    running = State("running")
    completed = State("completed")
    #TODO: add partially completed state, if cancelled but some jobs have finished

    #These can wrap back because they may fail
    generate = init.to(generated, init)
    start = generated.to(running, generated)

    complete = running.to(completed)
    
    #These can wrap back because the user may cancel the transition
    cancel = running.to(generated, running)
    #TODO: REMOVE running -> purge once we have a way to detect completion OR a way to cancel
    purge = generated.to(init, generated) | completed.to(init, completed) | running.to(init, running)

    stay = init.to.itself() | generated.to.itself() | running.to.itself() | completed.to.itself()
    scan = running.to.itself() | completed.to.itself()

    def __init__(self, bbar_project, **options):
        self.bbar_project = bbar_project
        self.store = bbar_project.state
        self.options = options
        start_value = self.store.get_status()
        if start_value is not None:
            super().__init__(start_value = start_value)
        else:
            super().__init__()

    def on_enter_init(self):
        self.store.set_status(self.current_state.value)
        debug("Status set to init")

    def on_enter_generated(self):
        self.store.set_status(self.current_state.value)
        debug("Status set to generated")

    def on_enter_running(self):
        self.store.set_status(self.current_state.value)
        debug("Status set to running")

    def on_enter_completed(self):
        self.store.set_status(self.current_state.value)
        debug("Status set to completed")

    def on_stay(self):
        info(f"Nothing to do, already {self.current_state.identifier}.")

    def on_generate(self):
        if (self.bbar_project.generate_files(**self.options) == BBAR_SUCCESS):
            info("Successfully generated files.")
            return self.generated
        else:
            info("Failed to generate files.")
            return self.init

    def on_start(self):
        if (self.bbar_project.run_benchmarks(**self.options) == BBAR_SUCCESS):
            info("Jobs have been started.")
            return self.running
        else:
            error("Failed to run jobs.")
            return self.generated
    
    def on_cancel(self):
        info("Cancelling all running jobs.")
        info("\"cancel\" not supported yet")
        return self.running

    def on_purge(self):
        info("Purging all generated files (except archives).")
        if (self.bbar_project.delete_files(**self.options) == BBAR_SUCCESS):
            info("All generated BBAR files were deleted.")
            return self.init
        else:
            return self.current_state

    def on_scan(self):
        debug("Scanning for SLURM output files.")
        self.bbar_project.scan_for_results()

    def try_command(self, cmd):
        state = self.current_state
        if (cmd, state) in [("generate",self.generated), ("run",self.running)]:
            self.stay()
            self.print_allowed_actions()
            return

        try:
            if cmd == "generate":
                self.generate()
            elif cmd == "run":
                if state == self.init:
                    self.generate()
                self.start()
            elif cmd == "cancel":
                self.cancel()
            elif cmd == "purge":
                if state == self.running:
                    self.cancel()
                self.purge()
        except statemachine_exceptions.TransitionNotAllowed as e:
            print(f"'bbar {cmd}' not allowed in current state")
            self.print_status()

    def try_system_task(self,task):
        if task == "scan" and self.current_state in [self.running,self.completed]:
            self.scan()


    def print_allowed_actions(self):
        "This has a lot of 'ugly' hacks to make it more readable"
        transitions = [t.identifier for t in self.current_state.transitions if t.identifier not in  ["stay","complete","scan"]]
        transitions = [t if t != "start" else "run" for t in transitions]
        if len(transitions) > 0:
            print(f"Allowed actions: {', '.join(transitions)}")


    def print_status(self):
        print(f"Status: {self.current_state.identifier}")
        if self.current_state in [self.running, self.completed]:
            self.bbar_project.list_output()
        self.print_allowed_actions()
