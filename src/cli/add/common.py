from threading import Event
from queue import Queue
import datetime
import socket

client_socket: socket.socket = None
event: Event = Event()
queue = Queue()
start_time: datetime = None
process_name: str = None
process_pid: int = None