"""
Конфигурация робота:
• STRATEGY_ALLOCATION — распределение капитала по стратегиям
• SYMBOLS            — перечень торговых инструментов
• LOT                — дефолтный объём
• ATR_SETTINGS       — параметры ATR для SL/TP
• MIN_STOP_POINTS    — минимальные безопасные стопы
• RUB_MARKET_HOURS   — торговые часы для рублёвых пар
• BREAK_EVEN_ATR/...  — параметры безубытка и трейлинга
"""
from typing import Dict, List

# ┌─── БЛОК 1: Распределение капитала и базовые настройки ───────────────
#Бюджеты стратегий
STRATEGY_ALLOCATION = {
    "PriceActionMAStrategy": 0.2,   # 20% от счёта
    "EMARSIVolumeStrategy": 0.4,    # 40% от счёта
    "VWAPStrategy": 0.2,     # 20% от счёта
    "CCIDivergenceStrategy": 0.2,     # 20% от счёта
}

# Trader-specific
MAX_POSITIONS_PER_SYMBOL = 1           # или 2, если стратегии умеют усредняться
DAILY_RISK_LIMIT = 0.03                # 3% депо в убытках → стоп
MAX_CONSECUTIVE_LOSSES = 3
MIN_FREE_MARGIN_RATIO = 0.05           # не открывать, если свободная маржа < 5%
MIN_ENTRY_INTERVAL_SEC = 300           # не чаще раза в 5 минут

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

# процент риска на одну сделку от текущего баланса
RISK_PER_TRADE = 0.02  # 2%

# минимальный и максимальный объём в лотах
MIN_LOT = 0.01
MAX_LOT = 1.0

# ┌─── БЛОК 2: Параметры стратегий (ATR / минимальные стопы) ─────────
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

# ┌─── БЛОК 3: Торговые часы и рублёвые символы ─────────────────────
from datetime import time, timezone, timedelta
MSK = timezone(timedelta(hours=3))
RUB_MARKET_HOURS = {
    "start": time(7, 0, tzinfo=MSK),
    "end":   time(20, 0, tzinfo=MSK),
}

RUB_SYMBOLS = [
    "USDRUBrfd",
    "EURRUBrfd",
    "CNYRUBrfd",
]

# ┌─── БЛОК 4: Параметры безубыточности и трейлинг-стопа ───────────
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

# ┌─── БЛОК 5: Порог спреда и magic numbers ─────────────────────────
# максимально допустимый спред (в пунктах) по каждой паре
SPREAD_THRESHOLD = {
    "default": 0.0005,
    "USDRUBrfd": 0.5,
    "EURRUBrfd": 0.5,
    "CNYRUBrfd": 0.5,
}

# уникальные magic-числа для каждой стратегии
MAGIC_NUMBERS = {
    "PriceActionMAStrategy": 101,
    "EMARSIVolumeStrategy": 102,
    "VWAPStrategy":         103,
    "CCIDivergenceStrategy":104,
}