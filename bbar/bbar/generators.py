def infinite_stepper(start, step):
    while True:
        yield start
        start+=step
    
def bound_stepper(start, step, num_steps):
    for _ in range(num_steps):
        yield start
        start+=step


def multiplicator(start,step_factor,num_steps):
    for _ in range(num_steps):
        yield start
        start*=step_factor

def const_generator(const):
    while True:
        yield const
        
def list_generator(l):
    for i in l:
        yield l
        
def generator_from_config(name, config, num_steps):
    if isinstance(config, dict):
        if "start" in config and "step" in config:
            return infinite_stepper(config["start"],config["step"])
        
    elif isinstance(config, list):
        if len(config) < num_steps:
            raise Exception(f"Too few items in list provided for {name}, needed {num_steps}, length was {len(config)}")
        return list_generator(config)

    else:
        return const_generator(config)
    
def scale_up_generator(config):
    if isinstance(config, dict):
        if "start" in config and "step" in config and "num_steps" in config:
            return bound_stepper(config["start"],config["step"],config["num_steps"])
        elif "start" in config and "step_factor" in config and "num_steps" in config:
            return multiplicator(config["start"], config["step_factor"], config["num_steps"])
        
    elif isinstance(config, list):
        return list_generator(config)
    
    else:
        return const_generator(config)

#TODO: stepper definitions in bbarfile implicitly coded into if statements, better type checking somehow?
