import json
import sys
from argparse import Namespace
from tabulate import tabulate  
from helper import create_socket_connection, send_data
from config import logger

def get_headers(detailed: bool) -> list[str]:
    headers = ['TRACK ID', 'PROCESS', 'STARTED', 'STATUS']
    if detailed:
        headers.insert(2, 'PID')
        headers.append('CONNECTION')
    return headers

def ps_handler(args: Namespace) -> None:
    client_socket = create_socket_connection()
    data = send_data(client_socket, { 'command': args.command, 'all': args.all, 'detailed': args.detailed })

    try:
        data = json.loads(data)

        headers = get_headers(args.detailed)
        rows = []

        for track_id, process_information in data.items():
            pl = []
            pl.append(track_id)
            pl.extend([ '--' if information == None else information for information in process_information.values() ])
            rows.append(pl)

        print(tabulate(rows, headers, tablefmt='simple', numalign='left'))
    except json.decoder.JSONDecodeError:
        logger.error(f'An error occured: there was a problem retrieving the tracked programs data, please try again')
        sys.exit(1)
    finally:
        client_socket.close()

        

        
