import socket
from .common import tracked_processes, lock
from helper import get_config
from type import AddType

def check_limit() -> bool:
    _, _, limit = get_config()
    return len(tracked_processes) < limit

def add_handler(conn: socket.socket, json_data: AddType) -> None:
    if not check_limit():
        conn.send(b'limit')
        return
    
    tag = list(json_data.keys())[1] 
    process = json_data[tag]

    with lock:
        for key, value in tracked_processes.items():
            if process['process_name'].lower() == value['process_name'].lower():
                conn.send(b'duplicate process')
                return
            elif key.lower() == tag.lower():
                conn.send(b'duplicate tag')
                return
        
        tracked_processes[tag] = process
        tracked_processes[tag]['conn'] = conn

    conn.send(b'ok')
    