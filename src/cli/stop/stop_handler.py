import sys
from config import logger
from helper  import create_socket_connection, send_data
from argparse import Namespace

def stop_handler(args: Namespace) -> None:
    client_socket = create_socket_connection()

    try:   
        data = send_data(client_socket, {'command': 'stop', 'flag': 'force' if args.force else 'non-force'}).lower()
                
        if data == 'ok' and args.verbose:
            logger.info('Stopping the server')
        elif data == 'error':
            raise Exception('Server stop failed: there are still processes being tracked')

    except Exception as e:
        logger.error(f'An error occurred: {e}')
        sys.exit(1)
    finally:
        client_socket.close()