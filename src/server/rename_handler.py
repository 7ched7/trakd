import socket
from .common import tracked_processes, lock
from type import RenameType

def rename_handler(conn: socket.socket, json_data: RenameType) -> None:
    id = json_data.get('process')
    new_id = json_data.get('new_id')

    with lock:
        if new_id in tracked_processes.keys():
            conn.send(b'duplicate')
            return
        if id in tracked_processes.keys():
            tracked_processes[new_id] = tracked_processes.pop(id)            
        else:
            conn.send(b'error')
            return
    
    conn.send(b'ok')

