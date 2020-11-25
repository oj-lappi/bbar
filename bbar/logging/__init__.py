verbosity = 0

def log(message, level):
    if level <= verbosity:
        print(message)

def error(message):
    log(message,-2)

def warning(message):
    log(message,-1)

def info(message):
    log(message, 0)

def debug(message):
    log(message, 1)

def set_verbosity(new_verbosity):
    global verbosity 
    verbosity = new_verbosity

