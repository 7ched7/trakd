import select
import time
import socket
import sys
from config import logger
from helper import send_data
from .common import event, queue

def connection_handler(client_socket: socket.socket) -> None:        
    try:
        while not event.is_set():
            ready_to_read, _, _ = select.select([client_socket], [], [], 1)

            if ready_to_read:
                data = client_socket.recv(4096).decode('utf-8')
                if data == 'stop':
                    event.set()
                    break
            
            if not queue.empty():
                json_data = queue.get()
                send_data(client_socket, json_data, wait_for_response=False)
                continue
            
            send_data(client_socket, 'ping', wait_for_response=False, event=event)
            time.sleep(10)
    except Exception as e:
        logger.error(f'Error during connection control: {e}')
        sys.exit(1)
    finally:
        client_socket.close()