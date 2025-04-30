# Обновлённый Trader с фильтрацией символов и аккуратным логированием отказов

from utils.logger import file_logger, console_logger
import MetaTrader5 as mt5
from core.mt5_interface import send_order, close_order
from config.settings import MIN_STOP_POINTS, STRATEGY_ALLOCATION
import os
import csv
from datetime import datetime

STRATEGY_ICONS = {
    "EMARSIVolumeStrategy": "🕰️",
    "PriceActionMAStrategy": "⚡"
}

def log_cycle_header():
    print(f"\n🔁 Новый цикл обработки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

class Trader:
    def __init__(self, symbol, strategy):
        self.symbol = symbol
        self.strategy = strategy
        self.strategy_name = self.strategy.__class__.__name__
        self.tp = MIN_STOP_POINTS.get(symbol, 20)
        self.sl = MIN_STOP_POINTS.get(symbol, 20)
        self.log_path = f"logs/{self.strategy_name}_{self.symbol}.csv"
        self._prepare_log()

    def _prepare_log(self):
        os.makedirs("logs", exist_ok=True)
        if not os.path.isfile(self.log_path):
            with open(self.log_path, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "action", "symbol", "price", "lot", "result"])

    def _log_trade(self, action, price, lot, result):
        with open(self.log_path, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([datetime.now().isoformat(), action, self.symbol, price, lot, result])

    def run(self):
        emoji = STRATEGY_ICONS.get(self.strategy_name, "📈")

        rates = self.strategy.get_rates()
        if rates is None:
            print(f"{emoji} {self.symbol} — ⚠️ нет данных")
            return

        symbol_info = mt5.symbol_info(self.symbol)
        if not symbol_info or symbol_info.trade_mode != mt5.SYMBOL_TRADE_MODE_FULL:
            print(f"{emoji} {self.symbol} — ⚠️ торговля запрещена")
            return

        spread = symbol_info.ask - symbol_info.bid
        if spread > symbol_info.point * 200:  # допустим максимум 20 пунктов для мажоров
            print(f"{emoji} {self.symbol} — ⚠️ спред слишком высокий")
            return

        positions = mt5.positions_get(symbol=self.symbol)
        current_position = None
        if positions:
            for pos in positions:
                if self.strategy_name in pos.comment:
                    current_position = pos
                    break

        if current_position:
            print(f"{emoji} {self.symbol} — 🟢 позиция открыта")
            self.check_and_close_position(current_position)
        else:
            signal = self.strategy.check_entry_signal(rates)
            if signal:
                print(f"{emoji} {self.symbol} — ✅ {signal.upper()}")
                self._try_open_order(signal)
            else:
                print(f"{emoji} {self.symbol} — ❌ ⛔")

    def _try_open_order(self, signal):
        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None:
            print(f"❌ {self.symbol}: ошибка тика")
            return

        price = tick.ask if signal == 'buy' else tick.bid
        account_info = mt5.account_info()
        total_equity = account_info.equity if account_info else 40000
        allocation_percent = STRATEGY_ALLOCATION.get(self.strategy_name, 0.25)
        strategy_budget = total_equity * allocation_percent

        lot = self.strategy.calculate_lot(price, self.sl, strategy_budget)
        print(f"🔎 {self.symbol}: бюджет={strategy_budget:.2f}, SL={self.sl}, лот={lot}")

        if lot <= 0:
            print(f"⚠️ {self.symbol}: Лот некорректен")
            return

        print(f"📤 {self.symbol}: открытие {signal.upper()} @ {price:.5f}, лот {lot}")

        result = send_order(
            self.symbol,
            lot,
            mt5.ORDER_TYPE_BUY if signal == 'buy' else mt5.ORDER_TYPE_SELL,
            price,
            sl_points=self.sl,
            tp_points=self.tp,
            comment=f"{self.strategy_name}_entry"
        )

        if result:
            print(f"✅ {self.symbol}: {signal.upper()} открыто (lot {lot})")
            self._log_trade("entry", price, lot, "success")
        else:
            print(f"⚠️ {self.symbol}: ошибка открытия ({signal.upper()})")
            self._log_trade("entry", price, lot, "fail")

    def check_and_close_position(self, position):
        rates = self.strategy.get_rates()
        if rates is None:
            print(f"⚠️ Нет данных для выхода {self.symbol}")
            return

        if self.strategy.check_exit_signal(rates):
            self.close_position(position)

    def close_position(self, position):
        price = mt5.symbol_info_tick(self.symbol)
        if price is None:
            file_logger.error(f"❌ Ошибка тика для закрытия {self.symbol}")
            return

        current_price = price.ask if position.type == mt5.ORDER_TYPE_BUY else price.bid
        result = close_order(position)
        if result:
            print(f"✅ {self.symbol}: позиция закрыта")
            self._log_trade("exit", current_price, position.volume, "success")
        else:
            print(f"❌ {self.symbol}: ошибка закрытия")
            self._log_trade("exit", current_price, position.volume, "fail")
