class LMOD_modules:
    def __init__(self,cfg):
        self.module_list = cfg["modules"] if "modules" in cfg else []
        
    def __repr__(self):
        if self.module_list:
            return f"module load {' '.join(self.module_list)}"
        return ""
    
class Environment_variables:
    def __init__(self,var_dict):
        self.var_dict = {k:v for k,v in var_dict.items()}
        
    def __repr__(self):
        if self.var_dict:
            return f"{' '.join([f'{k}={v}' for k,v in self.var_dict.items()])}"
        return ""
