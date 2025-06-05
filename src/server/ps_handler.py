import socket
import json
from .common import tracked_processes, lock
from type import PsType

def ps_handler(conn: socket.socket, json_data: PsType) -> None:
    ps_data = {}

    with lock:
        for track_id, process_info in tracked_processes.items():
            if not json_data['all'] and process_info.get('status') == 'stopped':
                continue

            data = {}
            for key, value in process_info.items():
                if key == 'track_pid':
                    continue

                if not json_data['detailed'] and key in ('pid', 'conn'):
                    continue

                if key == 'conn':
                    try:
                        client_host, client_port = value.getpeername()
                        data[key] = f'{client_host}/{client_port}'
                    except OSError:
                        data[key] = f'Disconnected'
                    continue
                
                data[key] = value

            ps_data[track_id] = data
            
    conn.sendall(json.dumps(ps_data).encode('utf-8'))