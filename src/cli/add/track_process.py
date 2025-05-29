import time
from datetime import datetime
from .get_process import get_process
from helper import save_start_time, save_end_time
from .common import event, queue

def track_process(process_name: str, start_time: float) -> None:
    process_pid = None
    idx = save_start_time(process_name, start_time)    

    while True:
        process_info = get_process(process_name)

        if process_info:
            if process_pid != None and process_pid != process_info['pid']:
                json_data = { 'command': 'update', 'status': 'running', process_info['name']: process_info['pid'] }
                queue.put(json_data)

            process_pid = process_info['pid']

            if not start_time:
                start_time = datetime.now()
                idx = save_start_time(process_name, start_time)

        elif not process_info:
            if start_time:
                json_data = { 'command': 'update', 'status': 'stopped', process_name: None }
                queue.put(json_data)

                save_end_time(process_name, start_time, idx)
        
                start_time = None
        
        if event.is_set():
            if start_time:
                save_end_time(process_name, start_time, idx)
            break
                
        time.sleep(1)