from enum import Enum


class Loglevel(Enum):
    NOTHING=-3
    ERROR=-2
    WARNING=-1
    INFO=0
    DEBUG=1
    DIAGNOSTICS=2
    EVERYTHING=3

verbosity = Loglevel.INFO

def log(message, level, condition):
    if condition and level.value <= verbosity.value:
        if level == Loglevel.INFO:
            print(message)
        else:
            print(f"[BBAR {level.name}] {message}")

def error(message, condition=True):
    log(message,Loglevel.ERROR, condition)

def warning(message, condition=True):
    log(message,Loglevel.WARNING, condition)

def info(message, condition=True):
    log(message, Loglevel.INFO, condition)

def debug(message, condition=True):
    log(message, Loglevel.DEBUG, condition)

def diagnostics(message, condition=True):
    log(message, Loglevel.DIAGNOSTICS, condition)

def set_verbosity(new_verbosity):
    global verbosity 
    if new_verbosity in [l.value for l in Loglevel]:
        verbosity = Loglevel(new_verbosity)
    else:
        print(f"No such verbose level: {new_verbosity}")
