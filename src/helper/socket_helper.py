import socket
import sys
import json
from threading import Event
from config import logger
from .config_helper import get_config
from typing import Union, Optional

def create_socket_connection() -> socket.socket:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(5)
    
    host, port, _ = get_config()

    try:
        client_socket.connect((host, port))
        return client_socket
    except ConnectionRefusedError:
        logger.error('Server is down')
        sys.exit(1)
    except socket.gaierror:
        logger.error(f'Address-related error connecting to {host}:{port}')
        sys.exit(1)
    except socket.error:
        logger.error(f'There may be a problem with the host ip address and port configuration')
        sys.exit(1)

def send_data(client_socket: socket.socket, data: Union[str, dict], wait_for_response: bool=True, event: Event=None) -> Optional[str]:
    if isinstance(data, dict):
        data = json.dumps(data)

    try:
        client_socket.sendall(data.encode('utf-8'))

        if wait_for_response:
            received_data = client_socket.recv(4096)
            return received_data.decode('utf-8')
    except (BrokenPipeError, socket.error):
        if event: event.set()
        client_socket.close()
        sys.exit(1)
        