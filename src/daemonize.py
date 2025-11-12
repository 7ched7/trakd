import __main__
import os
import subprocess
import sys
from constants import is_windows, is_frozen

def daemonize(func):
    def wrapper(*args, **kwargs):
        if '--fg' in sys.argv:
            return func(*args, **kwargs)
        
        if not is_windows:
            _unix_daemonize()  
            return func(*args, **kwargs)

        _windows_detach()
    return wrapper

def _unix_daemonize():
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        sys.exit(1)

    os.chdir('/')
    os.setsid()
    os.umask(0)

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        sys.exit(1)

    dev_null = open(os.devnull, 'r+')
    os.dup2(dev_null.fileno(), sys.stdin.fileno())
    os.dup2(dev_null.fileno(), sys.stdout.fileno())
    os.dup2(dev_null.fileno(), sys.stderr.fileno())

def _windows_detach():
    cmd = [sys.executable]

    if 'server' in sys.argv and 'start' in sys.argv:
        cmd += [] if is_frozen else [sys.argv[0]]
        cmd += ['server', 'run'] 
    else:
        cmd += sys.argv[1:] if is_frozen else sys.argv
        cmd += ['--fg'] 
    
    subprocess.Popen(
        cmd,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    sys.exit(0)