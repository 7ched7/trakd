import time
from datetime import datetime, timedelta
from .get_process import get_process
from helper import save_start_time, save_end_time
import cli.add.common as common

def track_process() -> None:
    event = common.event
    queue = common.queue
    start_time = common.start_time
    process_name = common.process_name
    process_pid = common.process_pid

    save_start_time(process_name, start_time)
    save_end_time(process_name, start_time)
    
    save_interval = timedelta(minutes=5)
    next_save = start_time + save_interval

    while True:
        process_info = get_process(process_name)
        now = datetime.now()

        if process_info:
            if process_pid != None and process_pid != process_info['pid']:
                json_data = { 'command': 'update', 'status': 'running', process_info['name']: process_info['pid'] }
                queue.put(json_data)

            process_pid = process_info['pid']

            if not start_time:
                start_time = now
                save_start_time(process_name, start_time)
                save_end_time(process_name, start_time)
                next_save = start_time + save_interval
        elif not process_info and start_time:
            json_data = { 'command': 'update', 'status': 'stopped', process_name: None }
            queue.put(json_data)
            save_end_time(process_name, start_time)
            start_time = None

        if now >= next_save and start_time:
            save_end_time(process_name, start_time)
            next_save = now + save_interval
        
        if event.is_set():
            if start_time:
                save_end_time(process_name, start_time)
            break
                
        time.sleep(1)