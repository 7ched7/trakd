import logging
from constants import RED, YELLOW, GREY, RED_LIGHT, BOLD, RESET 

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
