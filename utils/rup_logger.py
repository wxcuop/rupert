import logging
from datetime import datetime
import threading

# Define logging levels
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "NOTE": logging.INFO,  # No direct equivalent, using INFO
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
    "FATAL": logging.CRITICAL,
}

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("JisuLogger")

# Set default log level
logger.setLevel(LOG_LEVELS["NOTE"])  # Default to NOTE level

def set_log_level(level: str):
    """Set the logging level."""
    logger.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))

def log(level: str, message: str):
    """General logging function."""
    level = level.upper()
    if level in LOG_LEVELS:
        logger.log(LOG_LEVELS[level], message)

def log_debug(msg):
    logger.debug(f"{threading.current_thread().name}: {msg}")

def log_info(msg):
    logger.info(f"{threading.current_thread().name}: {msg}")

def log_warn(msg):
    logger.warning(f"{threading.current_thread().name}: {msg}")

def log_error(msg):
    logger.error(f"{threading.current_thread().name}: {msg}")

def log_fatal(msg):
    logger.critical(f"{threading.current_thread().name}: {msg}")

def log_exception(e):
    logger.error(f"Exception: {e}", exc_info=True)

# Example Usage
if __name__ == "__main__":
    set_log_level("DEBUG")
    log_debug("This is a debug message")
    log_info("This is an info message")
    log_warn("This is a warning message")
    log_error("This is an error message")
    log_fatal("This is a fatal message")
    try:
        1 / 0
    except Exception as e:
        log_exception(e)
