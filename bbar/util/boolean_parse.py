def human_to_bool(human_says, default=False):
    "interpret typical human ways of saying true or false"
    s = str(human_says).lower()
    if s in ["no","false","f","0","off"]:
        return False
    if s in ["yes","true","t","1","on"]:
        return True
    raise Exception(f"Invalid flag value: {human_says}")



    

