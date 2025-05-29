import sys
from argparse import Namespace 
from config import logger
from helper import create_socket_connection, send_data

def rm_handler(args: Namespace) -> None:
    client_socket = create_socket_connection()

    try:   
        data = send_data(client_socket, { 'command': 'rm', 'process': args.id }).lower()

        if data == 'ok' and args.verbose:
            logger.info(f'Tracking stopped: {args.id}')

        if data == 'error':
            raise Exception(f'{args.id} is not being tracked')
    
    except Exception as e:
        logger.error(f'An error occurred: {e}')
        sys.exit(1)
    finally:
        client_socket.close()
   