import os
from config import logger
from argparse import Namespace
from helper import get_config, check_socket_running, create_config, get_logs_dir

def reset_config(verbose: bool) -> None:
    create_config()
    if verbose:
        logger.info('Configuration has been successfully reset to default values')

def reset_logs(verbose: bool) -> None:
    logs_dir = get_logs_dir()
    for filename in os.listdir(logs_dir):
        file_path = os.path.join(logs_dir, filename)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                if verbose:
                    logger.info(f'{filename} deleted')
            except Exception:
                logger.error(f'Could not delete {filename}')

def reset_handler(args: Namespace) -> None:
    ip, port, _ = get_config()
    check_socket_running(ip, port)

    target = args.target
    verbose = args.verbose
    yes = args.yes

    if not yes:
        try:
            confirm = input(f'This will reset {target.upper()} data. Are you sure? [y/N]: ').strip().lower()
            if confirm != 'y':
                logger.info('Reset cancelled')
                return
        except (KeyboardInterrupt, EOFError):
            print()
            logger.info('Reset cancelled')
            return

    if target == 'all':
        reset_config(verbose)
        reset_logs(verbose)
    elif target == 'config':
        reset_config(verbose)
    elif target == 'logs':
        reset_logs(verbose)