import socket
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
from threading import Event
from queue import Queue
from typing import Any, Dict, Optional, Union
from helper import (
    create_socket_connection, 
    check_socket_running, 
    check_ip_valid,
    send_data, 
    save_start_time, 
    save_end_time, 
    create_config, 
    get_config, 
    get_logs, 
    get_logs_dir
)
from daemon import daemon
from logger import logger
from datetime import datetime, timedelta
from argparse import Namespace 
from tabulate import tabulate

class Client:
    '''
    Client class: manages socket connections, tracks processes, 
    communicates with the server, and handles CLI subcommands.
    '''

    def __init__(self):
        '''
        Initializes client attributes:
        - socket
        - event for thread control
        - message queue
        - process information (name, PID, start_time)
        '''

        self.client_socket: socket.socket = None
        self.event: Event = Event()
        self.queue = Queue()
        self.start_time: datetime = None
        self.process_name: str = None
        self.process_pid: int = None
    
    def _connection_handler(self) -> None:     
        '''
        Thread function that continuously monitors the connection to the server.
        - Handles incoming messages
        - Sends queued messages
        - Periodically sends ping
        '''

        client_socket = self.client_socket
        queue = self.queue
        event = self.event

        try:
            while not event.is_set():
                ready_to_read, _, _ = select.select([client_socket], [], [], 1)

                if ready_to_read:
                    data = client_socket.recv(4096).decode('utf-8')
                    if data == 'stop':
                        event.set()
                        break
                
                if not queue.empty():
                    json_data = queue.get()
                    send_data(client_socket, json_data, wait_for_response=False)
                    continue
                
                send_data(client_socket, 'ping', wait_for_response=False, event=event)
                time.sleep(10)
        except Exception as e:
            logger.error(f'Error during connection control: {e}')
            sys.exit(1)
        finally:
            client_socket.close()

    def _notify_socket(self, args: Namespace) -> None:
        '''
        Establishes initial connection to the server and sends process information to track.
        - Checks if the process is running
        - Generates or uses provided ID
        - Handles server response
        '''

        client_socket = create_socket_connection()

        try:
            process_info = self._get_process(args.process)
            _, _, limit = get_config()

            if not process_info:
                raise Exception('The program is not running, please start the application')
            
            process_name = process_info['name']    
            start_time = datetime.now()
            id = args.name or secrets.token_hex(6)

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

            received_data = send_data(client_socket, json_data).lower()

            if received_data == 'ok' and args.verbose:
                logger.info(f'Tracking started: {process_name}')
            elif received_data == 'duplicate id':
                raise Exception(f"Id '{args.name}' is already in use")
            elif received_data == 'duplicate process':
                raise Exception(f'Already tracking {process_name}')
            elif received_data == 'limit':
                process_word = 'process' if limit == 1 else 'processes'
                raise Exception(f'Maximum process tracking limit exceeded. You can only run up to {limit} {process_word} simultaneously')

            self.client_socket = client_socket
            self.process_name = process_name
            self.start_time = start_time
        except Exception as e:
            logger.error(e)
            client_socket.close()
            sys.exit(1)

    def _get_process(self, process: str) -> Optional[Dict[str, Any]]:
        '''
        Returns information about a process given its name or PID.
        Iterates through system processes to find a match.
        '''

        target: Union[str, int] = int(process) if process.isdigit() else process

        for proc in psutil.process_iter(['name', 'pid']):
            name = proc.info.get('name')
            pid = proc.info.get('pid')

            if isinstance(target, int) and target == pid:
                return proc.info
            elif isinstance(target, str) and name and target.lower() == name.lower():
                return proc.info
            
        return None

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

        save_start_time(process_name, start_time)
        save_end_time(process_name, start_time)
        
        save_interval = timedelta(minutes=5)
        next_save = start_time + save_interval

        while True:
            process_info = self._get_process(process_name)
            now = datetime.now()

            if process_info:
                if process_pid != None and process_pid != process_info['pid']:
                    json_data = { 'command': 'update', 'status': 'running', process_info['name']: process_info['pid'] }
                    queue.put(json_data)

                process_pid = process_info['pid']

                if not start_time:
                    start_time = now
                    save_start_time(process_name, start_time)
                    save_end_time(process_name, start_time)
                    next_save = start_time + save_interval
            elif not process_info and start_time:
                json_data = { 'command': 'update', 'status': 'stopped', process_name: None }
                queue.put(json_data)
                save_end_time(process_name, start_time)
                start_time = None

            if now >= next_save and start_time:
                save_end_time(process_name, start_time)
                next_save = now + save_interval
            
            if event.is_set():
                if start_time:
                    save_end_time(process_name, start_time)
                break
                    
            time.sleep(1)

    def _signal_handler(self) -> None:
        '''
        Registers SIGTERM and SIGINT handlers to ensure process end times are saved 
        and threads are properly stopped.
        '''

        def save_and_exit(s, f) -> None:
            start_time = self.start_time
            process_name = self.process_name

            if start_time:
                save_end_time(process_name, start_time)
                
            self.event.set()

        signal.signal(signal.SIGTERM, save_and_exit)
        signal.signal(signal.SIGINT, save_and_exit)

    @daemon
    def add_handler(self, args: Namespace) -> None:
        '''
        Starts the client tracking system:
        - Establishes connection
        - Sets up signal handlers
        - Runs connection and tracking threads
        '''

        self._notify_socket(args)
        self._signal_handler()

        t1 = threading.Thread(target=self._connection_handler)
        t2 = threading.Thread(target=self._track_process)
        t1.start()  
        t2.start()

        t1.join()
        t2.join()

    def ls_handler(self) -> None:
        '''
        Lists currently running processes with basic information.
        Displays results in a table format.
        '''

        headers = ['USER', 'PID', 'PROCESS']
        rows = []

        for proc in psutil.process_iter(['username', 'pid', 'name']):
            try:
                info = proc.info
                row = [info['username'], info['pid'], info['name']]
                rows.append(row)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        print(tabulate(rows, headers, tablefmt='simple', numalign='left'))

    def stop_handler(self, args: Namespace) -> None:
        '''
        Sends a stop command to the server.
        - Handles force or non-force stop
        - Logs messages accordingly
        '''

        client_socket = create_socket_connection()

        try:   
            data = send_data(client_socket, {'command': 'stop', 'flag': 'force' if args.force else 'non-force'}).lower()
                    
            if data == 'ok' and args.verbose:
                logger.info('Stopping the server')
            elif data == 'error':
                raise Exception('There are still processes being tracked')

        except Exception as e:
            logger.error(e)
            sys.exit(1)
        finally:
            client_socket.close()

    def status_handler(self) -> None:
        '''
        Retrieves and displays server status:
        - IP, port
        - Tracked processes (running/stopped counts)
        '''

        client_socket = create_socket_connection()
        data = send_data(client_socket, { 'command': 'status' })

        try: 
            data = json.loads(data)

            ip = data.get('ip')
            port = data.get('port')
            tracked_processes = data.get('tracked_processes')
            running = data.get('running')
            stopped = data.get('stopped')

            print(f'SERVER: running')
            print(f'HOST: {ip}:{port}')
            print(f'TRACKED PROCESSES: {tracked_processes} { f'({running} running, {stopped} stopped)' if tracked_processes != 0 else '' } ')

        except json.decoder.JSONDecodeError:
            logger.error(f'There was a problem retrieving the status data, please try again')
            sys.exit(1)
        finally:
            client_socket.close()

    def rm_handler(self, args: Namespace) -> None:
        '''
        Removes a tracked process by ID.
        Handles errors if the process is not being tracked.
        '''

        client_socket = create_socket_connection()

        try:   
            data = send_data(client_socket, { 'command': 'rm', 'process': args.id }).lower()

            if data == 'ok' and args.verbose:
                logger.info(f'Tracking stopped: {args.id}')

            if data == 'error':
                raise Exception(f'{args.id} is not being tracked')
        
        except Exception as e:
            logger.error(e)
            sys.exit(1)
        finally:
            client_socket.close()

    def ps_handler(self, args: Namespace) -> None:
        '''
        Displays tracked processes from the server in a table.
        Supports detailed view and all processes view.
        '''

        client_socket = create_socket_connection()
        data = send_data(client_socket, { 'command': args.command, 'all': args.all, 'detailed': args.detailed })

        try:
            data = json.loads(data)

            headers = ['TRACK ID', 'PROCESS', 'STARTED', 'STATUS']
            if args.detailed:
                headers.insert(2, 'PID')
                headers.append('CONNECTION')
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
            client_socket.close()

    def rename_handler(self, args: Namespace) -> None:
        '''
        Renames a tracked process ID on the server.
        Handles duplicates and errors.
        '''

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
                raise Exception(f"Id '{new_id}' is already in use")
        except Exception as e:
            logger.error(e)
            sys.exit(1)
        finally:
            client_socket.close()

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
        
        weekly = args.weekly
        monthly = args.monthly
        now = datetime.now()
        logs_dir = get_logs_dir()

        headers = ['PROCESS', 'TOTAL RUN TIME']
        if weekly or monthly:
            headers.append('ACTIVE DAYS')
        rows = []

        if weekly or monthly:
            inf = {}

            day_range = 30 if monthly else 7

            for day in range(day_range):
                t = now - timedelta(days=day)
                log_file = os.path.join(logs_dir, t.strftime('%Y%m%d'))
                data = get_logs(log_file)

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

            print(f'{"MONTHLY" if monthly else "WEEKLY"} REPORT - {(now - timedelta(days=day_range-1)).date()} - {now.date()}\n')
        else:
            log_file = os.path.join(logs_dir, now.strftime('%Y%m%d'))
            data = get_logs(log_file)

            for process, time_info in data.items():
                total_elapsed_time = timedelta()
                for info in time_info:
                    start = datetime.fromisoformat(info['start_time'])
                    end = datetime.fromisoformat(info['end_time']) if info['end_time'] else now
                    elapsed_time = end - start
                    total_elapsed_time += elapsed_time
                
                time_inf = timedelta_to_str(total_elapsed_time)
                rows.append([process, time_inf])

            print(f'DAILY REPORT - {now.date()}\n')

        print(tabulate(rows, headers, tablefmt='simple', numalign='left'))

    def reset_handler(self, args: Namespace) -> None:
        '''
        Resets data based on target (all/config/logs).
        - Confirms action with user if not forced
        - Resets the specified components
        '''

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
            self._reset_config(verbose)
            self._reset_logs(verbose)
        elif target == 'config':
            self._reset_config(verbose)
        elif target == 'logs':
            self._reset_logs(verbose)

    def _reset_config(self, verbose: bool) -> None:
        '''
        Resets configuration to default values.
        Optionally logs the action if verbose is True.
        '''

        create_config()
        if verbose:
            logger.info('Configuration has been successfully reset to default values')

    def _reset_logs(self, verbose: bool) -> None:
        '''
        Deletes all log files in the logs directory.
        Optionally logs each deletion if verbose is True.
        '''

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

    def config_handler(self, args: Namespace) -> None:
        '''
        Handles config-related CLI subcommands ("set" and "show").
        Delegates to appropriate internal methods.
        '''

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

    def _handle_show(self) -> None:
        '''
        Handles the "show" config command:
        - Retrieves current configuration values
        - Prints them
        '''

        ip, port, limit = get_config()
        print('HOST IP ADDRESS:', ip)
        print('PORT:', port)
        print('MAXIMUM PROCESS LIMIT:', limit)