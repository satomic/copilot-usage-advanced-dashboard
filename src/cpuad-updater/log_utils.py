import os
import logging
from datetime import datetime


def current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]


"""
Log utilities
"""
log_format = '%(asctime)s - [%(levelname)s] - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)


def configure_logger(log_path="logs", with_date_folder=True):

    if with_date_folder:
        log_path = os.path.join(log_path, current_time()[:10])


    # Get whether to enable debug
    debug = True

    if not os.path.exists(log_path):
        os.makedirs(log_path)

    log_file_name = f"{log_path}/{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_file_name, mode='a')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO if not debug else logging.DEBUG)
    # logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    return logger


if __name__ == '__main__':
    logger = configure_logger()
    logger.info("test")
    logger.debug("test")
    logger.warning("test")
    logger.error("test")