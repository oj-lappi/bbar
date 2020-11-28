from bbar.util.generators import generator_from_config
from bbar.generic.environment import Environment_variables, LMOD_modules
from pathlib import Path

class Command_closure:
    def __init__(self, workdir, command_dir, command, arguments, env_vars, format_params):
        self.env_vars = Environment_variables(env_vars)
        self.workdir = workdir.format(**env_vars, **format_params, arguments=arguments)
        self.command_dir = command_dir.format(**env_vars, **format_params, arguments=arguments)
        self.command = (Path(command_dir) / command).absolute()
        self.arguments = arguments
        self.argv_string = ' '.join([str(v) for v in [self.command]+self.arguments])

class Commands:
    def __init__(self, config, format_params):
        workdir = config["workdir"]
        command_dir = config["command_dir"] if "command_dir" in config else "."
        command = config["command"]

        num_settings = 1
        if "num_settings" in config:
            num_settings = int(config["num_settings"])

        argument_generators = []
        if "arguments" in config:
            try:
                argument_generators = [generator_from_config(i,v,num_settings) for i,v in enumerate(config["arguments"])]
            except Exception as e:
                raise Exception("ERROR generating arguments for benchmarks:", e)

        env_var_generators = {}
        if "env_vars" in config:
            try:
                env_var_generators = {
                    k:generator_from_config(k,v,num_settings)
                    for k,v in config["env_vars"].items()
                }
            except Exception as e:
                raise Exception("ERROR generating environment variables for benchmarks:", e)
        
        self.commands = [Command_closure( 
                             workdir, command_dir, command,
                             [next(a) for a in argument_generators],
                             {k:next(v) for k,v in env_var_generators.items()},
                             format_params) for _ in range(num_settings)]

        self.workdirs = [c.workdir for c in self.commands]

    def __repr__(self):
        return "\n".join([f"pushd {cmd_closure.workdir} &>/dev/null && {cmd_closure.env_vars} {cmd_closure.argv_string} && popd &> /dev/null" for cmd_closure in self.commands])
