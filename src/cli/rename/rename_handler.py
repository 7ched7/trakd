import sys
from argparse import Namespace 
from config import logger
from helper import create_socket_connection, send_data

def rename_handler(args: Namespace) -> None:
    client_socket = create_socket_connection()

    id = args.id
    new_id = args.new_id

    try:   
        data = send_data(client_socket, { 'command': 'rename', 'process': id, 'new_id': new_id }).lower()

        if data == 'ok' and args.verbose:
            logger.info(f"Id '{id}' successfully renamed to '{new_id}'")
        elif data == 'error':
            raise Exception(f'{id} is not being tracked')
        elif data == 'duplicate':
            raise Exception(f"Tag '{new_id}' is already in use")
    except Exception as e:
        logger.error(f'An error occurred: {e}')
        sys.exit(1)
    finally:
        client_socket.close()