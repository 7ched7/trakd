import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger: logging.Logger = logging.getLogger(__name__)