from ftfy import *

def fix_mojibake(data):    
    def fix_dict(d):        
        return {k: fix_text(v) if isinstance(v, str) else v for k, v in d.items()}    
    if isinstance(data, list):        
        return [fix_dict(item) for item in data]    
    elif isinstance(data, dict):        
        return fix_dict(data)
    else:        
        return data