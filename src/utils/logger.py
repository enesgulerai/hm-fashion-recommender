import logging
import os
import sys
from datetime import datetime

# 1. Specify the name and location of the log file.
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
LOG_FILE_PATH = os.path.join(LOG_DIR, LOG_FILE)

# 2. Log Format (Time - Level - Message)
logging_str = "[%(asctime)s] %(levelname)s: %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=logging_str,
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler(sys.stdout)
    ]
)

# 3. Create a Logger Object
logger = logging.getLogger("HM_Fashion_Logger")