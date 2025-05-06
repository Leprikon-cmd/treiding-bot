import pandas as pd
import MetaTrader5 as mt5
from core.strategy_base import StrategyBase

class EMARSIVolumeStrategy(StrategyBase):
    def __init__(self, symbol, lot, ema_fast=10, ema_slow=50, rsi_period=14, rsi_overbought=70, rsi_oversold=30, volume_threshold=1.5):
        super().__init__(symbol, lot)
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.volume_threshold = volume_threshold

    def get_timeframe(self):
        return mt5.TIMEFRAME_H1  # ⏱ среднесрок

    def get_rates(self):
        timeframe = self.get_timeframe()
        rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, 200)
        if rates is None or len(rates) < max(self.ema_slow, self.rsi_period, 20) + 1:
            return None
        return rates

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

        # Минимальный объем для сигнала
        if last['volume_avg'] == 0 or last['tick_volume'] == 0:
            return None

        ema_cross_up = last['ema_fast'] > last['ema_slow'] and df['ema_fast'].iloc[-2] <= df['ema_slow'].iloc[-2]
        ema_cross_down = last['ema_fast'] < last['ema_slow'] and df['ema_fast'].iloc[-2] >= df['ema_slow'].iloc[-2]
        volume_ok = last['tick_volume'] > last['volume_avg'] * self.volume_threshold
        rsi_buy_zone = last['rsi'] < self.rsi_oversold + 10
        rsi_sell_zone = last['rsi'] > self.rsi_overbought - 10

        if ema_cross_up and volume_ok and rsi_buy_zone:
            return "buy"

        if ema_cross_down and volume_ok and rsi_sell_zone:
         return "sell"

        print(f"[{self.symbol}] no signal | ema_fast: {last['ema_fast']:.5f}, ema_slow: {last['ema_slow']:.5f}, rsi: {last['rsi']:.2f}, volume: {last['tick_volume']}, avg_volume: {last['volume_avg']:.2f}")
        return None

    def check_exit_signal(self, rates):
        df = pd.DataFrame(rates)
        df = self._calculate_indicators(df)
        return abs(df['ema_fast'].iloc[-1] - df['ema_slow'].iloc[-1]) < df['close'].iloc[-1] * 0.001

    def open_trade(self, action):
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            print(f"Symbol {self.symbol} not found")
            return False

        price = mt5.symbol_info_tick(self.symbol).ask if action == "buy" else mt5.symbol_info_tick(self.symbol).bid
        deviation = 20
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": self.lot,
            "type": mt5.ORDER_TYPE_BUY if action == "buy" else mt5.ORDER_TYPE_SELL,
            "price": price,
            "deviation": deviation,
            "magic": 234000,
            "comment": "ema_cross_strategy",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ Ошибка отправки ордера: код={result.retcode}, сообщение={result.comment}")
        return result.retcode == mt5.TRADE_RETCODE_DONE