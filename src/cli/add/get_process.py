import psutil
from typing import Union, Optional, Dict, Any

def get_process(process: str) -> Optional[Dict[str, Any]]:
    target: Union[str, int] = int(process) if process.isdigit() else process

    for proc in psutil.process_iter(['name', 'pid']):
        name = proc.info.get('name')
        pid = proc.info.get('pid')

        if isinstance(target, int) and target == pid:
            return proc.info
        elif isinstance(target, str) and name and target.lower() == name.lower():
            return proc.info
        
    return None
        