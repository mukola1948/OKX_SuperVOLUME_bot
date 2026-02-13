"""
config.py

Файл конфігурації бота.
Містить основні параметри роботи:
- список торгових пар
- таймфрейм
- множник сплеску
- мінімальну кількість свічок
"""

PAIRS = [
    "LDO-USDT-SWAP",
    "BTC-USDT-SWAP",
    "OP-USDT-SWAP",
    "ETH-USDT-SWAP"
]

INTERVAL = "1m"

K_SPIKE = 5

MIN_CANDLES = 55
