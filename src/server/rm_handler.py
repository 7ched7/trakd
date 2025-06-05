import socket
from .common import tracked_processes, lock
from type import RemoveType

def rm_handler(conn: socket.socket, json_data: RemoveType) -> None:
    with lock:
        if json_data['process'] in tracked_processes.keys():
            untracked_process = tracked_processes[json_data['process']]
            process_conn: socket.socket = untracked_process['conn']
            del tracked_processes[json_data['process']]
        else:
            conn.send(b'error')
            return
    try:
        process_conn.sendall('stop'.encode('utf-8'))
    except OSError:
        pass
    
    conn.send(b'ok')

