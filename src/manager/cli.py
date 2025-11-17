import argparse
import os
import shutil
import sys
from pathlib import Path
import subprocess
from logger import logger
from constants import is_windows, is_frozen, RED, YELLOW, GREY, BOLD, RESET
from datetime import datetime, date
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
        server_subparser.add_parser('install', help='install socket service')
        server_subparser.add_parser('remove', help='remove socket service') 
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
        report_parser.add_argument('-s', '--start', default=datetime.combine(date.today(), datetime.min.time()), help='start date (e.g., "2 months ago", "1 week ago", "2025-06-12")')
        report_parser.add_argument('-e', '--end', default=datetime.now(), help='end date (e.g., "today", "yesterday", "2025-07-12")')

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

        if command == None: 
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

            server_subcommands = ['start', 'install', 'remove', 'enable', 'disable']
            
            if is_windows and subcommand in server_subcommands:
                self._windows_service_handler(subcommand)

            elif subcommand in server_subcommands:
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

    def _windows_service_handler(self, subcommand: str) -> None:
        '''
        Handles 'Trakd' service configurations and operations
        - Enables or disables the Trakd service to start automatically or manually.
        - For other subcommands, it manages the execution of a service script (service.exe or service.py).
        '''

        self._is_admin()

        if subcommand == 'enable':
            try:
                subprocess.run(f'sc config Trakd start=auto', check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.strip() or e.stdout.strip()
                logger.error(error_msg)
                sys.exit(1)
        
        elif subcommand == 'disable':
            try:
                subprocess.run(f'sc config Trakd start=demand', check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.strip() or e.stdout.strip()
                logger.error(error_msg)
                sys.exit(1)

        # start/install/remove
        else:
            if is_frozen:
                base_path = Path(sys.executable).parent
                service_path = base_path / 'service.exe'
                cmd = [str(service_path), subcommand]
            else:
                base_path = Path(__file__).resolve().parent.parent
                service_path = base_path / 'service.py'
                cmd = [sys.executable, str(service_path), subcommand]
            
            try:
                if not service_path.exists():
                    raise Exception(f'{'service.exe' if is_frozen else 'service.py'} not found at {base_path}')

                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                sys.exit(1)
            except Exception as e:
                logger.error(e)
                sys.exit(1)
    
    def _systemd_handler(self, subcommand: str) -> None:
        '''
        Handles systemd service operations for the 'trakd' service.
        - Installs or removes the 'trakd' service on the system
        - Manages service states (start, stop, enable, disable) using systemd commands
        '''

        self._is_admin()
        username, home = self._get_current_user()
        
        trakd_path = shutil.which('trakd')
        if not trakd_path:
            logger.error('trakd command not found in PATH')
            logger.error('Make sure trakd is installed and added to your PATH')
            sys.exit(1)

        service_name = 'trakd.service'
        service_path = Path(f'/etc/systemd/system/{service_name}')

        if subcommand == 'install':
            service_str = f'''
[Unit]
Description=Trakd Socket Server
After=network.target
Wants=network.target

[Service]
Type=simple
ExecStart={trakd_path} server run
User={username}
WorkingDirectory={home}/.trakd
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
'''
            
            try:
                with open(service_path, 'w') as f:
                    f.write(service_str.strip() + '\n')

                subprocess.run(['systemctl', 'daemon-reload'], check=True)
                logger.info('Service installed')
            except subprocess.CalledProcessError as e:
                sys.exit(1)
            except Exception as e:
                logger.error(e)
                sys.exit(1)

        elif subcommand == 'remove':
            try:
                if not service_path.exists():
                    raise Exception('Service \'trakd\' not found on this system')
                
                subprocess.run(['systemctl', 'stop', service_name], check=True)
                subprocess.run(['systemctl', 'disable', service_name], check=True)
                subprocess.run(['systemctl', 'daemon-reload'], check=True)
                
                service_path.unlink()
                logger.info('Service removed')
            except subprocess.CalledProcessError as e:
                sys.exit(1)
            except Exception as e:
                logger.error(e)
                sys.exit(1)

        # start/enable/disable
        else:
            try:
                if not service_path.exists():
                    raise Exception('Service \'trakd\' not found on this system')

                cmd = ['systemctl', subcommand, service_name]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)

                if result.stdout.strip():
                    logger.info(result.stdout.strip())
            except subprocess.CalledProcessError as e:
                sys.exit(1)
            except Exception as e:
                logger.error(e)
                sys.exit(1)

    def _is_admin(self) -> None:
        '''
        Checks if the current user has administrative (root) privileges.
        '''

        try:
            if is_windows:
                import ctypes
                if ctypes.windll.shell32.IsUserAnAdmin() == 0:
                    raise Exception('Administrator privileges required, run the command as administrator')
            else:
                if os.getuid() != 0:
                    raise Exception('Root privileges required, run the command with sudo')
        except Exception as e:
            logger.error(e)
            sys.exit(1)

    def _get_current_user(self) -> tuple[str, Path]:
        '''
        Retrieves the current user's username and home directory.
        '''

        import pwd

        if 'SUDO_USER' in os.environ and os.geteuid() == 0:
            username = os.environ['SUDO_USER']
            uid = int(os.environ['SUDO_UID'])
            try:
                pw_entry = pwd.getpwuid(uid)
                if pw_entry.pw_name == username:
                    return username, Path(pw_entry.pw_dir)
            except (KeyError, ValueError):
                pass

        try:
            username = pwd.getpwuid(os.getuid()).pw_name
            home = Path.home()
        except Exception:
            logger.error('An error occurred while retrieving current user information')
            sys.exit(1)

        return username, home