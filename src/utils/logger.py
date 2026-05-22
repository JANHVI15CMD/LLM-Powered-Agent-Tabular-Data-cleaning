# Updated src/utils/logger.py
import logging
import logging.config  # Explicit import for config submodule
import yaml
from pathlib import Path

def setup_logger():
    config_path = Path("config/logging.yaml")
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
    else:
        # Fallback if config file missing
        logging.basicConfig(level=logging.INFO)
    return logging.getLogger('app')