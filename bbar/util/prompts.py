#Utilities for user input
def yesno_prompt(prompt=None, default=False):
    if prompt is None:
        prompt = "Do you really want to do this?"
    if default:
        prompt = f"{prompt} [Y/n] "
    else:
        prompt = f"{prompt} [N/y] "

    while True:
        answer = input(prompt).lower()
        if not answer:
            return default
        if answer in ["y","yes"]:
            return True
        elif answer in ["n","no"]:
            return False
        print("please enter either y or n")

