import os
import csv
from collections import defaultdict
from datetime import datetime
from glob import glob


def generate_summary_report(logs_folder="logs"):
    summary = defaultdict(lambda: {
        "entry": 0,
        "exit": 0,
        "profit_trades": 0,
        "fail_trades": 0,
        "profit": 0.0
    })

    for filepath in glob(os.path.join(logs_folder, "*.csv")):
        strategy_name = os.path.basename(filepath).replace(".csv", "")

        deals = []

        with open(filepath, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                action = row.get('action')
                symbol = row.get('symbol')
                price = float(row.get('price', 0))
                lot = float(row.get('lot', 0))
                side = row.get('side', 'buy')
                result = row.get('result')

                if action == 'entry':
                    summary[strategy_name]['entry'] += 1
                    if result == 'success':
                        summary[strategy_name]['profit_trades'] += 1
                        deals.append({
                            "side": side,
                            "price": price,
                            "lot": lot
                        })
                    else:
                        summary[strategy_name]['fail_trades'] += 1

                elif action == 'exit':
                    summary[strategy_name]['exit'] += 1
                    if deals:
                        entry = deals.pop(0)
                        profit = calculate_profit(entry['side'], entry['price'], price, entry['lot'])
                        summary[strategy_name]['profit'] += profit

    # Вывод отчёта
    print("\n📊 Стратегии — сводный отчёт:\n")
    print(f"{'Стратегия':<35} {'Входов':<7} {'Выходов':<9} {'Успехов':<8} {'Ошибок':<8} {'Профит':<10}")
    print("-" * 80)

    for strategy, data in summary.items():
        print(f"{strategy:<35} {data['entry']:<7} {data['exit']:<9} {data['profit_trades']:<8} {data['fail_trades']:<8} {data['profit']:.2f}")

def calculate_profit(side, entry_price, exit_price, lot):
    if side == 'buy':
        profit = (exit_price - entry_price) * lot * 100000
    else:  # sell
        profit = (entry_price - exit_price) * lot * 100000
    return profit

if __name__ == "__main__":
    generate_summary_report()