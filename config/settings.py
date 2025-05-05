#Бюджеты стратегий
STRATEGY_ALLOCATION = {
    "PriceActionMAStrategy": 0.2,   # 20% от счёта
    "EMARSIVolumeStrategy": 0.4,    # 40% от счёта
    "VWAPStrategy": 0.2,     # 20% от счёта
    "CCIDivergenceStrategy": 0.2,     # 20% от счёта
}

# Валютные пары для торговли
SYMBOLS = [
    "EURUSDrfd",
    "GBPUSDrfd",
    "USDJPYrfd",
    "USDCHFrfd",
    "USDCADrfd",
    "AUDUSDrfd",
    "NZDUSDrfd",
    "USDRUBrfd",
    "EURRUBrfd",
    "CNYRUBrfd",
]

# Лот по умолчанию
LOT = 0.01

# ATR-based dynamic SL/TP settings per strategy
ATR_SETTINGS = {
    "PriceActionMAStrategy":    { "period":14, "sl_multiplier":1.5, "tp_multiplier":2.0 },
    "EMARSIVolumeStrategy":     { "period":14, "sl_multiplier":2.0, "tp_multiplier":3.0 },
    "VWAPStrategy":             { "period":14, "sl_multiplier":1.5, "tp_multiplier":2.5 },
    "CCIDivergenceStrategy":    { "period":14, "sl_multiplier":1.0, "tp_multiplier":1.5 },
}

# Минимальные безопасные стопы в пунктах по каждой валютной паре
MIN_STOP_POINTS = {
    "EURUSDrfd": 15,
    "GBPUSDrfd": 15,
    "USDJPYrfd": 15,
    "USDCHFrfd": 15,
    "USDCADrfd": 15,
    "AUDUSDrfd": 15,
    "NZDUSDrfd": 15,
    "USDRUBrfd": 50,
    "EURRUBrfd": 50,
    "CNYRUBrfd": 50,
}

from datetime import time

# Часы торговли по Москве для RUB-пар (07:00 — 20:00)
RUB_MARKET_HOURS = {
    "start": time(7, 0),   # 07:00
    "end": time(20, 0),    # 20:00
}

RUB_SYMBOLS = [
    "USDRUBrfd",
    "EURRUBrfd",
    "CNYRUBrfd",
]

# ATR-based break-even and trailing stop settings per strategy
BREAK_EVEN_ATR = {
    "PriceActionMAStrategy": 1.0,
    "EMARSIVolumeStrategy": 1.0,
    "VWAPStrategy": 1.0,
    "CCIDivergenceStrategy": 1.0,
}

TRAILING_ATR = {
    "PriceActionMAStrategy": 1.5,
    "EMARSIVolumeStrategy": 2.0,
    "VWAPStrategy": 1.5,
    "CCIDivergenceStrategy": 1.5,
}

TRAILING_STEP_ATR = {
    "PriceActionMAStrategy": 0.5,
    "EMARSIVolumeStrategy": 0.5,
    "VWAPStrategy": 0.5,
    "CCIDivergenceStrategy": 0.5,
}