import socket
import sys
import json
from threading import Event
from logger import logger
from typing import Union, Optional

class ClientSocketManager:
    '''
    Manages the client-side socket connection
    - Establishing a connection to the server
    - Sending and receiving data
    - Validating the server IP and port
    - Handling socket-related exceptions
    '''

    def __init__(self, username: str, ip: str, port: int, timeout: int = 5):
        '''
        Initializes the ClientSocketManager with provided username, IP, and port.
        '''

        self.username = username
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.client_socket: Optional[socket.socket] = None

    def create_connection(self) -> None:
        '''
        Creates a connection to the server by establishing a socket connection.
        Handles various exceptions that may occur during the connection process.
        '''

        try:
            if self.username is None:
                raise Exception('Please create a user or switch to an existing user to perform')
            
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(self.timeout)

            self.client_socket.connect((self.ip, self.port))
        except ConnectionRefusedError:
            logger.error('Server is down')
            sys.exit(1)
        except socket.gaierror:
            logger.error(f'Address-related error connecting to {self.ip}:{self.port}')
            sys.exit(1)
        except socket.error:
            logger.error(f'There may be a problem with the host ip address and port configuration')
            sys.exit(1)
        except Exception as e:
            logger.error(e)
            sys.exit(1)

    def is_socket_running(self) -> None:
        '''
        Checks if the server is running and prevents connection while the server is active.
        This function raises an exception if the server is already running.
        '''

        try:
            with socket.create_connection((self.ip, self.port), timeout=self.timeout):
                raise Exception('Cannot be performed while the server is running')
        except (socket.error, socket.timeout, OSError, socket.gaierror):
            pass
        except Exception as e:
            logger.error(e)
            sys.exit(1)
        except KeyboardInterrupt:
            sys.exit(1)

    def is_ip_valid(self, ip: str, port: int) -> bool:
        '''
        Validates if the IP address and port can be reached and are correct.
        Returns True if the connection can be established, otherwise exits the program with an error.
        '''

        sock = None

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.bind((ip, port))
            sock.listen(1)
            return True
        except PermissionError:
            logger.error(f'Permission denied on {ip}:{port}')
            sys.exit(1)
        except OSError as e:
            logger.error(f'Failed to bind {ip}:{port}: {str(e)}')
            sys.exit(1)
        except Exception as e:
            logger.error(f'An error occurred when trying to connect to {ip}:{port}: {str(e)}')
            sys.exit(1)
        except KeyboardInterrupt:
            sys.exit(1)
        finally:
            if sock: sock.close()

    def send_data(self, data: Union[str, dict], wait_for_response: bool=True, event: Event=None) -> Optional[str]:
        '''
        Sends data to the server. Send either a string or a dictionary (which will be converted to JSON).
        Optionally waits for a response from the server.
        '''

        if isinstance(data, dict):
            data = json.dumps(data)

        try:
            if not self.client_socket:
                raise Exception('Socket not initialized, please create connection first.')
            
            self.client_socket.sendall(data.encode('utf-8'))

            if wait_for_response:
                received_data = self.client_socket.recv(4096)
                return received_data.decode('utf-8')
        except (BrokenPipeError, ConnectionResetError, socket.error):
            if event: 
                event.set()
            self.client_socket.close()
            sys.exit(1)