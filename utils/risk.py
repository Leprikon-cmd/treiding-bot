import math
import MetaTrader5 as mt5
if not mt5.initialize():
    raise RuntimeError("Не удалось инициализировать MT5")

def calculate_raw_lot(risk_rub: float, sl_price: float, price: float, contract_size: float, point: float) -> float:
    """
    Calculate the raw lot size based on risk amount (in account currency) and stop loss distance.
    """
    sl_points = abs(price - sl_price) / point
    pip_value = point * contract_size
    sl_distance = sl_points * pip_value
    if sl_distance <= 0:
        return 0.0
    return risk_rub / sl_distance

def adjust_lot(raw_lot: float, step: float, min_lot: float, max_lot: float) -> float:
    """
    Adjust raw lot to conform with broker's volume step, and enforce min/max limits.
    """
    lot = math.floor(raw_lot / step) * step
    lot = max(min_lot, lot)
    lot = min(max_lot, lot)
    return lot

def max_affordable_lot(symbol: str, lot: float, price: float) -> float:
    """
    Iteratively reduce lot size until required margin fits within free margin.
    """
    account = mt5.account_info()
    if account is None:
        return 0.0
    margin_free = account.margin_free
    info = mt5.symbol_info(symbol)
    if info is None:
        return 0.0
    step = info.volume_step
    current_lot = lot
    while current_lot >= step:
        margin_req = mt5.order_calc_margin(mt5.ORDER_TYPE_BUY, symbol, current_lot, price)
        if margin_req <= margin_free:
            return current_lot
        current_lot -= step
    return 0.0