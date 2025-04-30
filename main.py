from config.settings import SYMBOLS, LOT
from core.mt5_wrapper import initialize_mt5, shutdown_mt5
from strategies.ema_cross import EMARSIVolumeStrategy
from strategies.price_action_ma import PriceActionMAStrategy
from core.trader import Trader
import time

print("\U0001F680 Запуск трейдинг-бота...")

# ⚙️ Подключение к MetaTrader 5
if not initialize_mt5():
    print("\u274C Ошибка подключения к MetaTrader 5. Завершение.")
    exit()

print("\u2705 Успешное подключение к MetaTrader 5.")

# 📈 Выбор активных стратегий
active_strategies = [
     EMARSIVolumeStrategy,
     PriceActionMAStrategy,
]

# 📈 Инициализация стратегий и трейдеров
strategies = []
for StrategyClass in active_strategies:
    for symbol in SYMBOLS:
        strategy = StrategyClass(symbol, LOT)
        strategies.append(strategy)

# 🔥 Правильное создание трейдеров
traders = [Trader(strategy.symbol, strategy) for strategy in strategies]

# 🔁 Основной цикл обработки
try:
    while True:
        print(f"\n\U0001F501 Новый цикл обработки: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        for trader in traders:
            trader.run()
        time.sleep(10)
except KeyboardInterrupt:
    print("\n\U0001F6D1 Остановка по запросу пользователя.")
finally:
    shutdown_mt5()
    print("\U0001F4F4 MetaTrader 5 отключён. Бот завершил работу.")
