import os
import sys
import socket
import shutil
from typing import Generator
from logger import logger
from filelock import FileLock
from contextlib import contextmanager
from .save_helper import get_logs_dir
from type import ProfileType

def get_trakd_path() -> str:
    dir = os.path.expanduser('~/.trakd')
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir

def get_profile_path() -> str:
    dir = os.path.expanduser('~/.trakd')
    if not os.path.exists(dir):
        os.makedirs(dir)
    profile_path = os.path.join(dir, 'profile')
    return profile_path

def check_socket_running(ip: str, port: int) -> None:
    try:
        with socket.create_connection((ip, port), timeout=3):
            raise Exception('Cannot be performed while the server is running')
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

@contextmanager
def manage_lock(profile_file: str) -> Generator[None, None, None]:
    lock = FileLock(profile_file)
    with lock:
        yield

def get_profiles() -> list[ProfileType]:
    profile_path = get_profile_path()
    profiles = []

    lock_file = os.path.join(get_trakd_path(), 'lck.lock')

    with manage_lock(lock_file):
        try:
            with open(profile_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    u, i, p, l, s = [x.strip() for x in line.strip().split('|')]
                    profiles.append({
                        'username': u,
                        'ip': i,
                        'port': int(p),
                        'limit': int(l),
                        'selected': int(s),
                    })
        except FileNotFoundError:
            pass
        return profiles

def write_profiles(profiles: list[ProfileType]) -> None:
    profile_path = get_profile_path()
    data = '\n'.join(f"{p['username']}|{p['ip']}|{p['port']}|{p['limit']}|{p['selected']}" for p in profiles) + '\n'

    lock_file = os.path.join(get_trakd_path(), 'lck.lock')

    with manage_lock(lock_file):
        with open(profile_path, 'w') as f:
            f.write(data)

def get_current_profile() -> tuple[str, str, int, int]:
    profiles = get_profiles()

    for p in profiles:
        if p['selected']:
            limit = max(1, min(p['limit'], 24))
            return p['username'], p['ip'], p['port'], limit
        
    return None, None, None, None

def create_profile(username: str, ip='127.0.0.1', port=10101, limit=8, selected=0) -> tuple[str, str, int, int]:
    profiles = get_profiles()
    profiles.append({'username': username, 'ip': ip, 'port': port, 'limit': limit, 'selected': selected})
    write_profiles(profiles)
    get_logs_dir(username)
    return username, ip, port, limit

def remove_profile(username: str) -> bool:
    profiles = get_profiles()
        
    new_profiles = [p for p in profiles if p['username'].strip() != username.strip()]
    removed = len(new_profiles) < len(profiles)
    if removed:
        write_profiles(new_profiles)

        logs_dir = get_logs_dir(username)
        shutil.rmtree(logs_dir)
    return removed

def switch_profile(username: str) -> bool:
    profiles = get_profiles()
    switched = False
    for p in profiles:
        if p['username'].strip() == username.strip():
            p['selected'] = 1
            switched = True
        else:
            p['selected'] = 0
    if switched:
        write_profiles(profiles)
    return switched

def rename_profile(old_username: str, new_username: str) -> bool:
    profiles = get_profiles()
    renamed = False
    for p in profiles:
        if p['username'].strip() == old_username.strip():
            p['username'] = new_username
            renamed = True
    if renamed:
        write_profiles(profiles)

        logs_dir = get_logs_dir(old_username)
        os.rename(logs_dir, os.path.expanduser(f'~/.trakd/logs/{new_username}'))
    return renamed

def update_profile(username: str, ip='127.0.0.1', port=10101, limit=8) -> bool:
    profiles = get_profiles()
    updated = False
    for p in profiles:
        if p['username'].strip() == username.strip():
            p['ip'], p['port'], p['limit'] = ip, port, limit
            updated = True
    if updated:
        write_profiles(profiles)
    return updated