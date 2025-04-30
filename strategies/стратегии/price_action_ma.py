import pandas as pd
import MetaTrader5 as mt5
from core.strategy_base import StrategyBase

class PriceActionMAStrategy(StrategyBase):
    def __init__(self, symbol, timeframe, lot, ma_period=20):
        super().__init__(symbol, timeframe, lot)
        self.ma_period = ma_period

    def get_rates(self):
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, 100)
        return rates if rates is not None and len(rates) >= self.ma_period + 2 else None
    
    def _calculate_indicators(self, df):
        df['ma'] = df['close'].rolling(window=self.ma_period).mean()
        return df

    def _is_bullish_engulfing(self, df):
        return (
            df['close'].iloc[-2] < df['open'].iloc[-2] and
            df['close'].iloc[-1] > df['open'].iloc[-1] and
            df['open'].iloc[-1] <= df['close'].iloc[-2] and
            df['close'].iloc[-1] >= df['open'].iloc[-2]
        )

    def _is_bearish_engulfing(self, df):
        return (
            df['close'].iloc[-2] > df['open'].iloc[-2] and
            df['close'].iloc[-1] < df['open'].iloc[-1] and
            df['open'].iloc[-1] >= df['close'].iloc[-2] and
            df['close'].iloc[-1] <= df['open'].iloc[-2]
        )

    def check_entry_signal(self, rates):
        if len(rates) < self.ma_period + 2:
            return None

        df = pd.DataFrame(rates)
        df = self._calculate_indicators(df)

        if self._is_bullish_engulfing(df) and df['close'].iloc[-1] > df['ma'].iloc[-1]:
            return "buy"
        elif self._is_bearish_engulfing(df) and df['close'].iloc[-1] < df['ma'].iloc[-1]:
            return "sell"
        return None

    def check_exit_signal(self, rates):
        if len(rates) < self.ma_period + 2:
            return False

        df = pd.DataFrame(rates)
        df = self._calculate_indicators(df)

        # Последняя свеча пересекает MA в обратную сторону
        close_now = df['close'].iloc[-1]
        ma_now = df['ma'].iloc[-1]
        close_prev = df['close'].iloc[-2]
        ma_prev = df['ma'].iloc[-2]

        crossed_down = close_prev > ma_prev and close_now < ma_now
        crossed_up = close_prev < ma_prev and close_now > ma_now

        if crossed_down or crossed_up:
            # и нет нового сигнала в ту же сторону
            if not self._is_bullish_engulfing(df) and not self._is_bearish_engulfing(df):
                return True

        return False