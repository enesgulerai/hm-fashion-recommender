import logging
import os
import sys
from datetime import datetime

# 1. Log Dosyasının Adını ve Yerini Belirle
# Örnek: logs/05_21_2024_14_30_00.log
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
LOG_FILE_PATH = os.path.join(LOG_DIR, LOG_FILE)

# 2. Log Formatı (Zaman - Seviye - Mesaj)
logging_str = "[%(asctime)s] %(levelname)s: %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=logging_str,
    handlers=[
        logging.FileHandler(LOG_FILE_PATH), # Dosyaya yaz
        logging.StreamHandler(sys.stdout)   # Konsola (Docker loglarına) yaz
    ]
)

# 3. Logger Nesnesini Oluştur
logger = logging.getLogger("HM_Fashion_Logger")