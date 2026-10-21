"""Простое управление складом."""

from pricing import total_value


def add_item(stock, name, qty):
    """Добавить qty единиц товара name на склад."""
    stock[name] = qty


def remove_item(stock, name, qty):
    """Списать qty единиц товара name со склада."""
    if name not in stock:
        raise KeyError(name)
    stock[name] -= qty
    return stock[name]


def stock_report(stock, prices):
    """Вернуть количество и суммарную стоимость склада."""
    return {"total_qty": sum(stock.values()), "total_value": total_value(stock, prices)}
