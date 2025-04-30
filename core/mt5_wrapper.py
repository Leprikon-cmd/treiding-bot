import MetaTrader5 as mt5

def initialize_mt5():
    if not mt5.initialize():
        print(f"Ошибка инициализации: {mt5.last_error()}")
        return False
    return True

def shutdown_mt5():
    mt5.shutdown()