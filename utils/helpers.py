#helpers.py
def check_stoplevels(symbols):
    import MetaTrader5 as mt5

    if not mt5.initialize():
        print("❌ Не удалось подключиться к MT5")
        return

    print(f"{'Символ':<12} {'StopLevel (пунктов)':<22} {'Point (размер пункта)':<22}")

    for symbol in symbols:
        info = mt5.symbol_info(symbol)
        if info is None:
            print(f"{symbol:<12} ❌ Символ не найден")
            continue

        print(f"{symbol:<12} {info.trade_stops_level:<22} {info.point:<22}")

    mt5.shutdown()