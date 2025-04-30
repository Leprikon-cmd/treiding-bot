import pandas as pd
from core.strategy_base import StrategyBase

class EMARSIVolumeStrategy(StrategyBase):
    def __init__(self, symbol, timeframe, lot, ema_fast=10, ema_slow=50, rsi_period=14, rsi_overbought=70, rsi_oversold=30, volume_threshold=1.5):
        super().__init__(symbol, timeframe, lot)
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.volume_threshold = volume_threshold

    def _calculate_indicators(self, df):
        df['ema_fast'] = df['close'].ewm(span=self.ema_fast, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.ema_slow, adjust=False).mean()
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)
        df['volume_avg'] = df['tick_volume'].rolling(window=20).mean()
        return df

    def _calculate_rsi(self, series, period):
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def check_entry_signal(self, rates):
        df = pd.DataFrame(rates)
        if len(df) < max(self.ema_slow, self.rsi_period, 20):
            return None

        df = self._calculate_indicators(df)

        last = df.iloc[-1]
        if (last['ema_fast'] > last['ema_slow'] and
            last['rsi'] < self.rsi_oversold and
            last['tick_volume'] > last['volume_avg'] * self.volume_threshold):
            return "buy"

        elif (last['ema_fast'] < last['ema_slow'] and
              last['rsi'] > self.rsi_overbought and
              last['tick_volume'] > last['volume_avg'] * self.volume_threshold):
            return "sell"

        return None

    def check_exit_signal(self, rates):
        df = pd.DataFrame(rates)
        df = self._calculate_indicators(df)
        return abs(df['ema_fast'].iloc[-1] - df['ema_slow'].iloc[-1]) < df['close'].iloc[-1] * 0.001
