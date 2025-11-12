import argparse
import sys
from pathlib import Path
import subprocess
from logger import logger
from constants import is_windows, is_frozen, RED, YELLOW, GREY, BOLD, RESET
from client import Client
from daemonize import daemonize
from server import Server
from __version__ import __version__

class CliManager:
    '''
    Handles command-line interface parsing and 
    delegates commands to the Client and Server instances.
    '''
    
    class CustomArgumentParser(argparse.ArgumentParser):
        '''
        Custom ArgumentParser that overrides the default error handling.
        '''

        def error(self, message: str) -> None:
            if 'invalid choice' in message:
                start_index = message.find('choose from') + len('choose from')
                choices_part = message[start_index:].strip()
                choices = choices_part.strip('()').split(', ')
                available_commands = ', '.join(choices)
                print(f'{RED}invalid command{RESET}\n{BOLD}Choose from:{RESET} {YELLOW}{available_commands}{RESET}')
            else:
                logger.error(message)
            sys.exit(2) 
    
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

    def create_parser(self) -> None:
        '''
        Sets up the command-line argument parser for the program.
        Configures various subcommands that the user can use to interact with the program.
        It creates different sections for managing processes, users, server settings, configuration and more.
        '''

        parser = self.CustomArgumentParser(
            prog='trakd',
            description='Keep track of process runtime',
        )
        parser.add_argument('-v', '--version', action='version', version=f'v{__version__}')

        subparsers = parser.add_subparsers(dest='command')
        
        server_parser = subparsers.add_parser('server', help='manage server')
        server_subparser = server_parser.add_subparsers(dest='subcommand', required=True)
        
        server_subparser.add_parser('run', help=argparse.SUPPRESS) 
        if is_windows:
            server_subparser.add_parser('install', help='install socket service')
            server_subparser.add_parser('remove', help='remove socket service') 
        else:
            server_subparser.add_parser('enable', help='enable socket service')
            server_subparser.add_parser('disable', help='disable socket service')
        server_start_parser = server_subparser.add_parser('start', help='start socket server')
        server_start_parser.add_argument('-d', '--daemonize', action='store_true', help='daemon mode')
        server_status_parser = server_subparser.add_parser('status', help='show the status of the server')
        server_stop_parser = server_subparser.add_parser('stop', help='stop socket server')
        
        ls_parser = subparsers.add_parser('ls', help='list all processes')

        add_parser = subparsers.add_parser('add', help='start tracking a process')
        add_parser.add_argument('process', help='process name or pid to track')
        add_parser.add_argument('-n', '--name', type=self._len_check, help='add custom tracking id')
        add_parser.add_argument('--fg', action='store_true', help='foreground mode')

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
        user_switch_parser = user_subparsers.add_parser('switch', help='switch to user')
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
        self._arg_controller(args)
    
    def _arg_controller(self, args: argparse.Namespace) -> None:
        '''
        Handles and delegates CLI commands to the appropriate methods.
        '''

        command = args.command
        client = self.client 
        server = self.server

        if args.command == None: 
            print(f'{BOLD}TRAKD v{__version__}{RESET} - {GREY}Keep track of process runtime{RESET}\nStart using with {YELLOW}\'trakd --help\'{RESET}')
            return
        
        if command == 'server':
            subcommand = args.subcommand
            
            if subcommand == 'run':
                server.run_server()
                return

            if subcommand == 'start' and args.daemonize:
                daemonize(server.run_server)()  
                return              

            linux_server_subcommands = ['start', 'enable', 'disable']
            win_server_subcommands = [linux_server_subcommands[0]] + ['install', 'remove']
            
            if is_windows and subcommand in win_server_subcommands:
                self._windows_service_handler(subcommand)

            elif subcommand in linux_server_subcommands:
                self._systemd_handler(subcommand)
            
            elif subcommand == 'status':
                client.status_handler()
            elif subcommand == 'stop':
                client.stop_handler()
            return

        command_handlers = {
            'ls': client.ls_handler,
            'add': lambda: daemonize(client.add_handler)(args),
            'rm': lambda: client.rm_handler(args),
            'ps': lambda: client.ps_handler(args),
            'rename': lambda: client.rename_handler(args),
            'report': lambda: client.report_handler(args),
            'user': lambda: client.user_handler(args),
            'config': lambda: client.config_handler(args),
            'reset': lambda: client.reset_handler(args)
        }

        if command in command_handlers:
            command_handlers[command]()

    def _windows_service_handler(self, subcommand: str):
        '''
        Handles the Windows service by determining if the application is frozen. 
        Based on the state, it builds the command to either run the executable or the Python script for the service.
        '''

        if is_frozen:
            base_path = Path(sys.executable).parent
            service_path = base_path / 'service.exe'
            cmd = [str(service_path), subcommand]
        else:
            base_path = Path(__file__).resolve().parent.parent
            service_path = base_path / 'service.py'
            cmd = [sys.executable, str(service_path), subcommand]
        
        if not service_path.exists():
            logger.error(f'{'service.exe' if is_frozen else 'service.py'} not found at {base_path}')
            sys.exit(1)

        subprocess.run(cmd)

    def _systemd_handler(self, subcommand: str):
        '''
        Handles the systemd service by checking if the service file exists at the specified path. 
        It then attempts to run systemd's 'systemctl' command.
        '''

        service_name = 'trakd.service'
        service_path = Path(f'/etc/systemd/system/{service_name}')

        if not service_path.exists():
            logger.error(f'\'{service_name}\' file not found at {service_path.parent}')
            sys.exit(1)

        try:
            cmd = ['systemctl', subcommand, service_name]
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE)

            if result.stdout.strip():
                logger.info(result.stdout.strip())
        except subprocess.CalledProcessError:
            sys.exit(1)