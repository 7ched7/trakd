import os
from datetime import datetime, timedelta
from filelock import FileLock
from contextlib import contextmanager
from typing import Generator
from constants import LOGS_DIR_PATH

class LogManager:
    '''
    Handles logging functionalities for tracking process 
    start and end times. Manages logs directory, file lock, and provides methods 
    to save and retrieve logs for specific processes.
    '''

    def __init__(self, username: str):
        '''
        Initializes LogManager attributes:
        - Sets up the logs directory for the user
        - Creates a lock file for synchronizing access to logs
        - Creates the directory if it doesn't exist
        '''

        self.username = username
        self.logs_dir = os.path.expanduser(f'{LOGS_DIR_PATH}/{self.username}')
        self.lock_file = os.path.join(self.logs_dir, 'lck.lock')
        
        if username is not None and not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
    
    @contextmanager
    def _manage_lock(self) -> Generator[None, None, None]:
        '''
        Context manager for handling file locks.
        - Ensures that only one process can access and modify log data at a time
        '''

        lock = FileLock(self.lock_file)
        with lock:
            yield

    def _write_logs(self, path: str, data: dict) -> None:
        '''
        Writes the log data to a specified file.
        - Converts the dictionary data to a string format and writes to the file
        '''

        log = ''
        for key in data:
            log += '\n'.join(f'{key}|{t['start_time']}|{t['end_time']}' for t in data[key]) + '\n'

        with open(path, 'w') as f:
            f.write(log)

    def get_logs(self, path: str) -> dict:
        '''
        Retrieves log data from a file and returns it as a dictionary.
        - Parses the file to extract process start and end times
        - Returns a dictionary where the key is the process name and the value is a list of time intervals
        '''

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
        except:
            pass
        return data

    def save_start_time(self, process_name: str, start_time: datetime) -> None:
        '''
        Saves the start time of a process in the log.
        - Writes the start time of the process to the log file corresponding to the current date
        '''

        log_file = os.path.join(self.logs_dir, start_time.strftime('%Y%m%d'))

        inf = { 
            'start_time': start_time.isoformat(),
            'end_time': None
        }

        with self._manage_lock():
            data = self.get_logs(log_file)

            if process_name in data:
                data[process_name].append(inf)
            else:
                data[process_name] = [inf]

            self._write_logs(log_file, data)

    def save_end_time(self, process_name: str, start_time: datetime) -> None:
        '''
        Saves the end time of a process in the log.
        - Updates the log file for the current day with the process's end time
        - If the process spans multiple days, updates each day's log file accordingly
        '''
        
        now = datetime.now()
        log_file = os.path.join(self.logs_dir, now.strftime('%Y%m%d'))

        with self._manage_lock():
            if start_time.date() != now.date():
                elapsed_day = (now - start_time).days

                for day in range(elapsed_day + 1):
                    t = now - timedelta(days=day)
                    daily_log_file = os.path.join(self.logs_dir, t.strftime('%Y%m%d'))

                    daily_data = self.get_logs(daily_log_file)

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

                    self._write_logs(daily_log_file, daily_data)
            else:
                data = self.get_logs(log_file)

                if process_name in data:
                    data[process_name][-1]['end_time'] = now.isoformat()

                self._write_logs(log_file, data)