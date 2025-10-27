import os
from datetime import datetime, timedelta
from filelock import FileLock
from contextlib import contextmanager
from typing import Generator
from type import LogType

def get_logs_dir(username: str) -> str:
    logs_dir = os.path.expanduser(f'~/.trakd/logs/{username}')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    return logs_dir
    
def get_logs(path: str) -> LogType:
    data = {}
    try:
        with open(path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                p, s, e = [x.strip() for x in line.strip().split('|')]

                if p not in data: 
                    data[p] = []

                data[p].append({
                    'start_time': s,
                    'end_time': e
                })
    except (FileNotFoundError, IOError):
        pass
    return data

def write_logs(path: str, data: dict) -> None:
    log = ''
    
    for key in data:
        log+='\n'.join(f"{key}|{t['start_time']}|{t['end_time']}" for t in data[key]) + '\n'
    
    with open(path, 'w') as f:
        f.write(log)

@contextmanager
def manage_lock(lock_file: str) -> Generator[None, None, None]:
    lock = FileLock(lock_file)
    with lock:
        yield

def save_start_time(username: str, process_name: str, start_time: datetime) -> int:
    logs_dir = get_logs_dir(username)
    log_file = os.path.join(logs_dir, start_time.strftime('%Y%m%d'))

    inf = { 
        'start_time': start_time.isoformat(),
        'end_time': None
    }

    lock_file = os.path.join(logs_dir, 'lck.lock')

    with manage_lock(lock_file):
        data = get_logs(log_file)

        if process_name in data:
            data[process_name].append(inf)
        else:
            data[process_name] = [inf]

        write_logs(log_file, data)

def save_end_time(username: str, process_name: str, start_time: datetime) -> None:
    now = datetime.now()
    
    logs_dir = get_logs_dir(username)

    lock_file = os.path.join(logs_dir, 'lck.lock')

    with manage_lock(lock_file):
        if start_time.date() != now.date():
            elapsed_day = (now - start_time).days
            
            for day in range(elapsed_day+1):
                t = now - timedelta(days=day)
                daily_log_file = os.path.join(logs_dir, t.strftime('%Y%m%d'))

                daily_data = get_logs(daily_log_file)

                if t.date() == now.date():
                    inf = {
                        'start_time': now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
                        'end_time': now.isoformat()
                    }
                    daily_data[process_name] = [inf]
                elif t.date() == start_time.date():
                    daily_data[process_name][-1]['end_time'] = t.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
                else:
                    inf = {
                        'start_time': t.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
                        'end_time': t.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
                    }
                    daily_data[process_name] = [inf]
                    
                write_logs(daily_log_file, daily_data)
        else:
            log_file = os.path.join(logs_dir, now.strftime('%Y%m%d'))
            data = get_logs(log_file)

            if process_name in data:
                data[process_name][-1]['end_time'] = now.isoformat()

            write_logs(log_file, data)
