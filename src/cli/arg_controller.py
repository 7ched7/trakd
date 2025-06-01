from argparse import Namespace
from .config import config_handler
from server import run_server
from .stop import stop_handler
from .add import add_handler
from .rm import rm_handler
from .rename import rename_handler
from .ps import ps_handler
from .ls import ls_handler
from .report import report_handler
from .reset import reset_handler

def arg_controller(args: Namespace) -> None:
    if args.command == 'config':
        config_handler(args)
    elif args.command == 'start':
        run_server(args.verbose)
    elif args.command == 'stop':
        stop_handler(args)
    elif args.command == 'add':
        add_handler(args)
    elif args.command == 'rm':
        rm_handler(args)
    elif args.command == 'rename':
        rename_handler(args)
    elif args.command == 'ps':
        ps_handler(args)
    elif args.command == 'ls':
        ls_handler()
    elif args.command == 'report':
        report_handler(args)
    elif args.command == 'reset':
        reset_handler(args)
