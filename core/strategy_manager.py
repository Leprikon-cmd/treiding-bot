from strategies.ema_cross import EMARSIVolumeStrategy
from strategies.price_action_ma import PriceActionMAStrategy
from strategies.vwap import VWAPStrategy
from strategies.cci_divergence import CCIDivergenceStrategy

class StrategyManager:
    def __init__(self, strategy_name, symbol, timeframe, lot):
        self.strategy_name = strategy_name.lower()
        self.symbol = symbol
        self.timeframe = timeframe
        self.lot = lot

    def get_strategy(self):
        if self.strategy_name == "ema_cross":
            return EMARSIVolumeStrategy(self.symbol, self.timeframe, self.lot)
        elif self.strategy_name == "price_action_ma":
            return PriceActionMAStrategy(self.symbol, self.timeframe, self.lot)
        elif self.strategy_name == "vwap":
            return VWAPStrategy(self.symbol, self.timeframe, self.lot)
        elif self.strategy_name == "cci_divergence":
            return CCIDivergenceStrategy(self.symbol, self.timeframe, self.lot)
        raise ValueError(f"❌ Неизвестная стратегия: {self.strategy_name}")
