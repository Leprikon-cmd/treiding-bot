
from core.mt5_broker import Mt5Broker
from core.trader import Trader
from core.strategy_manager import get_strategy

def main():
    symbol = "EURUSD"
    timeframe = "M5"
    strategy_name = "ema_cross"

    broker = Mt5Broker()
    strategy = get_strategy(strategy_name)
    trader = Trader(symbol=symbol, strategy=strategy, broker=broker)

    # Пример: загрузка истории и попытка входа
    rates = broker.copy_rates(symbol, getattr(broker, "TIMEFRAME_" + timeframe), 0, 100)
    trader._try_open_order(rates)

    broker.shutdown()

if __name__ == "__main__":
    main()
