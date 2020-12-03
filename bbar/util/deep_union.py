def deep_dict_union(original_dict, override_dict):
    for k,v in override_dict.items():
        if k in original_dict:
            if isinstance(original_dict[k],dict) and isinstance(v,dict):
                deep_dict_union(v, original_dict[k])        
                continue
        original_dict[k] = v
    return original_dict
