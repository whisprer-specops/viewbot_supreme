### utils/logging.py ###

import os
import logging
import logging.handlers

def setup_logging(config):
    """
    Set up logging with proper configuration.
    
    Args:
        config: Configuration dictionary
    """
    log_level = config.get("log_level", logging.INFO)
    log_file = config.get("log_file", "botnet.log")
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Create file handler
    try:
        # Create log directory if needed
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Set up rotating file handler (10 MB max, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        logging.error(f"Failed to set up file logging: {e}")
        
    logging.info(f"Logging initialized at level {logging.getLevelName(log_level)}")
