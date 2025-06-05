import socket
import threading
import sys
import json
from config import logger
from daemon import daemon
from .add_handler import add_handler
from .stop_handler import stop_handler
from .status_handler import status_handler
from .rm_handler import rm_handler
from .rename_handler import rename_handler
from .ps_handler import ps_handler
from .update_handler import update_handler
from .common import stop_event
from helper import get_config
from typing import Union
from type import AddType, RemoveType, RenameType, StopType, StatusType, PsType, UpdateType

def convert_json(data: str) -> Union[AddType, RemoveType, RenameType, StopType, StatusType, PsType, UpdateType, bool]:
    try:
        json_data = json.loads(data)
        return json_data
    except json.JSONDecodeError:
        return False

def handle_client(conn: socket.socket, addr: tuple[str, int], server_socket: socket) -> None:
    while not stop_event.is_set(): 
        try:
            data = conn.recv(4096)
        except (ConnectionResetError, OSError):
            break

        if not data:
            break
        
        data = data.decode('utf-8')
        json_data = convert_json(data)
        
        if json_data:
            if json_data['command'] == 'add':
                add_handler(conn, json_data)
            elif json_data['command'] == 'rm':
                rm_handler(conn, json_data)
            elif json_data['command'] == 'rename':
                rename_handler(conn, json_data)
            elif json_data['command'] == 'stop':
                stop_handler(conn, json_data)
            elif json_data['command'] == 'status':
                status_handler(conn, server_socket)
            elif json_data['command'] == 'ps':
                ps_handler(conn, json_data)
            elif json_data['command'] == 'update':
                update_handler(json_data)
            
    conn.close()

@daemon
def run_server(verbose: str) -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    ip, port, _ = get_config()

    try:
        server_socket.bind((ip, port))
    except OSError as e:
        if e.errno == 98:  
            logger.warning('Server is already up and running')
        elif e.errno == 13 or e.errno == 99:
            logger.error('There may be a problem with the host IP address and port configuration or lack of permissions')
        else:
            logger.error(e)
        sys.exit(1)

    server_socket.listen()
    if verbose:
        logger.info('Server is up and running')

    threads = []

    while not stop_event.is_set(): 
        try:
            server_socket.settimeout(1)
            conn, addr = server_socket.accept()

            t = threading.Thread(target=handle_client, args=(conn, addr, server_socket))
            t.start()
            threads.append(t)
        except socket.timeout:
            continue 

    for t in threads:
        t.join()

    server_socket.close()
