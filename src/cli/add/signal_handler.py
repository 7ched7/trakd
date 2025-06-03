import signal
from helper import save_end_time
import cli.add.common as common

def save_and_exit(s, f) -> None:
    start_time = common.start_time
    process_name = common.process_name

    if start_time:
        save_end_time(process_name, start_time)
        
    common.event.set()

def signal_handler() -> None:
    signal.signal(signal.SIGTERM, save_and_exit)
    signal.signal(signal.SIGINT, save_and_exit)