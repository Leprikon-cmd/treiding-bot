from abc import ABC, abstractmethod
import MetaTrader5 as mt5 # игнорировать проверку типов
from utils.risk import calculate_raw_lot, adjust_lot, max_affordable_lot
from config.settings import RISK_PER_TRADE

class StrategyBase(ABC):
    def __init__(self, symbol, lot, tp=50, sl=0):
        self.symbol = symbol
        self.lot = lot
        self.tp = tp
        self.sl = sl
    
    def check_entry_signal(self):
        pass

    @abstractmethod
    def get_rates(self):
        """
        Return historical data for the strategy.
        Each strategy must implement this to fetch its own timeframe rates.
        """
        pass

    def calculate_lot(self, symbol_info, entry_price: float, sl_price: float) -> float:
        """
        Рассчитывает размер позиции на основе фиксированного процента риска от текущего баланса
        и расстояния между ценой входа и стоп-лоссом с помощью утилит управления риском.
        """
        # получаем текущий баланс
        balance = mt5.account_info().balance
        # сумма риска на одну сделку
        risk_amount = balance * RISK_PER_TRADE
        # первоначальный лот на основе суммы риска и дистанции до SL
        raw_lot = calculate_raw_lot(
            risk_amount,
            sl_price,
            entry_price,
            symbol_info.trade_contract_size,
            symbol_info.point
        )
        # корректируем согласно ограничениям брокера
        adjusted = adjust_lot(
            raw_lot,
            symbol_info.volume_step,
            symbol_info.volume_min,
            symbol_info.volume_max
        )
        # проверяем доступность лота по марже
        lot = max_affordable_lot(symbol_info.name, adjusted, entry_price)
        return lot