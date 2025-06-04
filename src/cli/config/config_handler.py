import sys
import ipaddress
from config import logger
from argparse import Namespace
from helper import get_config, check_socket_running, check_ip_valid, create_config

def validate_args(args: Namespace) -> None:
    if not any([args.ip, args.port is not None, args.limit_max_process is not None]):
        raise ValueError('You must provide at least one of the following arguments: -i, -p, or -l')
    
    if args.ip:
        ipaddress.ip_address(args.ip)

    if args.port is not None and not (1 <= args.port <= 65535):
        raise ValueError('Invalid port number, port must be between 1 and 65535')

    if args.limit_max_process is not None:
        if args.limit_max_process >= 24:
            args.limit_max_process = 24
            if args.verbose:
                logger.warning('The specified limit is too high, it has been automatically set to the maximum limit of 24')
        elif args.limit_max_process < 1:
            args.limit_max_process = 1
            if args.verbose:
                logger.warning('The specified limit cannot be 0 or a negative value, it has been automatically set to the minimum valid limit of 1')

def handle_set(args: Namespace) -> None:
    try:
        validate_args(args)
    except ValueError as e:
        logger.error(e)
        sys.exit(1)    

    ip, port, limit = get_config()
    check_socket_running(ip, port)

    i = args.ip or ip
    p = args.port or port
    l = args.limit_max_process or limit

    if args.ip or args.port:
        check_ip_valid(i, p)
    create_config(i, p, l)

    if args.verbose:
        logger.info('Configuration has been saved successfully')

def handle_show() -> None:
    ip, port, limit = get_config()
    print('HOST IP ADDRESS:', ip)
    print('PORT:', port)
    print('MAXIMUM PROCESS LIMIT:', limit)

def config_handler(args: Namespace) -> None:
    subcommand = args.subcommand
    if subcommand == 'set':
        handle_set(args)
    elif subcommand == 'show':
        handle_show()