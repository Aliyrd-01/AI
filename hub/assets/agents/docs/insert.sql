-- INSERT для PostgreSQL (выполнить через MCP-инструмент)
INSERT INTO invoices (invoice_no, vendor, invoice_date, currency, subtotal, tax, total)
VALUES
  ('INV-1001', 'ACME SUPPLY CO.', '2026-09-12', 'USD', 245.0, 19.6, 264.6),
  ('INV-1003', 'Greenleaf Analytics GmbH', '2026-09-18', 'USD', 2450.0, 245.0, 2695.0)
ON CONFLICT (invoice_no) DO NOTHING;