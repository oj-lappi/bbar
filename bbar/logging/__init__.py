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

def log(message, level):
    if level.value <= verbosity.value:
        if level == Loglevel.INFO:
            print(message)
        else:
            print(f"[BBAR {level.name}] {message}")

def error(message):
    log(message,Loglevel.ERROR)

def warning(message):
    log(message,Loglevel.WARNING)

def info(message):
    log(message, Loglevel.INFO)

def debug(message):
    log(message, Loglevel.DEBUG)

def diagnostics(message):
    log(message, Loglevel.DIAGNOSTICS)

def set_verbosity(new_verbosity):
    global verbosity 
    if new_verbosity in [l.value for l in Loglevel]:
        verbosity = Loglevel(new_verbosity)
    else:
        print(f"No such verbose level: {new_verbosity}")
