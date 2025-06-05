import argparse
from __version__ import __version__

def len_check(s: str) -> str:
    min_length = 3
    max_length = 24
    if len(s) >= min_length and len(s) <= max_length:
        return s
    raise argparse.ArgumentTypeError(f'tag length must be between {min_length} and {max_length}')

def create_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='trakd',
        description='Keep track of process runtime',
    )
    parser.add_argument('-v', '--version', action='version', version=f'v{__version__}')

    subparsers = parser.add_subparsers(dest='command', required=True)

    config_parser = subparsers.add_parser('config', help='manage configuration')
    config_subparsers = config_parser.add_subparsers(dest='subcommand', required=True)

    config_set_parser = config_subparsers.add_parser('set', help='set configuration')
    config_set_parser.add_argument('-i', '--ip', help='set host ip address')
    config_set_parser.add_argument('-p', '--port', type=int, help='set port number')
    config_set_parser.add_argument('-l', '--limit_max_process', type=int, help='set the maximum number of concurrently tracked processes')
    config_set_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')
    config_show_parser = config_subparsers.add_parser('show', help='show current configuration')
    
    start_parser = subparsers.add_parser('start', help='start server')
    start_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')

    stop_parser = subparsers.add_parser('stop', help='stop server')
    stop_parser.add_argument('-f', '--force', action='store_true', help='force stop')
    stop_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')

    status_parser = subparsers.add_parser('status', help='show the status of the server')

    add_parser = subparsers.add_parser('add', help='start tracking a process')
    add_parser.add_argument('process', help='process name or pid to track')
    add_parser.add_argument('-n', '--name', type=len_check, help='add tag')
    add_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')

    rm_parser = subparsers.add_parser('rm', help='stop tracking a process')
    rm_parser.add_argument('id', help='id of the tracked process to stop')
    rm_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')

    rename_parser = subparsers.add_parser('rename', help='rename tracking id of a process')
    rename_parser.add_argument('id', help='current tracking id')
    rename_parser.add_argument('new_id', type=len_check, help='new tracking id')
    rename_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')

    ps_parser = subparsers.add_parser('ps', help='show status of tracked processes')
    ps_parser.add_argument('-a', '--all', action='store_true', help='show both currently tracked and stopped processes')
    ps_parser.add_argument('-d', '--detailed', action='store_true', help='show detailed information about tracked processes')
    
    ls_parser = subparsers.add_parser('ls', help='list all processes')

    report_parser = subparsers.add_parser('report', help='show report')
    report_parser.add_argument('--daily', default=True, action='store_true', help='show daily report')
    report_parser.add_argument('--weekly', action='store_true', help='show weekly report')

    reset_parser = subparsers.add_parser('reset', help='reset program')
    reset_parser.add_argument('target', choices=['all', 'config', 'logs'], help='what to reset')
    reset_parser.add_argument('-y', '--yes', action='store_true', help='skip confirmation')
    reset_parser.add_argument('-v', '--verbose', action='store_true', help='show what is being done')

    args = parser.parse_args()

    return args