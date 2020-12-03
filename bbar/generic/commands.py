from bbar.util.generators import generator_from_config
from bbar.util.deep_union import deep_dict_union
from bbar.generic.environment import Environment_variables, LMOD_modules
from pathlib import Path
import re

class Command_closure:
    def __init__(self, workdir, command_dir, command, arguments, env_vars, format_params):
        self.env_vars = Environment_variables(env_vars)
        self.workdir = workdir.format(**env_vars, **format_params, arguments=arguments)
        self.command_dir = command_dir.format(**env_vars, **format_params, arguments=arguments)
        self.command = (Path(command_dir) / command).absolute()
        self.arguments = arguments
        self.argv_string = ' '.join([str(v) for v in [self.command]+self.arguments])

cond_regex=re.compile("\s*(?P<lhs>\w+)\s*(?P<op>\W+)\s*(?P<rhs>\w+)\s*")
#Extremely tiny, limited condition parser. Only allow 3 tokens, <lhs> <op>, <rhs>
def condition_eval(condition, format_params):
    m = cond_regex.search(condition)
    try:
        lhs, op, rhs = m.group('lhs'),m.group('op'),m.group('rhs')
        if lhs == "N":
            lhs = int(format_params["SBATCH_N"])
        elif lhs == "n":
            lhs = int(format_params["SBATCH_n"])
        else:
            lhs = int(lhs)

        if rhs == "N":
            rhs = int(format_params["SBATCH_N"])
        elif rhs == "n":
            rhs = int(format_params["SBATCH_n"])
        else:
            rhs = int(rhs)
        
        if op == "=" or op == "==":
            return lhs == rhs
        if op == "!=":
            return lhs != rhs
        if op == ">":
            return lhs > rhs
        if op == "<":
            return lhs < rhs

        return false

    except:
        raise Exception(f"Bad condition {condition} in bbarfile")
    


#TODO: currently getting stuff from format_params, also get an object to evaluate conditionals on
class Commands:
    def __init__(self, config, format_params):
        cfg = config.copy()
        conditionals = cfg["if"] if "if" in cfg else {}
        for condition, conditional_value in conditionals.items():
            if condition_eval(condition, format_params):
                #add contents of v, a dict, to cfg
                cfg = deep_dict_union(cfg, conditional_value)

        workdir = cfg["workdir"]
        command_dir = cfg["command_dir"] if "command_dir" in cfg else "."
        command = cfg["command"]

        num_settings = 1
        if "num_settings" in cfg:
            num_settings = int(cfg["num_settings"])

        argument_generators = []
        if "arguments" in cfg:
            try:
                argument_generators = [generator_from_config(i,v,num_settings) for i,v in enumerate(cfg["arguments"])]
            except Exception as e:
                raise Exception("ERROR generating arguments for benchmarks:", e)

        env_var_generators = {}
        if "env_vars" in cfg:
            try:
                env_var_generators = {
                    k:generator_from_config(k,v,num_settings)
                    for k,v in cfg["env_vars"].items()
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
