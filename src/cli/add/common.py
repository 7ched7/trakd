from threading import Event
from queue import Queue

event: Event = Event()
queue = Queue()