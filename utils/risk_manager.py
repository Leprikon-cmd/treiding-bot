
class RiskManager:
    def __init__(self, risk_per_trade=0.01):
        self.risk_per_trade = risk_per_trade

    def get_lot(self, equity, atr, stop_distance):
        if atr == 0 or stop_distance == 0:
            return 0.01
        risk_amount = equity * self.risk_per_trade
        lot = risk_amount / (atr * stop_distance)
        return round(min(max(lot, 0.01), 100), 2)  # Ограничение по минимальному и максимальному лоту
