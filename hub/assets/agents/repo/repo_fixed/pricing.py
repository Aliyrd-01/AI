"""Цены и форматирование денег."""


def total_value(stock, prices):
    """Сумма qty * price по всем позициям склада."""
    total = 0.0
    for name, qty in stock.items():
        try:
            price = prices[name]
        except KeyError:
            raise ValueError(f"Missing price for {name}")
        total += qty * price
    return total


def format_money(value):
    """Формат денежной суммы."""
    return f"${value:.2f}"