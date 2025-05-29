import os
import json 
from datetime import datetime, timedelta
from filelock import FileLock
from contextlib import contextmanager
from typing import Generator
from type import LogType

def get_logs_dir() -> str:
    logs_dir = os.path.expanduser('~/.trakd/logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    return logs_dir
    
def get_logs(path: str) -> LogType:
    data = {}
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return data

def write_logs(path: str, data: dict) -> None:
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

@contextmanager
def manage_lock(lock_file: str) -> Generator[None, None, None]:
    lock = FileLock(lock_file)
    with lock:
        yield

def save_start_time(process_name: str, start_time: datetime) -> int:
    logs_dir = get_logs_dir()
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

        return len(data[process_name]) - 1

def save_end_time(process_name: str, start_time: datetime, idx: int) -> None:
    now = datetime.now()
    
    logs_dir = get_logs_dir()

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
                data[process_name][idx]['end_time'] = now.isoformat()

            write_logs(log_file, data)
