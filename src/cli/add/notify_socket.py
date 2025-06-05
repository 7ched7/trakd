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
    socket = create_socket_connection()

    try:
        process_info = get_process(args.process)
        _, _, limit = get_config()

        if not process_info:
            raise Exception('The program is not running, please start the application')
        
        name = process_info['name']    
        now = datetime.now()
        id = args.name or secrets.token_hex(6)

        json_data = {
            'command': args.command,
            id: {
                'process_name': name,
                'pid': process_info['pid'],
                'track_pid': os.getpid(),
                'start_time': now.strftime('%Y/%m/%d %H:%M:%S'),
                'status': 'running',
                'conn': None
            }
        }

        received_data = send_data(socket, json_data).lower()

        if received_data == 'ok' and args.verbose:
            logger.info(f'Tracking started: {name}')
        elif received_data == 'duplicate tag':
            raise Exception(f"Tag '{args.name}' is already in use")
        elif received_data == 'duplicate process':
            raise Exception(f'Already tracking {name}')
        elif received_data == 'limit':
            process_word = 'process' if limit == 1 else 'processes'
            raise Exception(f'Maximum process tracking limit exceeded. You can only run up to {limit} {process_word} simultaneously')

        common.client_socket = socket
        common.process_name = name
        common.start_time = now
    except Exception as e:
        logger.error(f'An error occured: {e}')
        socket.close()
        sys.exit(1)