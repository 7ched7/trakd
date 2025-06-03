import select
import time
import sys
from config import logger
from helper import send_data
import cli.add.common as common

def connection_handler() -> None:     
    client_socket = common.client_socket
    queue = common.queue
    event = common.event

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