import sys
import os
import secrets
from datetime import datetime
from .get_process import get_process
from helper import get_config
from argparse import Namespace 
from helper import create_socket_connection, send_data
from config import logger
import cli.add.common as common

def notify_socket(args: Namespace) -> None:
    client_socket = create_socket_connection()

    try:
        process_info = get_process(args.process)
        _, _, limit = get_config()

        if not process_info:
            raise Exception('The program is not running, please start the application')
        
        process_name = process_info['name']    
        start_time = datetime.now()
        id = args.name or secrets.token_hex(6)

        json_data = {
            'command': args.command,
            id: {
                'process_name': process_name,
                'pid': process_info['pid'],
                'track_pid': os.getpid(),
                'start_time': start_time.strftime('%Y/%m/%d %H:%M:%S'),
                'status': 'running',
                'conn': None
            }
        }

        received_data = send_data(client_socket, json_data).lower()

        if received_data == 'ok' and args.verbose:
            logger.info(f'Tracking started: {process_name}')
        elif received_data == 'duplicate id':
            raise Exception(f"Id '{args.name}' is already in use")
        elif received_data == 'duplicate process':
            raise Exception(f'Already tracking {process_name}')
        elif received_data == 'limit':
            process_word = 'process' if limit == 1 else 'processes'
            raise Exception(f'Maximum process tracking limit exceeded. You can only run up to {limit} {process_word} simultaneously')

        common.client_socket = client_socket
        common.process_name = process_name
        common.start_time = start_time
    except Exception as e:
        logger.error(e)
        client_socket.close()
        sys.exit(1)