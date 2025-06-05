import os
from datetime import datetime, timedelta
from argparse import Namespace
from tabulate import tabulate
from helper import get_logs_dir, get_logs

def get_headers(weekly_or_monthly: bool) -> list[str]:
    headers = ['PROCESS', 'TOTAL RUN TIME']
    if weekly_or_monthly:
        headers.append('ACTIVE DAYS')
    return headers

def timedelta_to_str(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    
    hours = (total_seconds) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f'{hours}h {minutes}m {seconds}s'
    
def report_handler(args: Namespace) -> None:
    weekly = args.weekly
    monthly = args.monthly
    now = datetime.now()
    logs_dir = get_logs_dir()
    headers = get_headers(weekly or monthly)
    rows = []

    if weekly or monthly:
        inf = {}

        day_range = 30 if monthly else 7

        for day in range(day_range):
            t = now - timedelta(days=day)
            log_file = os.path.join(logs_dir, t.strftime('%Y%m%d'))
            data = get_logs(log_file)

            for process, time_info in data.items():
                for info in time_info:
                    start = datetime.fromisoformat(info['start_time'])
                    end = datetime.fromisoformat(info['end_time']) if info['end_time'] else now
                    elapsed_time = end - start

                    if process not in inf:
                        inf[process] = {'total_time': timedelta(), 'active_days': set()}

                    inf[process]['total_time'] += elapsed_time
                    inf[process]['active_days'].add(start.date())

        for process, info in inf.items():
            time_inf = timedelta_to_str(info['total_time'])
            active_days_count = len(info['active_days']) or 1  
            rows.append([process, time_inf, active_days_count])

        print(f'{"MONTHLY" if monthly else "WEEKLY"} REPORT - {(now - timedelta(days=day_range-1)).date()} - {now.date()}\n')
    else:
        log_file = os.path.join(logs_dir, now.strftime('%Y%m%d'))
        data = get_logs(log_file)

        for process, time_info in data.items():
            total_elapsed_time = timedelta()
            for info in time_info:
                start = datetime.fromisoformat(info['start_time'])
                end = datetime.fromisoformat(info['end_time']) if info['end_time'] else now
                elapsed_time = end - start
                total_elapsed_time += elapsed_time
            
            time_inf = timedelta_to_str(total_elapsed_time)
            rows.append([process, time_inf])

        print(f'DAILY REPORT - {now.date()}\n')

    print(tabulate(rows, headers, tablefmt='simple', numalign='left'))