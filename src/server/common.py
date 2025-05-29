from threading import Event, Lock
from typing import Dict
from type import ProcessInfo

tracked_processes: Dict[str, ProcessInfo] = {}
stop_event: Event = Event()
lock: Lock = Lock()