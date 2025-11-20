import socket
import threading
import sys
import json
import signal
import time
from manager import ProfileManager
from logger import logger
from typing import Union, Dict
from type import AddType, ProcessInfo, RemoveType, RenameType, ReportType, StatusType, PsType, UpdateType
from threading import Event, Lock

class Server:
    '''
    Manages the server-side socket connections, handles
    client requests for process tracking, and maintains state for all tracked processes.
    '''

    def __init__(self):
        '''
        Initializes server attributes:
        - profile_manager: Manages user profiles
        - tracked_processes: Dictionary to store currently tracked processes
        - stop_event: Event to signal server shutdown
        - lock: Lock to safely access shared resources across threads
        '''

        self.profile_manager = ProfileManager()
        self.tracked_processes: Dict[str, ProcessInfo] = {}
        self.stop_event: Event = Event()
        self.lock: Lock = Lock()
    
    def _handle_client(self, conn: socket.socket, addr: tuple[str, int], server_socket: socket) -> None:
        '''
        Handles communication with a connected client.
        - Receives data from client
        - Parses JSON commands
        - Delegates commands to the appropriate handler (add, rm, rename, stop, status, ps, update)
        - Closes connection when client disconnects or stop_event is set
        '''

        def convert_json(data: str) -> Union[AddType, RemoveType, RenameType, ReportType, StatusType, PsType, UpdateType, bool]:
            try:
                json_data = json.loads(data)
                return json_data
            except json.JSONDecodeError:
                return False

        while not self.stop_event.is_set(): 
            try:
                data = conn.recv(4096)
            except (ConnectionResetError, OSError):
                break

            if not data:
                break
            
            data = data.decode('utf-8')
            json_data = convert_json(data)
            
            if json_data:
                match json_data['command']:
                    case 'add':
                        self.add_handler(conn, json_data)
                    case 'rm':
                        self.rm_handler(conn, json_data)
                    case 'rename':
                        self.rename_handler(conn, json_data)
                    case 'report':
                        self.report_handler(conn)
                    case 'stop':
                        self._graceful_shutdown()
                    case 'status':
                        self.status_handler(conn, server_socket)
                    case 'ps':
                        self.ps_handler(conn, json_data)
                    case 'update':
                        self.update_handler(json_data)
                    case _:
                        pass
                
        conn.close()

    def run_server(self, is_service: bool=False) -> None:
        '''
        Starts the server socket and listens for incoming client connections.
        - Binds to IP and port from configuration
        - Handles errors on binding (address in use, permission issues)
        - Accepts connections and starts a new thread for each client
        - Waits for all threads to finish on shutdown
        '''

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        username, ip, port, _ = self.profile_manager.get_current_profile()

        try:
            if username is None:
                raise Exception('Please create a user or switch to an existing user to start the server')
        except Exception as e:
            logger.error(e)
            sys.exit(1)

        if not is_service: 
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)

        try:
            server_socket.bind((ip, port))
        except OSError as e:
            if e.errno == 98 or 10048:  
                logger.warning('Server is already up and running')
            elif e.errno == 13 or e.errno == 99:
                logger.error('There may be a problem with the host IP address and port configuration or lack of permissions')
            else:
                logger.error(e)
            sys.exit(1)

        server_socket.listen()
        logger.debug('Server is up and running')

        threads = []

        while not self.stop_event.is_set(): 
            try:
                server_socket.settimeout(1)
                conn, addr = server_socket.accept()

                t = threading.Thread(target=self._handle_client, args=(conn, addr, server_socket))
                t.start()
                threads.append(t)
            except socket.timeout:
                continue 
            except KeyboardInterrupt:
                self._graceful_shutdown()

        for t in threads:
            t.join()

        server_socket.close()

    def _signal_handler(self, sig, frame):
        '''
        Handles SIGTERM/SIGINT signal to ensure proper shutdown.
        - Calls the graceful shutdown method to stop the server
        - Exits the program with a success status
        '''

        self._graceful_shutdown()
        sys.exit(0)

    def _graceful_shutdown(self) -> None:
        '''
        Manages the shutdown process:
        - Attempts to stop any running tracked processes by sending a 'stop' signal
        - If processes are still running, sends a stop signal to each process
        - Sets the stop_event to trigger the server shutdown 
        '''

        tracked_processes = self.tracked_processes
        lock = self.lock

        with lock:
            has_running = bool(tracked_processes)
        
        if has_running:
            with lock:
                processes_copy = list(tracked_processes.values())
                tracked_processes.clear()  
            for running_process in processes_copy:
                process_conn: socket.socket = running_process['conn']
                try:
                    process_conn.sendall('stop'.encode('utf-8'))
                except OSError:
                    continue
        
        logger.debug('Stopping the server')
        self.stop_event.set()
    
    def status_handler(self, conn: socket.socket, server_socket: socket.socket):
        '''
        Sends server status to the client.
        - Includes IP, port, number of tracked processes
        - Counts running and stopped processes
        '''

        tracked_processes = self.tracked_processes
        lock = self.lock

        ip, port = server_socket.getsockname()

        with lock:
            status_data = {
                'ip': ip,
                'port': port,
                'tracked_processes': len(tracked_processes),
                'running': 0,
                'stopped': 0
            }

            for process_info in tracked_processes.values():
                status = process_info.get('status')
                if status == 'running':
                    status_data['running'] += 1
                else:
                    status_data['stopped'] += 1

        logger.debug(f'Sent server status to client {conn.getpeername()} | Status: {status_data}')
        conn.send(json.dumps(status_data).encode('utf-8'))

    def add_handler(self, conn: socket.socket, json_data: AddType) -> None:
        '''
        Adds a new process to the tracked_processes dictionary.
        - Checks maximum tracking limit
        - Checks for duplicate process names or IDs
        - Stores connection socket for future communication
        - Sends acknowledgment or error to client
        '''

        tracked_processes = self.tracked_processes
        lock = self.lock

        _, _, _, limit = self.profile_manager.get_current_profile()
        if not len(tracked_processes) < limit:
            logger.debug(f'Client {conn.getpeername()} attempted to add a process but reached limit')
            conn.send(b'limit')
            return
        
        id = list(json_data.keys())[1] 
        process = json_data[id]

        with lock:
            for key, value in tracked_processes.items():
                if process['process_name'].lower() == value['process_name'].lower():
                    logger.debug(f'Duplicate process name attempt by client {conn.getpeername()}: {process['process_name']}')
                    conn.send(b'duplicate process')
                    return
                elif key.lower() == id.lower():
                    logger.debug(f'Duplicate ID attempt by client {conn.getpeername()}: {id}')
                    conn.send(b'duplicate id')
                    return
            
            tracked_processes[id] = process
            tracked_processes[id]['conn'] = conn

        logger.debug(f'Process added by client {conn.getpeername()} | Process ID: {id}')
        conn.send(b'ok')

    def rm_handler(self, conn: socket.socket, json_data: RemoveType) -> None:
        '''
        Removes a process from tracking.
        - Sends stop signal to the process' client
        - Deletes process from tracked_processes
        - Sends acknowledgment or error to client
        '''

        tracked_processes = self.tracked_processes
        lock = self.lock

        with lock:
            if json_data['process'] in tracked_processes.keys():
                untracked_process = tracked_processes[json_data['process']]
                process_conn: socket.socket = untracked_process['conn']
                del tracked_processes[json_data['process']]
                logger.debug(f'Process {json_data['process']} removed by client {conn.getpeername()}')
            else:
                logger.warning(f'Client {conn.getpeername()} attempted to remove a non-existent process')
                conn.send(b'error')
                return
        try:
            process_conn.sendall('stop'.encode('utf-8'))
        except OSError:
            pass
        
        conn.send(b'ok')

    def ps_handler(self, conn: socket.socket, json_data: PsType) -> None:
        '''
        Sends a list of tracked processes to the client.
        - Supports filters: all vs running only, detailed vs summary view
        - Excludes certain internal fields if not requested
        - Handles disconnected clients gracefully
        '''

        tracked_processes = self.tracked_processes
        lock = self.lock

        ps_data = {}

        with lock:
            for track_id, process_info in tracked_processes.items():
                if not json_data['all'] and process_info.get('status') == 'stopped':
                    continue

                data = {}
                for key, value in process_info.items():
                    if key == 'track_pid' or key == 'session_time':
                        continue

                    if not json_data['detailed'] and key in ('pid', 'conn'):
                        continue

                    if key == 'runtime' and process_info['session_time'] is not None:
                        data[key] = process_info['runtime'] + time.time() - process_info['session_time']
                        continue

                    if key == 'conn':
                        try:
                            client_host, client_port = value.getpeername()
                            data[key] = f'{client_host}/{client_port}'
                        except OSError:
                            data[key] = f'Disconnected'
                            data['pid'] = '--'
                            data['runtime'] = '--'
                            data['status'] = '--'
                        continue
                    
                    data[key] = value

                ps_data[track_id] = data
        
        logger.debug(f'Sent process status list to client {conn.getpeername()} | Data: {ps_data}')
        conn.sendall(json.dumps(ps_data).encode('utf-8'))

    def rename_handler(self, conn: socket.socket, json_data: RenameType) -> None:
        '''
        Renames the tracking ID of a process.
        - Checks for duplicate new ID
        - Updates tracked_processes dictionary
        - Sends acknowledgment or error to client
        '''

        tracked_processes = self.tracked_processes
        lock = self.lock

        id = json_data.get('process')
        new_id = json_data.get('new_id')

        with lock:
            if new_id in tracked_processes.keys():
                logger.debug(f'Client {conn.getpeername()} attempted to rename process but new ID {new_id} is already in use')
                conn.send(b'duplicate')
                return
            if id in tracked_processes.keys():
                tracked_processes[new_id] = tracked_processes.pop(id)            
                logger.debug(f'Process {id} renamed to {new_id} by client {conn.getpeername()}')
            else:
                logger.warning(f'Client {conn.getpeername()} attempted to rename a non-existent process: {id}')
                conn.send(b'error')
                return
        
        conn.send(b'ok')

    def report_handler(self, conn: socket.socket) -> None:
        '''
        Handles the generation of a report containing the list of active processes.
        - Check the status of each tracked process 
        - Sends the names to the client
        '''
        
        tracked_processes = self.tracked_processes
        lock = self.lock

        data = {'active_processes': []}

        with lock:
            for process_info in tracked_processes.values():
                if process_info['status'] == 'running':
                    try:
                        process_info['conn'].getpeername()
                    except OSError:
                        continue

                    data['active_processes'].append(process_info['process_name'])

        logger.debug(f'Generated report for active processes: {data['active_processes']}')
        conn.sendall(json.dumps(data).encode('utf-8'))

    def update_handler(self, json_data: UpdateType) -> None:
        '''
        Updates the status and PID of a tracked process.
        - Finds the process by name
        - Updates its 'status' and 'pid' fields in tracked_processes
        '''

        tracked_processes = self.tracked_processes
        lock = self.lock

        status = json_data['status']
        process_name = list(json_data.keys())[2] 
        pid = json_data[process_name]
        session_time = json_data['session_time']

        with lock:
            for process in tracked_processes.values():
                if process['process_name'] == process_name:
                    process['status'] = status
                    process['pid'] = pid

                    if session_time is None and process['session_time'] is not None: 
                        process['runtime'] += time.time() - process['session_time']
                    process['session_time'] = session_time

                    logger.debug(f'Updated process {process_name} | Status: {status}, PID: {pid}, Session Time: {session_time}')
                    return
            logger.warning(f'Client attempted to update non-existent process: {process_name}')