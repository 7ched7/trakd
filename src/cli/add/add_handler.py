import threading
from argparse import Namespace 
from .connection_handler import connection_handler
from .notify_socket import notify_socket
from .signal_handler import signal_handler
from .track_process import track_process
from daemon import daemon

@daemon
def add_handler(args: Namespace) -> None:
    notify_socket(args)
    signal_handler()

    t1 = threading.Thread(target=connection_handler)
    t2 = threading.Thread(target=track_process)
    t1.start()  
    t2.start()

    t1.join()
    t2.join()
