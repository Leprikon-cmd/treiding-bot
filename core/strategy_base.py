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
        self.timeframe = self.get_timeframe()

    def get_timeframe(self):
        return mt5.TIMEFRAME_M5  # можно переопределить в конкретной стратегии

    def get_rates(self):
        return mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, 100)

    def calculate_lot(self, price, sl_points, budget, risk_percent=0.02):
        sl_distance = sl_points * price * 0.0001
        if sl_distance <= 0:
            return 0.01

        risk_rub = budget * risk_percent
        raw_lot = risk_rub / sl_distance
        raw_lot = max(0.01, raw_lot)

        account_info = mt5.account_info()
        if not account_info:
            return round(min(raw_lot, 0.5), 2)

        # Проверка: какой максимум реально доступен
        max_lot = raw_lot
        while max_lot >= 0.01:
            margin = mt5.order_calc_margin(
                mt5.TRADE_ACTION_DEAL,
                self.symbol,
                mt5.ORDER_TYPE_BUY,
                max_lot,
                price
            )
            if margin is None or margin > account_info.margin_free:
                max_lot -= 0.01
            else:
                break

        return round(max(max_lot, 0.01), 2)
    
    def check_entry_signal(self):
        pass

    def calculate_lot(self, symbol_info, entry_price: float, sl_price: float) -> float:
        """
        Рассчитывает размер позиции на основе фиксированного процента риска от текущего баланса
        и расстояния между ценой входа и стоп-лоссом с помощью утилит управления риском.
        """
        # получаем текущий баланс
        balance = mt5.account_info().balance
        # сумма риска на одну сделку
        risk_amount = balance * DEFAULT_RISK_PERCENT
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