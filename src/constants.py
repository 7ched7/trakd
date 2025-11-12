import os
import sys

DEFAULT_IP_ADDRESS = '127.0.0.1'
DEFAULT_PORT = 8000
DEFAULT_LIMIT = 8

is_windows = sys.platform.startswith('win')
is_frozen = getattr(sys, 'frozen', False)

TRAKD_DIR = os.path.join(os.environ['ProgramData'], 'Trakd') if is_windows else os.path.expanduser('~/.trakd')

RED = '\033[31m'
YELLOW = '\033[93m'
GREEN = '\033[32m'
GREY = '\033[90m'
RED_LIGHT = '\033[91m'
BOLD = '\033[1m'
RESET = '\033[0m'