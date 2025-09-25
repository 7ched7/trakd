import socket
import threading
import sys
import json
from helper import get_config
from daemon import daemon
from logger import logger
from typing import Union, Dict
from type import AddType, ProcessInfo, RemoveType, RenameType, StopType, StatusType, PsType, UpdateType
from threading import Event, Lock

class Server:
    '''
    Server class: manages the server-side socket connections, handles
    client requests for process tracking, and maintains state for all tracked processes.
    '''

    def __init__(self):
        '''
        Initializes server attributes:
        - tracked_processes: dictionary to store currently tracked processes
        - stop_event: Event to signal server shutdown
        - lock: Lock to safely access shared resources across threads
        '''

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

        def convert_json(data: str) -> Union[AddType, RemoveType, RenameType, StopType, StatusType, PsType, UpdateType, bool]:
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
                if json_data['command'] == 'add':
                    self.add_handler(conn, json_data)
                elif json_data['command'] == 'rm':
                    self.rm_handler(conn, json_data)
                elif json_data['command'] == 'rename':
                    self.rename_handler(conn, json_data)
                elif json_data['command'] == 'stop':
                    self.stop_handler(conn, json_data)
                elif json_data['command'] == 'status':
                    self.status_handler(conn, server_socket)
                elif json_data['command'] == 'ps':
                    self.ps_handler(conn, json_data)
                elif json_data['command'] == 'update':
                    self.update_handler(json_data)
                
        conn.close()

    @daemon
    def run_server(self, verbose: str) -> None:
        '''
        Starts the server socket and listens for incoming client connections.
        - Binds to IP and port from configuration
        - Handles errors on binding (address in use, permission issues)
        - Accepts connections and starts a new thread for each client
        - Waits for all threads to finish on shutdown
        '''

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        ip, port, _ = get_config()

        try:
            server_socket.bind((ip, port))
        except OSError as e:
            if e.errno == 98:  
                logger.warning('Server is already up and running')
            elif e.errno == 13 or e.errno == 99:
                logger.error('There may be a problem with the host IP address and port configuration or lack of permissions')
            else:
                logger.error(e)
            sys.exit(1)

        server_socket.listen()
        if verbose:
            logger.info('Server is up and running')

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

        for t in threads:
            t.join()

        server_socket.close()

    def stop_handler(self, conn: socket.socket, json_data: StopType) -> None:
        '''
        Handles stop requests from clients.
        - Non-force stop fails if processes are still running
        - Force stop terminates all tracked processes
        - Sends acknowledgment to the client
        - Sets stop_event to shut down the server
        '''

        tracked_processes = self.tracked_processes
        lock = self.lock

        with lock:
            has_running = bool(tracked_processes)
        
        if json_data['flag'] == 'non-force' and has_running:
            conn.send(b'error')
        else:
            if json_data['flag'] == 'force' and has_running:
                with lock:
                    processes_copy = list(tracked_processes.values())
                    tracked_processes.clear()  
                for running_process in processes_copy:
                    process_conn: socket.socket = running_process['conn']
                    try:
                        process_conn.sendall('stop'.encode('utf-8'))
                    except OSError:
                        continue

            conn.send(b'ok')
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

        _, _, limit = get_config()
        if not len(tracked_processes) < limit:
            conn.send(b'limit')
            return
        
        id = list(json_data.keys())[1] 
        process = json_data[id]

        with lock:
            for key, value in tracked_processes.items():
                if process['process_name'].lower() == value['process_name'].lower():
                    conn.send(b'duplicate process')
                    return
                elif key.lower() == id.lower():
                    conn.send(b'duplicate id')
                    return
            
            tracked_processes[id] = process
            tracked_processes[id]['conn'] = conn

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
            else:
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
                    if key == 'track_pid':
                        continue

                    if not json_data['detailed'] and key in ('pid', 'conn'):
                        continue

                    if key == 'conn':
                        try:
                            client_host, client_port = value.getpeername()
                            data[key] = f'{client_host}/{client_port}'
                        except OSError:
                            data[key] = f'Disconnected'
                        continue
                    
                    data[key] = value

                ps_data[track_id] = data
                
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
                conn.send(b'duplicate')
                return
            if id in tracked_processes.keys():
                tracked_processes[new_id] = tracked_processes.pop(id)            
            else:
                conn.send(b'error')
                return
        
        conn.send(b'ok')

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

        with lock:
            for process in tracked_processes.values():
                if process['process_name'] == process_name:
                    process['status'] = status
                    process['pid'] = pid