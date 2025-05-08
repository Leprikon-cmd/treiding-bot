
from .entry_guards import EntryGuards, GuardError
from utils.risk_manager import RiskManager
from .mt5_broker import Mt5Broker
from utils.logger import file_logger
import MetaTrader5 as mt5
from core.mt5_interface import send_order, close_order
from config.settings import STRATEGY_ALLOCATION
import os
import csv
from datetime import datetime
import pandas as pd
from config.settings import ATR_SETTINGS, RISK_PER_TRADE, MIN_LOT, MAX_LOT
from config.settings import BREAK_EVEN_ATR, TRAILING_ATR, TRAILING_STEP_ATR
from config.settings import MAX_POSITIONS_PER_SYMBOL, DAILY_RISK_LIMIT, MAX_CONSECUTIVE_LOSSES, MIN_FREE_MARGIN_RATIO, MIN_ENTRY_INTERVAL_SEC
from datetime import datetime, timedelta
import math

STRATEGY_ICONS = {
    "EMARSIVolumeStrategy": "🕰️",
    "PriceActionMAStrategy": "⚡",
    "VWAPStrategy": "📊",
    "CCIDivergenceStrategy": "💸",
}

def log_cycle_header():
    print(f"\n🔁 Новый цикл обработки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

class Trader:
    def __init__(self, symbol, strategy):
        self.symbol = symbol
        self.strategy = strategy
        self.strategy_name = self.strategy.__class__.__name__
        self.log_path = f"logs/{self.strategy_name}_{self.symbol}.csv"
        self._prepare_log()
        # session risk tracking
        self.daily_pnl = 0.0
        self.consec_losses = 0
        self.last_entry_time = None
        # Initialize trailing/break-even state per position
        self._trailing_state = {}

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

        symbol_info = self.broker.symbol_info(self.symbol)
        if not symbol_info or symbol_info.trade_mode != self.broker.SYMBOL_TRADE_MODE_FULL:
            print(f"{emoji} {self.symbol} — ⚠️ торговля запрещена")
            return

        spread = symbol_info.ask - symbol_info.bid
        if spread > symbol_info.point * 200:  # допустим максимум 20 пунктов для мажоров
            print(f"{emoji} {self.symbol} — ⚠️ спред слишком высокий")
            return

        positions = self.broker.positions_get(symbol=self.symbol)
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
            # Debug: log strategy entry check details
            file_logger.info(f"{self.symbol}: проверка входного сигнала ({self.strategy_name}) на {len(rates)} баров, последний close={rates[-1]['close']}")
            print(f"DEBUG {self.symbol}: running check_entry_signal for last close={rates[-1]['close']}")
            # Print last 5 bars for debugging
            last_bars = rates[-5:]
            print(f"DEBUG {self.symbol}: последние 5 баров (time, close): " +
                  ", ".join(f"({datetime.fromtimestamp(b['time']).strftime('%H:%M')}, {b['close']:.5f})" for b in last_bars))
            signal = self.strategy.check_entry_signal(rates)
            file_logger.info(f"{self.symbol}: check_entry_signal returned '{signal}'")
            print(f"DEBUG {self.symbol}: сигнал входа = {signal}")
            if signal:
                print(f"{emoji} {self.symbol} — ✅ {signal.upper()}")
                self._try_open_order(signal, rates)
            else:
                print(f"{emoji} {self.symbol} — ❌ ⛔")

    
    def _try_open_order(self, rates):
        account = self.broker.get_account_info()
        positions = self.broker.get_open_positions(symbol=self.symbol)  # предполагаем, что метод добавлен

        guards = EntryGuards(account, positions, settings={"min_free_margin": 100, "max_positions": 5})
        try:
            guards.check_all()
        except GuardError as e:
            print(f"[GUARD] {e}")
            return

        signal = self.strategy.check_entry_signal(rates)
        if not signal:
            return

        atr = self._compute_atr(rates)  # предполагается, что уже есть
        risk_mgr = RiskManager()
        lot = risk_mgr.get_lot(account.equity, atr, abs(signal.sl - rates[-1]["close"]))

        request = {
            "symbol": self.symbol,
            "volume": lot,
            "type": self._get_order_type(signal.direction),
            "price": self._get_price(signal.direction),
            "sl": signal.sl,
            "tp": signal.tp,
            "deviation": 10,
            "magic": 123456,
            "comment": "entry",
            "type_time": 0,
            "type_filling": 1,
        }

        result = self.broker.send_order(request)
        print(f"[ORDER] Sent: {result}")
    

        account = self.broker.account_info()
        full_equity = account.equity if account else 40000
        allocation = STRATEGY_ALLOCATION.get(self.strategy_name, 1.0)  # например, 0.2 для 20%
        allocated_equity = full_equity * allocation
        file_logger.info(
            f"Стратегия {self.strategy_name}: {self.symbol}: total_equity={full_equity:.2f}, allocation={allocation*100:.0f}%, "
            f"allocated_equity={allocated_equity:.2f}"
        )

        # до того, как мы рассчитываем лот
        if account and account.margin_free < allocated_equity * MIN_FREE_MARGIN_RATIO:
            file_logger.warning(
                f"{self.symbol}: свободная маржа ({account.margin_free:.2f}) "
                f"< {MIN_FREE_MARGIN_RATIO*100:.0f}% выделенного капитала ({allocated_equity:.2f}), входы приостановлены")
            return

        # Max positions per symbol guard
        positions = self.broker.positions_get(symbol=self.symbol) or []
        if len(positions) >= MAX_POSITIONS_PER_SYMBOL:
            print(f"⚠️ {self.symbol}: уже открыто {len(positions)} позиций, максимум {MAX_POSITIONS_PER_SYMBOL}")
            return

        # Daily loss guard
        if account and self.daily_pnl < -DAILY_RISK_LIMIT * account.balance:
            print(f"⚠️ {self.symbol}: дневной убыток превысил {DAILY_RISK_LIMIT*100:.0f}% депо")
            return

        # Consecutive losses guard
        if self.consec_losses >= MAX_CONSECUTIVE_LOSSES:
            print(f"⚠️ {self.symbol}: подряд {self.consec_losses} убыточных сделок, входы заблокированы")
            return

        # Multi-TF filter: require H4 trend alignment
        rates_h4 = self.broker.copy_rates_from(self.symbol, self.broker.TIMEFRAME_H4, datetime.now(), 100)
        if rates_h4 is not None and len(rates_h4) > 0:
    
            df_h4 = pd.DataFrame(rates_h4)
            sma_short = df_h4['close'].rolling(window=10).mean().iloc[-1]
            sma_long = df_h4['close'].rolling(window=50).mean().iloc[-1]
            if (signal == 'buy' and sma_short < sma_long) or (signal == 'sell' and sma_short > sma_long):
                file_logger.info(f"{self.symbol}: H4 trend mismatch (sma10={sma_short:.5f}, sma50={sma_long:.5f}), вход {signal} отменён")
                return

        # динамический расчет SL/TP на основе ATR (настройки для каждой стратегии)
        df_atr = pd.DataFrame(rates)
        df_atr['prev_close'] = df_atr['close'].shift(1)
        df_atr['hl'] = df_atr['high'] - df_atr['low']
        df_atr['hc'] = (df_atr['high'] - df_atr['prev_close']).abs()
        df_atr['lc'] = (df_atr['low'] - df_atr['prev_close']).abs()
        df_atr['tr'] = df_atr[['hl', 'hc', 'lc']].max(axis=1)
        df_atr.drop(columns=['prev_close','hl','hc','lc'], inplace=True)
        strategy_atr = ATR_SETTINGS.get(self.strategy_name, {})
        period = strategy_atr.get('period', 14)
        sl_multiplier = strategy_atr.get('sl_multiplier', 1.5)
        tp_multiplier = strategy_atr.get('tp_multiplier', 3.0)
        atr = df_atr['tr'].rolling(window=period).mean().iloc[-1]

        symbol_info = self.broker.symbol_info(self.symbol)
        point = symbol_info.point

        # SL/TP в пунктах (расчёт через ATR)
        sl_points = (sl_multiplier * atr) / point
        tp_points = (tp_multiplier * atr) / point
        print(f"ATR={atr:.5f}, SL_pts={sl_points:.2f}, TP_pts={tp_points:.2f}")

        tick = self.broker.symbol_info_tick(self.symbol)
        if tick is None:
            print(f"❌ {self.symbol}: ошибка тика")
            return

        price = tick.ask if signal == 'buy' else tick.bid
        # рассчитываем цену стоп-лосса в валютных единицах
        sl_price = price - sl_points * point if signal == 'buy' else price + sl_points * point
        account_info = self.broker.account_info()
        full_equity = account_info.equity if account_info else 40000
        allocation = STRATEGY_ALLOCATION.get(self.strategy_name, 1.0)
        allocated_equity = full_equity * allocation
        # Calculate risk amount based on configured percentage of allocated equity
        risk_amount = allocated_equity * RISK_PER_TRADE
        file_logger.info(f"{self.symbol}: equity full={full_equity:.2f}, allocation={allocation*100:.0f}%, allocated={allocated_equity:.2f}, risk_amount={risk_amount:.2f}")
        
        symbol_info = self.broker.symbol_info(self.symbol)

        # Determine lot size from risk amount and stop-loss
        file_logger.info(
            f"Стратегия {self.strategy_name}: рассчитываю lot на основе price={price:.5f}, "
            f"sl_price={sl_price:.5f}, risk_amount={risk_amount:.2f}"
        )
        raw_lot = self.strategy.calculate_lot(symbol_info, price, sl_price)
        file_logger.info(f"Стратегия {self.strategy_name}: raw_lot={raw_lot:.2f}")
        lot = max(MIN_LOT, min(raw_lot, MAX_LOT))
        file_logger.info(f"Стратегия {self.strategy_name}: lot после clamp [{MIN_LOT}, {MAX_LOT}] = {lot:.2f}")

        # Hard cap: max 10% of allocated equity used for margin per trade
        max_margin_per_trade = allocated_equity * 0.10
        volume_step = symbol_info.volume_step

        # Estimate margin required for 1.0 lot
        margin_for_one_lot = self.broker.order_calc_margin(
            self.broker.ORDER_TYPE_BUY if signal == 'buy' else self.broker.ORDER_TYPE_SELL,
            self.symbol, 1.0, price
        )
        if margin_for_one_lot is None:
            file_logger.error(f"{self.symbol}: не удалось рассчитать маржу для 1.0 лота")
            return
        # Compute maximum allowed lot under margin cap
        allowed_lot = max_margin_per_trade / margin_for_one_lot
        # Convert to steps
        max_steps = math.floor(allowed_lot / volume_step)
        if max_steps <= 0:
            print(f"⚠️ {self.symbol}: недостаточно маржи для минимального лота после ограничения маржи")
            return
        max_lot_by_margin = max_steps * volume_step
        # Final lot is limited by both raw calculation and margin cap
        lot = min(lot, max_lot_by_margin, MAX_LOT)
        file_logger.info(
            f"{self.symbol}: lot capped by margin cap to {lot:.2f} "
            f"(max allowed by margin: {max_lot_by_margin:.2f})"
        )

        print(f"🔎 {self.symbol}: риск={risk_amount:.2f}, SL={sl_points:.2f}, лот={lot}")

        if lot <= 0:
            print(f"⚠️ {self.symbol}: Лот некорректен")
            return

        print(f"📤 {self.symbol}: открытие {signal.upper()} @ {price:.5f}, лот {lot}")

        result = send_order(
            self.symbol,
            lot,
            self.broker.ORDER_TYPE_BUY if signal == 'buy' else self.broker.ORDER_TYPE_SELL,
            price,
            sl_points=sl_points,
            tp_points=tp_points,
            comment=f"{self.strategy_name}_entry"
        )

        if result:
            print(f"✅ {self.symbol}: {signal.upper()} открыто (lot {lot})")
            self._log_trade("entry", price, lot, "success")
            self.last_entry_time = now
        else:
            print(f"⚠️ {self.symbol}: ошибка открытия ({signal.upper()})")
            self._log_trade("entry", price, lot, "fail")

    def _compute_atr(self, rates, period):
        df = pd.DataFrame(rates)
        df['prev_close'] = df['close'].shift(1)
        df['hl'] = df['high'] - df['low']
        df['hc'] = (df['high'] - df['prev_close']).abs()
        df['lc'] = (df['low'] - df['prev_close']).abs()
        df['tr'] = df[['hl', 'hc', 'lc']].max(axis=1)
        return df['tr'].rolling(window=period).mean().iloc[-1]

    def _manage_trailing(self, position, atr):
        """
        Manage break-even and trailing stop-loss adjustments.
        Break-even and trailing levels are recalculated from the current market price,
        enforcing minimal stop distance and treating CODE 10025 (NO_CHANGES) as success.
        """
        # Retrieve symbol parameters and current market tick
        symbol_info = self.broker.symbol_info(self.symbol)
        tick = self.broker.symbol_info_tick(self.symbol)
        if not symbol_info or not tick:
            return

        point = symbol_info.point
        stop_level = symbol_info.trade_stops_level
        min_dist = stop_level * point

        is_buy = position.type == self.broker.ORDER_TYPE_BUY
        # For SL calculations, buy uses bid, sell uses ask
        price_for_sl = tick.bid if is_buy else tick.ask

        entry_price = position.price_open
        current_price = price_for_sl
        profit = (current_price - entry_price) if is_buy else (entry_price - current_price)

        ticket = position.ticket
        state = self._trailing_state.setdefault(ticket, {"be": False, "last_trail": None})

        # Break-even logic
        be_mult = BREAK_EVEN_ATR.get(self.strategy_name, BREAK_EVEN_ATR)
        if not state["be"] and profit >= be_mult * atr:
            # Calculate break-even price at minimal distance
            be_price = entry_price + min_dist if is_buy else entry_price - min_dist
            # Validate new SL: must differ sufficiently and respect minimal distance
            if abs(be_price - price_for_sl) >= min_dist and abs(be_price - position.sl) >= point:
                req = {
                    "action": self.broker.TRADE_ACTION_SLTP,
                    "symbol": self.symbol,
                    "position": ticket,
                    "sl": be_price,
                    "tp": position.tp,
                    "deviation": 10,
                    "type_filling": self.broker.ORDER_FILLING_FOK
                }
                res = self.broker.order_send(req)
                # Treat NO_CHANGES (10025) as success
                if res.retcode in (self.broker.TRADE_RETCODE_DONE, self.broker.TRADE_RETCODE_NO_CHANGES):
                    print(f"🔒 {self.symbol}: SL updated #{ticket} @ {be_price:.5f}")
                else:
                    file_logger.error(f"❌ Ошибка модификации SL/TP #{ticket}: {res.retcode}")
                state["be"] = True
                file_logger.info(f"{self.symbol}: BE SL → {be_price:.5f}, PROFIT={profit:.5f}")
                file_logger.info(f"{self.symbol}: TRAIL SL → {trail_price:.5f}")

        # Trailing stop logic
        trail_mult = TRAILING_ATR.get(self.strategy_name, TRAILING_ATR)
        step_mult = TRAILING_STEP_ATR.get(self.strategy_name, TRAILING_STEP_ATR)
        base_dist = (trail_mult - step_mult) * atr
        trail_price = price_for_sl + base_dist if is_buy else price_for_sl - base_dist

        if state["be"]:
            # Ensure trailing SL respects minimal distance and has changed since last trail
            if abs(trail_price - price_for_sl) >= min_dist and \
               (state["last_trail"] is None or abs(trail_price - state["last_trail"]) >= point):
                req = {
                    "action": self.broker.TRADE_ACTION_SLTP,
                    "symbol": self.symbol,
                    "position": ticket,
                    "sl": trail_price,
                    "tp": position.tp,
                    "deviation": 10,
                    "type_filling": self.broker.ORDER_FILLING_FOK
                }
                res = self.broker.order_send(req)
                if res.retcode in (self.broker.TRADE_RETCODE_DONE, self.broker.TRADE_RETCODE_NO_CHANGES):
                    print(f"↔️ {self.symbol}: трейл #{ticket} @ {trail_price:.5f}")
                else:
                    file_logger.error(f"❌ Ошибка модификации SL/TP #{ticket}: {res.retcode}")
                state["last_trail"] = trail_price
                file_logger.info(f"{self.symbol}: BE SL → {be_price:.5f}, PROFIT={profit:.5f}")
                file_logger.info(f"{self.symbol}: TRAIL SL → {trail_price:.5f}")


    def check_and_close_position(self, position):
        rates = self.strategy.get_rates()
        if rates is None:
            print(f"⚠️ Нет данных для выхода {self.symbol}")
            return

        # compute ATR and apply break-even/trailing logic
        atr = self._compute_atr(self.strategy.get_rates(), ATR_SETTINGS[self.strategy_name]['period'])
        self._manage_trailing(position, atr)

        if self.strategy.check_exit_signal(rates):
            self.close_position(position)

    def close_position(self, position):
        price = self.broker.symbol_info_tick(self.symbol)
        if price is None:
            file_logger.error(f"❌ Ошибка тика для закрытия {self.symbol}")
            return

        current_price = price.ask if position.type == self.broker.ORDER_TYPE_BUY else price.bid
        result = close_order(position)
        if result:
            print(f"✅ {self.symbol}: позиция закрыта")
            self._log_trade("exit", current_price, position.volume, "success")
        else:
            print(f"❌ {self.symbol}: ошибка закрытия")
            self._log_trade("exit", current_price, position.volume, "fail")
