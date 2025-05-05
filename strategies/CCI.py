import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from core.strategy_base import StrategyBase

class CCIDivergenceStrategy(StrategyBase):
    def __init__(self, symbol, lot, period=14, divergence_bars=2):
        super().__init__(symbol, lot)
        self.period = period
        # number of bars to look back for divergence
        self.divergence_bars = divergence_bars

    def get_timeframe(self):
        # 5-minute timeframe for CCI divergence
        return mt5.TIMEFRAME_M5

    def get_rates(self):
        # fetch enough bars: period + divergence_bars + 1
        count = self.period + self.divergence_bars + 1
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, count)
        return rates if rates is not None and len(rates) >= count else None

    def _calculate_indicators(self, df):
        # Typical price
        df['tp'] = (df['high'] + df['low'] + df['close']) / 3.0
        # Moving average of typical price
        df['tp_ma'] = df['tp'].rolling(window=self.period).mean()
        # Mean deviation
        df['mean_dev'] = df['tp'].rolling(window=self.period).apply(
            lambda x: np.mean(np.abs(x - x.mean())), raw=True
        )
        # CCI
        df['cci'] = (df['tp'] - df['tp_ma']) / (0.015 * df['mean_dev'])
        return df

    def _is_bearish_divergence(self, df):
        # price makes higher high, CCI makes lower high over divergence_bars
        idx = -self.divergence_bars - 1
        price_prev = df['high'].iloc[idx]
        price_curr = df['high'].iloc[-1]
        cci_prev = df['cci'].iloc[idx]
        cci_curr = df['cci'].iloc[-1]
        return price_curr > price_prev and cci_curr < cci_prev

    def _is_bullish_divergence(self, df):
        # price makes lower low, CCI makes higher low over divergence_bars
        idx = -self.divergence_bars - 1
        price_prev = df['low'].iloc[idx]
        price_curr = df['low'].iloc[-1]
        cci_prev = df['cci'].iloc[idx]
        cci_curr = df['cci'].iloc[-1]
        return price_curr < price_prev and cci_curr > cci_prev

    def check_entry_signal(self, rates):
        df = pd.DataFrame(rates)
        df = self._calculate_indicators(df)
        if np.isnan(df['cci'].iloc[-1]):
            return None

        if self._is_bullish_divergence(df):
            return "buy"
        if self._is_bearish_divergence(df):
            return "sell"
        return None

    def check_exit_signal(self, rates):
        # exit when CCI crosses zero
        df = pd.DataFrame(rates)
        df = self._calculate_indicators(df)
        cci_prev = df['cci'].iloc[-2]
        cci_curr = df['cci'].iloc[-1]
        # crossing zero
        return cci_prev * cci_curr < 0