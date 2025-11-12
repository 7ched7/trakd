from typing import Dict, List, Optional, TypedDict, Union
from datetime import datetime

class ProfileType(TypedDict):
    username: str
    ip: str
    port: int
    limit: int
    selected: int

class LogInfo(TypedDict):
    start_time: datetime
    end_time: datetime
LogType = Dict[str, List[LogInfo]]

class CommandType(TypedDict):
    command: str

class ProcessInfo(TypedDict):
    process_name: str
    pid: int
    track_pid: int
    start_time: str
    status: str
    conn: Optional[object]
AddType = Union[CommandType, Dict[str, ProcessInfo]]

class RemoveType(TypedDict, CommandType):
    process: str

class RenameType(TypedDict, CommandType):
    process: str
    new_id: str

class StatusType(TypedDict, CommandType):
    pass

class PsType(TypedDict, CommandType):
    all: bool
    detailed: bool

class UpdateInfo(TypedDict, CommandType):
    status: str
UpdateType = Union[UpdateInfo, Dict[str, int]]