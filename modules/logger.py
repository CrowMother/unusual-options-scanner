import logging

logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('logger.log')
file_handler.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)