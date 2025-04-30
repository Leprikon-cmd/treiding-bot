import logging

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('logs/trading_bot.log', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

file_logger = logging.getLogger('file_logger')
file_logger.setLevel(logging.DEBUG)
file_logger.addHandler(file_handler)

console_logger = logging.getLogger('console_logger')
console_logger.setLevel(logging.INFO)
console_logger.addHandler(console_handler)
