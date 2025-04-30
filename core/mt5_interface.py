import MetaTrader5 as mt5
from utils.logger import file_logger, console_logger
from datetime import datetime, timezone, time

# RUB-пары
RUB_SYMBOLS = ["USDRUBrfd", "EURRUBrfd", "CNYRUBrfd"]
RUB_MARKET_START = time(7, 0)   # 07:00 по Москве
RUB_MARKET_END = time(20, 0)    # 20:00 по Москве

def is_rub_market_open(symbol):
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        file_logger.error(f"❌ Не удалось получить тик для {symbol} при проверке времени торговли.")
        return False

    server_time = datetime.utcfromtimestamp(tick.time)
    moscow_time = server_time.replace(tzinfo=timezone.utc).astimezone(timezone.utc).time()

    return RUB_MARKET_START <= moscow_time <= RUB_MARKET_END

def send_order(symbol, lot, order_type, price, sl_points=100, tp_points=100, comment=""):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        file_logger.error(f"❌ Символ {symbol} не найден")
        return False

    account_info = mt5.account_info()
    if account_info is None:
        file_logger.error("❌ Не удалось получить информацию о счёте.")
        return False

    # ⛔ Проверка времени торговли для RUB-пар
    if symbol in RUB_SYMBOLS and not is_rub_market_open(symbol):
        file_logger.warning(f"⏱️ {symbol}: Вне торгового окна RUB (07:00–20:00 МСК)")
        return False

    # 🔍 Подготовка
    point = symbol_info.point
    stop_level_points = symbol_info.trade_stops_level
    stop_level_price = stop_level_points * point
    spread = symbol_info.ask - symbol_info.bid
    min_distance = max(stop_level_price, spread * 2, 10 * point)

    # 🔧 SL и TP
    sl_p = max(sl_points * point, min_distance + 2 * point)
    tp_p = max(tp_points * point, min_distance + 2 * point)

    if order_type == mt5.ORDER_TYPE_BUY:
        sl_price = price - sl_p
        tp_price = price + tp_p
    else:
        sl_price = price + sl_p
        tp_price = price - tp_p

    file_logger.info(
        f"🔍 SL/TP расчёт для {symbol}:\n"
        f"  • price={price:.5f}, spread={spread:.5f}, point={point}, stop_level={stop_level_points}\n"
        f"  • SL={sl_price:.5f}, TP={tp_price:.5f}, min_distance={min_distance:.5f}"
    )

    if not symbol_info.visible or symbol_info.trade_mode != mt5.SYMBOL_TRADE_MODE_FULL:
        file_logger.warning(f"⚠️ Символ {symbol} недоступен для торговли: рынок закрыт или нет сессии.")
        return False

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "sl": sl_price,
        "tp": tp_price,
        "deviation": 10,
        "type_filling": mt5.ORDER_FILLING_FOK,
        "comment": comment,
    }

    result = mt5.order_send(request)

    if result.retcode == mt5.TRADE_RETCODE_DONE:
        file_logger.info(
            f"✅ Сделка открыта: {symbol} | {['BUY','SELL'][order_type]} @ {price:.5f} | SL: {sl_price:.5f} | TP: {tp_price:.5f}"
        )
        return True
    else:
        file_logger.error(
            f"❌ Ошибка отправки ордера по {symbol}: {result.retcode}\n"
            f"📨 Запрос: {request}\n"
            f"📩 Ответ: {result._asdict()}"
        )
        return False