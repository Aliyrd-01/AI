# Сводка: документы → данные

- Документов: 4
- Без замечаний: 2
- Требуют проверки: 2
- Сумма по валидным (USD): 2,959.60

| Файл | Invoice | Vendor | Дата | Total | Статус | Замечания |
|---|---|---|---|---|---|---|
| invoice_1001.txt | INV-1001 | ACME SUPPLY CO. | 2026-09-12 | 264.60 USD | OK |  |
| invoice_1002.txt | INV-1002 | Blue Harbor Consulting LLC | 2026-09-15 | 1368.00 USD | CHECK | дубликат invoice_no |
| invoice_1003.docx | INV-1003 | Greenleaf Analytics GmbH | 2026-09-18 | 2695.00 USD | OK |  |
| invoice_1004.txt | INV-1002 | Blue Harbor Consulting LLC | 2026-09-18 | 600.00 USD | CHECK | арифметика: 475.00 + 95.00 != 600.00; дубликат invoice_no |

> Запись в PostgreSQL выполняется через MCP: готовый SQL — `insert.sql`.