import pandas as pd
import MetaTrader5 as mt5
from core.strategy_base import StrategyBase

class VWAPStrategy(StrategyBase):
    """
    VWAP-based scalping strategy:
      - When price deviates from VWAP by a threshold and then returns,
        generates a sell or buy signal on M5 timeframe.
      - Uses dynamic ATR-based SL/TP as configured in ATR_SETTINGS.
    """
    def __init__(self, symbol, lot, deviation_points: float = 10.0):
        super().__init__(symbol, lot)
        self.deviation_points = deviation_points
        self.ma_period = 2
        # point size for this symbol
        info = mt5.symbol_info(symbol)
        self.point = info.point if info else 0.0

    def get_timeframe(self):
        # Use 5-minute bars
        return mt5.TIMEFRAME_M5

    def get_rates(self):
        # берём таймфрейм из метода стратегии
        timeframe = self.get_timeframe()
        # запрашиваем 100 баров нужного TF
        rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, 100)
        # если не получилось или недостаточно данных — возвращаем None
        return rates if rates is not None and len(rates) >= self.ma_period + 2 else None

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # Typical price
        df['tp'] = (df['high'] + df['low'] + df['close']) / 3.0
        # Cumulative volume and volume-price
        df['cum_vol'] = df['tick_volume'].cumsum()
        df['cum_vp'] = (df['tp'] * df['tick_volume']).cumsum()
        # VWAP
        df['vwap'] = df['cum_vp'] / df['cum_vol']
        return df

    def check_entry_signal(self, rates) -> str:
        df = pd.DataFrame(rates)
        df = self._calculate_indicators(df)
        # need at least two bars to detect a return
        if len(df) < 2:
            return None

        # threshold in price units
        threshold = self.deviation_points * self.point
        prev = df.iloc[-2]
        curr = df.iloc[-1]

        # SELL: price was above VWAP + threshold and has now crossed back below it
        if prev['close'] > prev['vwap'] + threshold and curr['close'] < curr['vwap'] + threshold:
            return "sell"

        # BUY: price was below VWAP - threshold and has now crossed back above it
        if prev['close'] < prev['vwap'] - threshold and curr['close'] > curr['vwap'] - threshold:
            return "buy"

        return None

    def check_exit_signal(self, rates) -> bool:
        # rely on broker SL/TP for exits
        return False
