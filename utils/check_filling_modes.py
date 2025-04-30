import MetaTrader5 as mt5
from config.settings import SYMBOLS

if not mt5.initialize():
    print("Ошибка инициализации MT5:", mt5.last_error())
    quit()

for symbol in SYMBOLS:
    info = mt5.symbol_info(symbol)
    if info is None:
        print(f"[{symbol}] ❌ Не удалось получить информацию о символе.")
        continue

    print(f"[{symbol}]")
    print(f"  ➤ filling_mode: {info.filling_mode}")
    print()

mt5.shutdown()