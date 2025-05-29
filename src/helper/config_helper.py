import os
import sys
import json
import socket
from config import logger
from type import ConfigType

def get_config_path() -> str:
    dir = os.path.expanduser('~/.trakd')
    if not os.path.exists(dir):
        os.makedirs(dir)
    config_path = os.path.join(dir, 'config.json')
    return config_path

def check_socket_running(ip: str, port: int) -> None:
    try:
        with socket.create_connection((ip, port), timeout=3):
            raise Exception('Cannot reset while the server is running')
    except (socket.error, socket.timeout, OSError, socket.gaierror):
        pass
    except Exception as e:
        logger.error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(1)

def check_ip_valid(ip: str, port: int) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=5):
            return True
    except ConnectionRefusedError:
        return True 
    except socket.timeout:
        logger.error(f'Connection to {ip}:{port} timed out. Please check if the server is running and reachable')
        sys.exit(1)
    except OSError as e:
        logger.error(f'Connection error to {ip}:{port}. Reason: {str(e)}')
        sys.exit(1)
    except socket.gaierror:
        logger.error(f'Invalid IP address or hostname: {ip}. Please verify the address')
        sys.exit(1)
    except Exception as e:
        logger.error(f'An error occurred when trying to connect to {ip}:{port}: {str(e)}')
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(1)
        
def get_config() -> tuple[str, str, int]:
    config_path = get_config_path()
    
    data = {}
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        pass

    if not data:
        data = create_config()
    
    ip = data.get('host_ip_address')
    port = data.get('port')
    limit = max(1, min(data.get('max_process_limit'), 24))
    return ip, port, limit 

def create_config(ip: str='127.0.0.1', port: int=10101, limit: int=8) -> ConfigType:
    config_path = get_config_path()

    try:
        with open(config_path, 'w') as f:
            data = {
                'host_ip_address': ip,
                'port': port,
                'max_process_limit': limit
            }
            json.dump(data, f, indent=4)
        return data
    except Exception as e:
        logger.error(f'An error occurred: {e}')
        sys.exit(1)
