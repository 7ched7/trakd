import psutil
from tabulate import tabulate

def ls_handler() -> None:
    headers = ['USER', 'PID', 'PROCESS']
    rows = []

    for proc in psutil.process_iter(['username', 'pid', 'name']):
        try:
            info = proc.info
            row = [info['username'], info['pid'], info['name']]
            rows.append(row)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    print(tabulate(rows, headers, tablefmt='simple', numalign='left'))
    