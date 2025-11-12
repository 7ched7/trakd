import threading
import psutil
import time
import sys
import os
import ipaddress
import signal
import secrets
import select
import json
import re
from threading import Event
from queue import Queue
from pathlib import Path
from typing import Any, Dict, Optional, Union
from manager import (
    ProfileManager,
    LogManager,
    ClientSocketManager
)
from logger import logger
from constants import is_windows, GREEN, YELLOW, BOLD, RESET 
from datetime import datetime, timedelta
from argparse import Namespace 
from tabulate import tabulate

class Client:
    '''
    Manages socket connections, tracks processes, 
    communicates with the server, and handles CLI subcommands.
    '''

    def __init__(self):
        '''
        Initializes client attributes:
        - profile, log, and client socket managers
        - event for thread control
        - message queue
        - process information (name, PID, start_time)
        '''

        self.profile_manager = ProfileManager()
        username, ip, port, _ = self.profile_manager.get_current_profile()

        self.log_manager = LogManager(username) 
        self.client_socket_manager = ClientSocketManager(username, ip, port)

        self.event: Event = Event()
        self.queue = Queue()
        self.process_name: str = None
        self.process_pid: int = None
        self.start_time: datetime = None
    
    def _connection_handler(self) -> None:     
        '''
        Thread function that continuously monitors the connection to the server.
        - Handles incoming messages
        - Sends queued messages
        - Periodically sends ping
        '''

        client_socket = self.client_socket_manager.client_socket
        queue = self.queue
        event = self.event

        try:
            logger.info('Connection handler started')

            while not event.is_set():
                ready_to_read, _, _ = select.select([client_socket], [], [], 1)

                if ready_to_read:
                    data = client_socket.recv(4096).decode('utf-8')
                    if data == 'stop':
                        logger.info('Received stop signal, stopping connection handler')
                        event.set()
                        break
                
                if not queue.empty():
                    json_data = queue.get()
                    self.client_socket_manager.send_data(json_data, wait_for_response=False)
                    continue
                
                self.client_socket_manager.send_data('ping', wait_for_response=False, event=event)
                time.sleep(10)
        except Exception as e:
            logger.error(f'Error during connection control: {e}')
            sys.exit(1)
        finally:
            event.set()
            logger.info('Closing client socket')
            client_socket.close()

    def _notify_socket(self, args: Namespace) -> None:
        '''
        Establishes initial connection to the server and sends process information to track.
        - Checks if the process is running
        - Generates or uses provided ID
        - Handles server response
        '''

        self.client_socket_manager.create_connection()
        logger.info('Connection established to the server')

        _, _, _, limit = self.profile_manager.get_current_profile()

        try:
            logger.info(f'Getting process information for {args.process}')
            process_info = self._get_process(args.process)

            if not process_info:
                raise Exception('The program is not running, please start the application')
            
            process_name = process_info['name']    
            start_time = datetime.now()
            id = args.name or secrets.token_hex(6)

            logger.info(f'Generated/Provided ID: {id}')

            json_data = {
                'command': args.command,
                id: {
                    'process_name': process_name,
                    'pid': process_info['pid'],
                    'track_pid': os.getpid(),
                    'start_time': start_time.strftime('%Y/%m/%d %H:%M:%S'),
                    'status': 'running',
                    'conn': None
                }
            }

            logger.info('Sending data to server for tracking...')
            received_data = self.client_socket_manager.send_data(json_data).lower()

            if received_data == 'duplicate id':
                raise Exception(f'Id \'{args.name}\' is already in use')
            elif received_data == 'duplicate process':
                raise Exception(f'Already tracking \'{process_name}\'')
            elif received_data == 'limit':
                process_word = 'process' if limit == 1 else 'processes'
                raise Exception(f'Maximum process tracking limit exceeded. You can only run up to {limit} {process_word} simultaneously')

            self.process_name = process_name
            self.process_pid = process_info['pid']    
            self.start_time = start_time
        except Exception as e:
            logger.error(e)
            self.client_socket_manager.client_socket.close()
            sys.exit(1)

    def _get_process(self, process: str) -> Optional[Dict[str, Any]]:
        '''
        Returns information about a process given its name or PID.
        Iterates through system processes to find a match.
        '''

        target: Union[str, int] = int(process) if process.isdigit() else process

        for proc in psutil.process_iter(['name', 'pid']):
            if self._is_self_tracking_process(proc):
                continue

            name = proc.info.get('name')
            pid = proc.info.get('pid')

            if isinstance(target, int) and target == pid:
                return proc.info
            elif isinstance(target, str) and name and target.lower() == name.lower():
                return proc.info
            
        return None
    
    def _is_self_tracking_process(self, proc: psutil.Process) -> bool:
        '''
        Checks if the program is trying to track itself.
        The process is excluded from tracking if:
        - It has the same PID as the current script (self).
        - It is the 'trakd' process (based on specific path).
        - The process command line contains 'trakd'.
        '''

        if proc.pid == os.getpid():
            return True
        
        name = 'trakd.exe' if is_windows else 'trakd'
        if proc.info['name'].lower() == name:
            return True

        try:
            exe_path = Path(proc.exe()).resolve()
            trakd_path = Path('/usr/local/bin/trakd').resolve()
            if exe_path == trakd_path:
                return True
        except:
            pass

        try:
            if proc.cmdline() and 'trakd' in proc.cmdline([0]):
                return True
        except:
            pass

        return False

    def _track_process(self) -> None:
        '''
        Continuously tracks the specified process.
        - Updates status
        - Saves start/end times at intervals
        - Puts updates into the message queue
        '''

        event = self.event
        queue = self.queue
        start_time = self.start_time
        process_name = self.process_name
        process_pid = self.process_pid

        logger.info(f'Tracking started: {process_name}')

        self.log_manager.save_start_time(process_name, start_time)
        self.log_manager.save_end_time(process_name, start_time)
        
        save_interval = timedelta(minutes=5)
        next_save = start_time + save_interval

        while True:
            process_info = self._get_process(process_name)
            now = datetime.now()

            if process_info:
                if process_pid != None and process_pid != process_info['pid']:
                    logger.info(f'Process {process_name} started')
                    json_data = { 'command': 'update', 'status': 'running', process_info['name']: process_info['pid'] }
                    queue.put(json_data)

                process_pid = self.process_pid = process_info['pid']

                if not start_time:
                    start_time = self.start_time = now
                    self.log_manager.save_start_time(process_name, start_time)
                    self.log_manager.save_end_time(process_name, start_time)
                    next_save = start_time + save_interval
            elif not process_info and start_time:
                logger.info(f'Process {process_name} stopped')
                json_data = { 'command': 'update', 'status': 'stopped', process_name: None }
                queue.put(json_data)
                self.log_manager.save_end_time(process_name, start_time)
                start_time = self.start_time = None

            if now >= next_save and start_time:
                self.log_manager.save_end_time(process_name, start_time)
                next_save = now + save_interval
            
            if event.is_set():
                logger.info(f'Stopping tracking of {process_name}')
                if start_time:
                    self.log_manager.save_end_time(process_name, start_time)
                break
                    
            time.sleep(1)

    def _signal_handler(self) -> None:
        '''
        Registers SIGTERM and SIGINT handlers.
        '''

        signal.signal(signal.SIGTERM, self._save_and_exit)
        signal.signal(signal.SIGINT, self._save_and_exit)

    def _wait_for_interrupt(self) -> None:
        '''
        Waits for a KeyboardInterrupt signal or until an event is set.
        Saves process end time when exiting.
        '''

        try:
            while not self.event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self._save_and_exit(None, None)
           
    def _save_and_exit(self, s, f) -> None:
        '''
        Saves the process end time and sets the event to signal completion.
        '''

        start_time = self.start_time
        process_name = self.process_name

        if start_time:
            self.log_manager.save_end_time(process_name, start_time)
            
        self.event.set()

    def add_handler(self, args: Namespace) -> None:
        '''
        Starts the client tracking system.
        - Establishes connection
        - Sets up signal and interrupt handlers
        - Runs connection and tracking threads
        ''' 
        
        self._notify_socket(args)
        if not is_windows:
            self._signal_handler()
        
        t1 = threading.Thread(target=self._connection_handler)
        t2 = threading.Thread(target=self._track_process)
        t1.start()  
        t2.start()

        if is_windows: 
            self._wait_for_interrupt()

        t1.join()
        t2.join()

    def stop_handler(self) -> None:
        '''
        Sends a stop command to the server.
        '''

        self.client_socket_manager.create_connection()

        try:   
            self.client_socket_manager.send_data({'command': 'stop'}, wait_for_response=False)
            logger.info('Stopping the server')

        except Exception as e:
            logger.error(e)
            sys.exit(1)
        finally:
            self.client_socket_manager.client_socket.close()

    def ls_handler(self) -> None:
        '''
        Lists currently running processes with basic information.
        Displays results in a table format.
        '''

        headers = [f'{YELLOW}USER{RESET}', f'{YELLOW}PID{RESET}', f'{YELLOW}PROCESS{RESET}']
        rows = []

        for proc in psutil.process_iter(['username', 'pid', 'name']):
            try:
                info = proc.info
                row = [info['username'], info['pid'], info['name']]
                rows.append(row)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        print(tabulate(rows, headers, tablefmt='simple', numalign='left'))

    def status_handler(self) -> None:
        '''
        Retrieves and displays server status:
        - IP, port
        - Tracked processes (running/stopped counts)
        '''

        self.client_socket_manager.create_connection()
        data = self.client_socket_manager.send_data({ 'command': 'status' })

        try: 
            data = json.loads(data)

            ip = data.get('ip')
            port = data.get('port')
            tracked_processes = data.get('tracked_processes')
            running = data.get('running')
            stopped = data.get('stopped')

            print(f'{BOLD}SERVER:{RESET} running')
            print(f'{BOLD}HOST:{RESET} {ip}:{port}')
            print(f'{BOLD}TRACKED PROCESSES:{RESET} {tracked_processes} { f'{GREEN}({running} running, {stopped} stopped){RESET}' if tracked_processes != 0 else '' } ')

        except json.decoder.JSONDecodeError:
            logger.error(f'There was a problem retrieving the status data, please try again')
            sys.exit(1)
        finally:
            self.client_socket_manager.client_socket.close()

    def rm_handler(self, args: Namespace) -> None:
        '''
        Removes a tracked process by ID.
        Handles errors if the process is not being tracked.
        '''

        self.client_socket_manager.create_connection()

        try:   
            data = self.client_socket_manager.send_data({ 'command': 'rm', 'process': args.id }).lower()

            if data == 'ok' and args.verbose:
                logger.info(f'Tracking stopped: {args.id}')

            if data == 'error':
                raise Exception(f'{args.id} is not being tracked')
        
        except Exception as e:
            logger.error(e)
            sys.exit(1)
        finally:
            self.client_socket_manager.client_socket.close()

    def ps_handler(self, args: Namespace) -> None:
        '''
        Displays tracked processes from the server in a table.
        Supports detailed view and all processes view.
        '''

        self.client_socket_manager.create_connection()
        data = self.client_socket_manager.send_data({ 'command': args.command, 'all': args.all, 'detailed': args.detailed })

        try:
            data = json.loads(data)

            headers = [f'{YELLOW}TRACK ID{RESET}', f'{YELLOW}PROCESS{RESET}', f'{YELLOW}STARTED{RESET}', f'{YELLOW}STATUS{RESET}']
            if args.detailed:
                headers.insert(2, f'{YELLOW}PID{RESET}')
                headers.append(f'{YELLOW}CONNECTION{RESET}')
            rows = []

            for track_id, process_information in data.items():
                pl = []
                pl.append(track_id)
                pl.extend([ '--' if information == None else information for information in process_information.values() ])
                rows.append(pl)

            print(tabulate(rows, headers, tablefmt='simple', numalign='left'))
        except json.decoder.JSONDecodeError:
            logger.error(f'There was a problem retrieving the tracked programs data, please try again')
            sys.exit(1)
        finally:
            self.client_socket_manager.client_socket.close()

    def rename_handler(self, args: Namespace) -> None:
        '''
        Renames a tracked process ID on the server.
        Handles duplicates and errors.
        '''

        self.client_socket_manager.create_connection()

        id = args.id
        new_id = args.new_id

        try:   
            data = self.client_socket_manager.send_data({ 'command': 'rename', 'process': id, 'new_id': new_id }).lower()

            if data == 'ok' and args.verbose:
                logger.info(f'Id \'{id}\' successfully renamed to \'{new_id}\'')
            elif data == 'error':
                raise Exception(f'{id} is not being tracked')
            elif data == 'duplicate':
                raise Exception(f'Id \'{new_id}\' is already in use')
        except Exception as e:
            logger.error(e)
            sys.exit(1)
        finally:
            self.client_socket_manager.client_socket.close()

    def report_handler(self, args: Namespace) -> None:
        '''
        Generates reports for tracked processes.
        - Supports daily, weekly, or monthly reports
        - Includes total runtime and active days
        '''

        def timedelta_to_str(td: timedelta) -> str:
            total_seconds = int(td.total_seconds())
            
            hours = (total_seconds) // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            return f'{hours}h {minutes}m {seconds}s'
        
        username, _, _, _ = self.profile_manager.get_current_profile()

        try:
            if username is None:
                raise Exception('Please create a user or switch to an existing user to perform')
        except Exception as e:
            logger.error(e)     
            sys.exit(1)
            
        weekly = args.weekly
        monthly = args.monthly
        now = datetime.now()

        logs_dir = self.log_manager.logs_dir

        headers = [f'{YELLOW}PROCESS{RESET}', f'{YELLOW}TOTAL RUN TIME{RESET}']
        if weekly or monthly:
            headers.append(f'{YELLOW}ACTIVE DAYS{RESET}')
        rows = []

        if weekly or monthly:
            inf = {}

            day_range = 30 if monthly else 7

            for day in range(day_range):
                t = now - timedelta(days=day)
                log_file = os.path.join(logs_dir, t.strftime('%Y%m%d'))
                data = self.log_manager.get_logs(log_file)

                for process, time_info in data.items():
                    for info in time_info:
                        start = datetime.fromisoformat(info['start_time'])
                        end = datetime.fromisoformat(info['end_time']) if info['end_time'] else now
                        elapsed_time = end - start

                        if process not in inf:
                            inf[process] = {'total_time': timedelta(), 'active_days': set()}

                        inf[process]['total_time'] += elapsed_time
                        inf[process]['active_days'].add(start.date())

            for process, info in inf.items():
                time_inf = timedelta_to_str(info['total_time'])
                active_days_count = len(info['active_days']) or 1  
                rows.append([process, time_inf, active_days_count])

            print(f'{f'{BOLD}MONTHLY' if monthly else f'{BOLD}WEEKLY'} REPORT - {(now - timedelta(days=day_range-1)).date()} - {now.date()}{RESET}\n')
        else:
            log_file = os.path.join(logs_dir, now.strftime('%Y%m%d'))
            data = self.log_manager.get_logs(log_file)

            for process, time_info in data.items():
                total_elapsed_time = timedelta()
                for info in time_info:
                    start = datetime.fromisoformat(info['start_time'])
                    end = datetime.fromisoformat(info['end_time']) if info['end_time'] else now
                    elapsed_time = end - start
                    total_elapsed_time += elapsed_time
                
                time_inf = timedelta_to_str(total_elapsed_time)
                rows.append([process, time_inf])

            print(f'{BOLD}DAILY REPORT - {now.date()}{RESET}\n')

        print(tabulate(rows, headers, tablefmt='simple', numalign='left'))

    def reset_handler(self, args: Namespace) -> None:
        '''
        Resets data based on target (all/config/logs).
        - Confirms action with user if not forced
        - Resets the specified components
        '''

        username, _, _, _ = self.profile_manager.get_current_profile()

        try:
            if username is None:
                raise Exception('Please create a user or switch to an existing user to perform')
        except Exception as e:
            logger.error(e)     
            sys.exit(1)

        self.client_socket_manager.check_if_socket_running()

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
                logger.info('Reset cancelled')
                return

        if target == 'all':
            self._reset_config(username, verbose)
            self._reset_logs()
        elif target == 'config':
            self._reset_config(username, verbose)
        elif target == 'logs':
            self._reset_logs()

    def _reset_config(self, username: str, verbose: bool) -> None:
        '''
        Resets configuration to default values.
        Optionally logs the action if verbose is True.
        '''

        self.profile_manager.update_profile(username)
        if verbose:
            logger.info('Configuration has been successfully reset to default values')

    def _reset_logs(self) -> None:
        '''
        Deletes all log files in the logs directory.
        Optionally logs each deletion if verbose is True.
        '''

        logs_dir = self.log_manager.logs_dir

        for filename in os.listdir(logs_dir):
            file_path = os.path.join(logs_dir, filename)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    logger.error(f'Could not delete {filename}')

    def user_handler(self, args: Namespace) -> None:
        '''
        Handles user-related operations based on subcommands.
        - 'add': Creates a new user
        - 'rm': Removes an existing user
        - 'switch': Switches to another user
        - 'rename': Renames a user
        - 'ls': Lists all users
        '''

        subcommand = args.subcommand

        if subcommand == 'add':
            self._user_add_handler(args)
        elif subcommand == 'rm':
            self._user_rm_handler(args)
        elif subcommand == 'switch':
            self._user_switch_handler(args)
        elif subcommand == 'rename':
            self._user_rename_handler(args)
        elif subcommand == 'ls':
            self._user_ls_handler()

    def _is_valid_username(self, username: str) -> bool:
        '''
        Validates the username:
        - Must consist of letters, digits, hyphen (-) or underscore (_)
        - Must be between 3 and 16 characters long
        '''

        pattern = r'^[a-zA-Z0-9_-]{3,16}$'

        try:
            if re.match(pattern, username):
                return True
            raise ValueError('Username must only contain letters, digits, hyphens (-) or underscores (_) and its length must be between 3 and 16 characters.')
        except ValueError as e:
            logger.error(e)
            sys.exit(1)    

    def _user_add_handler(self, args: Namespace) -> None: 
        '''
        Adds a new user to the system.
        - Creates the profile if valid
        - Switches to the new user if requested
        '''

        self.client_socket_manager.check_if_socket_running()        

        try:
            username = args.username
            self._is_valid_username(username)

            if not self.profile_manager.create_profile(username):
                raise Exception(f'User \'{username}\' already exists')

            if args.verbose:
                logger.info(f'User \'{username}\' has been created')
            
            if args.switch:
                self._user_switch_handler(args)
        except Exception as e:
            logger.error(e)
            sys.exit(1)    

    def _user_rm_handler(self, args: Namespace) -> None:
        '''
        Removes an existing user from the system.
        - Validates if the user exists before removing
        '''

        self.client_socket_manager.check_if_socket_running()

        try:
            username = args.username

            if not self.profile_manager.remove_profile(username):
                raise Exception(f'User \'{username}\' does not exist')

            if args.verbose:
                logger.info(f'User \'{username}\' has been removed')
        except Exception as e:
            logger.error(e)
            sys.exit(1)   

    def _user_switch_handler(self, args: Namespace) -> None:
        '''
        Switches to a different user profile.
        - Validates if the profile exists before switching
        '''
        
        self.client_socket_manager.check_if_socket_running()

        try:
            username = args.username

            if not self.profile_manager.switch_profile(username):
                raise Exception(f'User \'{username}\' does not exist')

            if args.verbose:
                logger.info(f'Switched to \'{username}\'')
        except Exception as e:
            logger.error(e)
            sys.exit(1)   

    def _user_rename_handler(self, args: Namespace) -> None:
        '''
        Renames an existing user profile.
        - Validates if the old user exists before renaming
        '''

        self.client_socket_manager.check_if_socket_running()

        try:
            old_username, new_username = args.old_username, args.new_username
            self._is_valid_username(new_username)

            if not self.profile_manager.rename_profile(old_username, new_username):
                raise Exception('Ensure the user you try to rename exists and the new username is not taken')

            if args.verbose:
                logger.info(f'User \'{old_username}\' has been renamed to \'{new_username}\'')
        except Exception as e:
            logger.error(e)
            sys.exit(1)   

    def _user_ls_handler(self) -> None:
        '''
        Lists all user profiles.
        - Marks the selected user with "<="
        '''

        profile_data = self.profile_manager.get_profiles()
        
        for profile in profile_data:
            username = f'{BOLD}{profile.get('username')}{RESET}'
            if int(profile.get('selected')): 
                username+=f' {GREEN}<={RESET} '
            print(username)

    def config_handler(self, args: Namespace) -> None:
        '''
        Handles config-related CLI subcommands ("set" and "show").
        Delegates to appropriate internal methods.
        '''
        
        username, _, _, _ = self.profile_manager.get_current_profile()

        try:
            if username is None:
                raise Exception('Please create a user or switch to an existing user to perform')
        except Exception as e:
            logger.error(e)
            sys.exit(1)

        subcommand = args.subcommand
        if subcommand == 'set':
            self._handle_set(args)
        elif subcommand == 'show':
            self._handle_show()

    def _validate_args(self, args: Namespace) -> None:
        '''
        Validates configuration arguments.
        Raises ValueError for invalid IP, port, or limit values.
        Warns if limits are automatically adjusted.
        '''

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

    def _handle_set(self, args: Namespace) -> None:
        '''
        Handles the "set" config command:
        - Validates arguments
        - Checks socket
        - Updates configuration
        - Logs success
        '''

        try:
            self._validate_args(args)
        except ValueError as e:
            logger.error(e)
            sys.exit(1)    

        username, ip, port, limit = self.profile_manager.get_current_profile()
        self.client_socket_manager.check_if_socket_running()

        i = args.ip or ip
        p = args.port or port
        l = args.limit_max_process or limit

        if args.ip or args.port:
            self.client_socket_manager.check_ip_valid()
        self.profile_manager.update_profile(username, i, p, l)

        if args.verbose:
            logger.info('Configuration has been saved successfully')

    def _handle_show(self) -> None:
        '''
        Handles the "show" config command:
        - Retrieves current configuration values
        - Prints them
        '''

        _, ip, port, limit = self.profile_manager.get_current_profile()
        print(f'{BOLD}HOST IP ADDRESS:{RESET}', ip)
        print(f'{BOLD}PORT:{RESET}', port)
        print(f'{BOLD}MAXIMUM PROCESS LIMIT:{RESET}', limit)