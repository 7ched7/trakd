import json
import sys
from helper import create_socket_connection, send_data
from config import logger

def status_handler() -> None:
    client_socket = create_socket_connection()
    data = send_data(client_socket, { 'command': 'status' })

    try: 
        data = json.loads(data)

        ip = data.get('ip')
        port = data.get('port')
        tracked_processes = data.get('tracked_processes')
        running = data.get('running')
        stopped = data.get('stopped')

        print(f'SERVER: running')
        print(f'HOST: {ip}:{port}')
        print(f'TRACKED PROCESSES: {tracked_processes} { f'({running} running, {stopped} stopped)' if tracked_processes != 0 else '' } ')

    except json.decoder.JSONDecodeError:
        logger.error(f'There was a problem retrieving the status data, please try again')
        sys.exit(1)
    finally:
        client_socket.close()