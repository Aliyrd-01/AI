# Отчёт агента по репозиторию

- Baseline: FAILED
- После правок: PASSED

# Отчёт о тестировании и исправлении багов

## Исходное состояние тестов
Запуск `pytest` показал 3 неудачных теста и 4 успешных.

**Финальный результат (Baseline):**
```
F.F...F                                                                  [100%]
================================== FAILURES ===================================
...
3 failed, 4 passed in 1.87s
```

## Найденные баги

1.  **Файл:** `inventory.py`, **Функция:** `add_item`
    *   **Баг:** При добавлении товара с уже существующим именем происходит перезапись количества вместо прибавления.
    *   **Тест:** `test_add_item_accumulates_existing` падает с ошибкой `assert 3 == 5`.

2.  **Файл:** `inventory.py`, **Функция:** `remove_item`
    *   **Баг:** Функция не проверяет, что количество не станет отрицательным, и не выбрасывает исключение `ValueError`.
    *   **Тест:** `test_remove_item_rejects_negative_stock` падает с ошибкой `DID NOT RAISE ValueError`.

3.  **Файл:** `pricing.py`, **Функция:** `total_value`
    *   **Баг:** При отсутствии цены на товар выбрасывается `KeyError`, вместо ожидаемого `ValueError`.
    *   **Тест:** `test_total_value_missing_price` падает с ошибкой `KeyError: 'b'`.

## Изменения (Diff)

### inventory.py
```diff
--- a/inventory.py
+++ b/inventory.py
@@ -5,13 +5,15 @@
 
 def add_item(stock, name, qty):
     """Добавить qty единиц товара name на склад."""
-    stock[name] = qty
+    stock[name] = stock.get(name, 0) + qty
 
 
 def remove_item(stock, name, qty):
     """Списать qty единиц товара name со склада."""
     if name not in stock:
         raise KeyError(name)
+    if stock[name] < qty:
+        raise ValueError()
     stock[name] -= qty
     return stock[name]
 
```

### pricing.py
```diff
--- a/pricing.py
+++ b/pricing.py
@@ -5,7 +5,11 @@
     """Сумма qty * price по всем позициям склада."""
     total = 0.0
     for name, qty in stock.items():
-        total += qty * prices[name]
+        try:
+            price = prices[name]
+        except KeyError:
+            raise ValueError(f"Missing price for {name}")
+        total += qty * price
     return total
 
 
```

## Финальный результат pytest
После внесения исправлений все тесты прошли успешно.

**Финальный результат:**
```
.......                                                                  [100%]
7 passed in 0.11s
```