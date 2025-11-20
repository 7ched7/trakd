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

    def create_connection(self, return_bool: bool=False) -> None:
        '''
        Creates a connection to the server by establishing a socket connection.
        - Attempts to connect to the specified server IP and port
        - Returns True if the connection is successful and return_bool is True
        - Handles different exceptions and logs them
        '''

        try:
            if self.username is None:
                raise Exception('Please create a user or switch to an existing user to perform')
            
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(self.timeout)

            self.client_socket.connect((self.ip, self.port))
            if return_bool: return True
        except ConnectionRefusedError:
            if return_bool: return False
            logger.error('Server is down')
            sys.exit(1)
        except socket.gaierror:
            if return_bool: return False
            logger.error(f'Address-related error connecting to {self.ip}:{self.port}')
            sys.exit(1)
        except socket.error:
            if return_bool: return False
            logger.error(f'There may be a problem with the host ip address and port configuration')
            sys.exit(1)
        except Exception as e:
            if return_bool: return False
            logger.error(e)
            sys.exit(1)

    def check_if_socket_running(self, return_bool: bool=False) -> None:
        '''
        Checks if the server socket is already running by attempting to create a connection.
        - If successful, raises an exception to prevent further actions while the server is running
        - Returns True if the socket is running and return_bool is True, otherwise returns False
        - Handles different exceptions and logs them
        '''

        try:
            with socket.create_connection((self.ip, self.port), timeout=self.timeout):
                if return_bool: return True
                raise Exception('Cannot be performed while the server is running')
        except (socket.error, socket.timeout, OSError, socket.gaierror):
            if return_bool: return False
            pass
        except Exception as e:
            if return_bool: return False
            logger.error(e)
            sys.exit(1)
        except KeyboardInterrupt:
            sys.exit(1)

    def check_ip_valid(self) -> bool:
        '''
        Validates if the IP address and port can be reached and are correct.
        Returns True if the connection can be established, otherwise exits the program with an error.
        '''

        try:
            with socket.create_connection((self.ip, self.port), timeout=self.timeout):
                return True
        except ConnectionRefusedError:
            return True 
        except socket.timeout:
            logger.error(f'Connection to {self.ip}:{self.port} timed out. Please check if the server is running and reachable')
            sys.exit(1)
        except OSError as e:
            logger.error(f'Connection error to {self.ip}:{self.port}. Reason: {str(e)}')
            sys.exit(1)
        except socket.gaierror:
            logger.error(f'Invalid IP address or hostname: {self.ip}. Please verify the address')
            sys.exit(1)
        except Exception as e:
            logger.error(f'An error occurred when trying to connect to {self.ip}:{self.port}: {str(e)}')
            sys.exit(1)
        except KeyboardInterrupt:
            sys.exit(1)

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