import socket
from .common import tracked_processes, stop_event, lock
from type import StopType

def stop_handler(conn: socket.socket, json_data: StopType) -> None:
    with lock:
        has_running = bool(tracked_processes)
    
    if json_data['flag'] == 'non-force' and has_running:
        conn.send(b'error')
    else:
        if json_data['flag'] == 'force' and has_running:
            with lock:
                processes_copy = list(tracked_processes.values())
                tracked_processes.clear()  
            for running_process in processes_copy:
                process_conn: socket.socket = running_process['conn']
                try:
                    process_conn.sendall('stop'.encode('utf-8'))
                except OSError:
                    continue

        conn.send(b'ok')
        stop_event.set()