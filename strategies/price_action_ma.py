import pandas as pd
import MetaTrader5 as mt5
from core.strategy_base import StrategyBase

class PriceActionMAStrategy(StrategyBase):
    def __init__(self, symbol, lot, ma_period=20):
        self.ma_period = ma_period
        super().__init__(symbol, lot)

    def get_rates(self):
        # берём таймфрейм из метода стратегии
        timeframe = self.get_timeframe()
        # запрашиваем 100 баров нужного TF
        rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, 100)
        # если не получилось или недостаточно данных — возвращаем None
        return rates if rates is not None and len(rates) >= self.ma_period + 2 else None

    def get_rates(self):
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, 100)
        return rates if rates is not None and len(rates) >= self.ma_period + 2 else None

    def _calculate_indicators(self, df):
        # Скользящая средняя
        df['ma'] = df['close'].rolling(window=self.ma_period).mean()

        # True Range (TR) в векторном виде
        prev_close = df['close'].shift(1)
        hl = df['high'] - df['low']
        hc = (df['high'] - prev_close).abs()
        lc = (df['low'] - prev_close).abs()
        # объединяем и берём максимум по каждой строке
        df['tr'] = pd.concat([hl, hc, lc], axis=1).max(axis=1)

        # ADX
        df['adx'] = self._calculate_adx(df)

        # (опционально) можно убрать колонку tr, если она больше не нужна:
        # df.drop(columns=['tr'], inplace=True)

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

    def _calculate_adx(self, df, period=14):
        df['high_diff'] = df['high'] - df['high'].shift(1)
        df['low_diff'] = df['low'].shift(1) - df['low']
        df['plus_dm'] = df['high_diff'].where((df['high_diff'] > df['low_diff']) & (df['high_diff'] > 0), 0)
        df['minus_dm'] = df['low_diff'].where((df['low_diff'] > df['high_diff']) & (df['low_diff'] > 0), 0)
        tr = df[['high', 'low', 'close']].copy()
        tr['hl'] = df['high'] - df['low']
        tr['hc'] = abs(df['high'] - df['close'].shift(1))
        tr['lc'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = tr[['hl', 'hc', 'lc']].max(axis=1)
        atr = df['tr'].rolling(window=period).mean()
        plus_di = 100 * (df['plus_dm'].rolling(window=period).sum() / atr)
        minus_di = 100 * (df['minus_dm'].rolling(window=period).sum() / atr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        return adx

    def check_entry_signal(self, rates):
        if len(rates) < self.ma_period + 2:
            return None

        df = pd.DataFrame(rates)
        df = self._calculate_indicators(df)

        # Фильтр: тренд должен быть достаточно сильным
        if df['adx'].iloc[-1] < 20:
            return None

        if self._is_bullish_engulfing(df) and df['close'].iloc[-1] > df['ma'].iloc[-1]:
            return "buy"
        elif self._is_bearish_engulfing(df) and df['close'].iloc[-1] < df['ma'].iloc[-1]:
            return "sell"
        return None

    def check_exit_signal(self, rates):
        if len(rates) < self.ma_period:
            return False

        df = pd.DataFrame(rates)
        df = self._calculate_indicators(df)

        close_now = df['close'].iloc[-1]
        ma_now = df['ma'].iloc[-1]
        close_prev = df['close'].iloc[-2]
        ma_prev = df['ma'].iloc[-2]

        crossed_down = close_prev > ma_prev and close_now < ma_now
        crossed_up = close_prev < ma_prev and close_now > ma_now

        if crossed_down or crossed_up:
            if not self._is_bullish_engulfing(df) and not self._is_bearish_engulfing(df):
                return True

        return False
