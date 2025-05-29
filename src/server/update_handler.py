from .common import tracked_processes, lock
from type import UpdateType

def update_handler(json_data: UpdateType) -> None:
    status = json_data['status']
    process_name = list(json_data.keys())[2] 
    pid = json_data[process_name]

    with lock:
        for process in tracked_processes.values():
            if process['process_name'] == process_name:
                process['status'] = status
                process['pid'] = pid
            