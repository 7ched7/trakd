import socket
import json
from .common import tracked_processes, lock

def status_handler(conn: socket.socket, server_socket: socket.socket):
    ip, port = server_socket.getsockname()

    with lock:
        status_data = {
            'ip': ip,
            'port': port,
            'tracked_processes': len(tracked_processes),
            'running': 0,
            'stopped': 0
        }

        for process_info in tracked_processes.values():
            status = process_info.get('status')
            if status == 'running':
                status_data['running'] += 1
            else:
                status_data['stopped'] += 1

    conn.send(json.dumps(status_data).encode('utf-8'))