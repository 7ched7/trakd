import threading
from argparse import Namespace 
from .connection_handler import connection_handler
from .notify_socket import notify_socket
from .track_process import track_process
from daemon import daemon

@daemon
def add_handler(args: Namespace) -> None:
    client_socket, process_name, start_time = notify_socket(args)

    t1 = threading.Thread(target=connection_handler, args=(client_socket,))
    t2 = threading.Thread(target=track_process, args=(process_name, start_time))
    t1.start()  
    t2.start()

    t1.join()
    t2.join()
