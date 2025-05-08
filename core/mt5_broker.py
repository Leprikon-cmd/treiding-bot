
from typing import Optional
import MetaTrader5 as mt5

class Mt5Broker:
    def __init__(self):
        if not mt5.initialize():
            raise RuntimeError(f"MT5 initialization failed: {mt5.last_error()}")

    def shutdown(self):
        mt5.shutdown()

    def get_account_info(self):
        return mt5.account_info()

    def get_symbol_info(self, symbol: str):
        return mt5.symbol_info(symbol)

    def get_tick(self, symbol: str):
        return mt5.symbol_info_tick(symbol)

    def copy_rates(self, symbol: str, timeframe, start_pos: int, count: int):
        return mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)

    def send_order(self, request: dict):
        return mt5.order_send(request)

    def close_order(self, ticket: int):
        position = mt5.positions_get(ticket=ticket)
        if position is None or len(position) == 0:
            return None
        pos = position[0]
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "position": ticket,
            "price": mt5.symbol_info_tick(pos.symbol).bid if pos.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(pos.symbol).ask,
            "deviation": 10,
            "magic": 234000,
            "comment": "Close order",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        return mt5.order_send(close_request)

    def get_open_positions(self, symbol: Optional[str] = None):
        if symbol:
            return mt5.positions_get(symbol=symbol)
        return mt5.positions_get()
    