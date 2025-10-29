import argparse
from client import Client
from server import Server
from __version__ import __version__

class CliManager:
    '''
    CLI Manager class: handles command-line interface parsing and delegates
    commands to the Client and Server instances.
    '''

    def __init__(self, client: Client, server: Server):
        '''
        Initializes the CLI manager with Client and Server instances.
        '''

        self.client = client
        self.server = server

    def _len_check(self, s: str) -> str:
        '''
        Validates that a tracking ID string length is between 3 and 24 characters.
        Raises argparse.ArgumentTypeError if the check fails.
        '''

        min_length = 3
        max_length = 24
        if len(s) >= min_length and len(s) <= max_length:
            return s
        raise argparse.ArgumentTypeError(f'id length must be between {min_length} and {max_length}')

    def create_parser(self) -> argparse.Namespace:
        '''
        Creates and configures the argument parser for the CLI.
        - Defines main commands
        - Adds subcommands and their specific arguments
        - Supports custom validation for tracking IDs
        Returns the parsed arguments namespace.
        '''

        parser = argparse.ArgumentParser(
            prog='trakd',
            description='Keep track of process runtime',
        )
        parser.add_argument('-v', '--version', action='version', version=f'v{__version__}')

        subparsers = parser.add_subparsers(dest='command', required=True)
        
        start_parser = subparsers.add_parser('start', help='start server')
        start_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')

        stop_parser = subparsers.add_parser('stop', help='stop server')
        stop_parser.add_argument('-f', '--force', action='store_true', help='force stop')
        stop_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')

        status_parser = subparsers.add_parser('status', help='show the status of the server')

        ls_parser = subparsers.add_parser('ls', help='list all processes')

        add_parser = subparsers.add_parser('add', help='start tracking a process')
        add_parser.add_argument('process', help='process name or pid to track')
        add_parser.add_argument('-n', '--name', type=self._len_check, help='add custom tracking id')
        add_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')

        rm_parser = subparsers.add_parser('rm', help='stop tracking a process')
        rm_parser.add_argument('id', help='id of the tracked process to stop')
        rm_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')

        ps_parser = subparsers.add_parser('ps', help='show status of tracked processes')
        ps_parser.add_argument('-a', '--all', action='store_true', help='show both currently tracked and stopped processes')
        ps_parser.add_argument('-d', '--detailed', action='store_true', help='show detailed information about tracked processes')

        rename_parser = subparsers.add_parser('rename', help='rename tracking id of a process')
        rename_parser.add_argument('id', help='current tracking id')
        rename_parser.add_argument('new_id', type=self._len_check, help='new tracking id')
        rename_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')

        report_parser = subparsers.add_parser('report', help='show report')
        report_parser.add_argument('--daily', default=True, action='store_true', help='show daily report')
        report_parser.add_argument('--weekly', action='store_true', help='show weekly report')
        report_parser.add_argument('--monthly', action='store_true', help='show monthly report')

        user_parser = subparsers.add_parser('user', help='manage users')
        user_subparsers = user_parser.add_subparsers(dest='subcommand', required=True)

        user_add_parser = user_subparsers.add_parser('add', help='add a new user')
        user_add_parser.add_argument('username', help='username')
        user_add_parser.add_argument('-s', '--switch', action='store_true', help='switch after user is created')
        user_add_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')
        user_rm_parser = user_subparsers.add_parser('rm', help='remove a user')
        user_rm_parser.add_argument('username')
        user_rm_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')
        user_switch_parser = user_subparsers.add_parser('switch', help='switch user')
        user_switch_parser.add_argument('username')
        user_switch_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')
        user_rename_parser = user_subparsers.add_parser('rename', help='rename username')
        user_rename_parser.add_argument('old_username')
        user_rename_parser.add_argument('new_username')
        user_rename_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')
        user_list_parser = user_subparsers.add_parser('ls', help='list all users')

        config_parser = subparsers.add_parser('config', help='manage configuration')
        config_subparsers = config_parser.add_subparsers(dest='subcommand', required=True)

        config_set_parser = config_subparsers.add_parser('set', help='set configuration')
        config_set_parser.add_argument('-i', '--ip', help='set host ip address')
        config_set_parser.add_argument('-p', '--port', type=int, help='set port number')
        config_set_parser.add_argument('-l', '--limit_max_process', type=int, help='set the maximum number of concurrently tracked processes')
        config_set_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')
        config_show_parser = config_subparsers.add_parser('show', help='show current configuration')

        reset_parser = subparsers.add_parser('reset', help='reset program')
        reset_parser.add_argument('target', choices=['all', 'config', 'logs'], help='what to reset')
        reset_parser.add_argument('-y', '--yes', action='store_true', help='skip confirmation')
        reset_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')

        args = parser.parse_args()

        return args

    def arg_controller(self, args: argparse.Namespace) -> None:
        '''
        Controls CLI commands based on the parsed arguments.
        Delegates each command to the appropriate method in Client or Server.
        '''

        command = args.command
        client = self.client 
        server = self.server

        if command == 'start':
            server.run_server(args.verbose)
        elif command == 'stop':
            client.stop_handler(args)
        elif command == 'status':
            client.status_handler()
        elif command == 'ls':
            client.ls_handler()
        elif command == 'add':
            client.add_handler(args)
        elif command == 'rm':
            client.rm_handler(args)
        elif command == 'ps':
            client.ps_handler(args)
        elif command == 'rename':
            client.rename_handler(args)
        elif command == 'report':
            client.report_handler(args)
        elif command == 'user':
            client.user_handler(args)
        elif command == 'config':
            client.config_handler(args)
        elif command == 'reset':
            client.reset_handler(args)