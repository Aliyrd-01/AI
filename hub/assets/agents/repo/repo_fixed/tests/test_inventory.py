import pytest

from inventory import add_item, remove_item, stock_report
from pricing import total_value


def test_add_item_accumulates_existing():
    stock = {"widget": 2}
    add_item(stock, "widget", 3)
    assert stock["widget"] == 5


def test_add_item_creates_new():
    stock = {}
    add_item(stock, "gizmo", 4)
    assert stock["gizmo"] == 4


def test_remove_item_rejects_negative_stock():
    stock = {"widget": 2}
    with pytest.raises(ValueError):
        remove_item(stock, "widget", 5)
    assert stock["widget"] == 2


def test_remove_item_ok():
    stock = {"widget": 5}
    assert remove_item(stock, "widget", 2) == 3


def test_remove_missing_item_raises_keyerror():
    with pytest.raises(KeyError):
        remove_item({}, "ghost", 1)


def test_total_value():
    assert total_value({"a": 2, "b": 3}, {"a": 10.0, "b": 1.5}) == 24.5


def test_total_value_missing_price():
    with pytest.raises(ValueError):
        total_value({"a": 2, "b": 3}, {"a": 10.0})
