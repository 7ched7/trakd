import logging

RESET = '\033[0m'
BOLD = '\033[1m'
GREY = '\033[90m'
YELLOW = '\033[93m'
GREEN = "\033[32m"
RED = '\033[31m'
RED_LIGHT = '\033[91m'

class AnsiColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord):
        start_style = {
            'DEBUG': GREY,
            'INFO': GREY,
            'WARNING': YELLOW,
            'ERROR': RED,
            'CRITICAL': RED_LIGHT + BOLD,
        }.get(record.levelname, RESET)
        end_style = RESET
        return f'{start_style}{super().format(record)}{end_style}'
    
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = AnsiColorFormatter('{levelname} | {message}', style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel('INFO')
