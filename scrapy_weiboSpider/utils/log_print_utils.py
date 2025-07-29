import json
import logging


def log_and_print(message, log_level="info", print_end="\n"):
    if log_level.lower() == "info":
        logging.info(message)
    elif log_level.lower() == "warn" or log_level.lower() == "warning":
        logging.warning(message)
    elif log_level.lower() == "debug":
        logging.debug(message)
    elif log_level.lower() == "error":
        logging.error(message)
    print(message, end=print_end)
