import logging
import os
from logging.handlers import RotatingFileHandler

# Убедимся, что папка для логов существует
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "trading_bot.log")

# Формат сообщений
formatter = logging.Formatter("%(asctime)s - %(levelname)-8s - %(message)s")

# Файловый хендлер с ротацией
file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8"
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Консольный хендлер
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Единый логгер для файла и консоли
file_logger = logging.getLogger("file_logger")
file_logger.setLevel(logging.INFO)
file_logger.addHandler(file_handler)
file_logger.addHandler(console_handler)