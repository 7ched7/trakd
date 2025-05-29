import os

def daemon(func):
    def wrapper(*args, **kwargs):
        if os.fork(): 
            return
        func(*args, **kwargs)
        os._exit(os.EX_OK)
    return wrapper