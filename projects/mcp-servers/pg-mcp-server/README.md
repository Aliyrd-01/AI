# PostgreSQL MCP Server

MCP сервер для базы `testPost2` (localhost:5432). Работает через Streamable HTTP.

## Запуск

```powershell
.\start-pg-mcp-server.ps1
# или
node server.js
```

Порт: **9002**, эндпоинт: `POST http://localhost:9002/mcp`
Аутентификация: `Authorization: Bearer REDACTED_KEY`

## Tools

| Tool | Описание | Параметры |
|---|---|---|
| `list_tables` | Список таблиц | — |
| `describe_table` | Колонки таблицы | `table` |
| `select` | SELECT запрос | `sql` |
| `insert` | Вставить строку | `table`, `data` (object) |
| `update` | Обновить строки | `table`, `set` (object), `where` (string) |
| `delete_rows` | Удалить строки | `table`, `where` |
| `create_table` | Создать таблицу | `sql` |
| `add_column` | Добавить колонку | `table`, `column_def` |
| `create_index` | Создать индекс | `table`, `columns` |
| `run_sql` | Любой SQL запрос | `sql` |

## Resources

- `postgres://tables` — список таблиц
- `postgres://table/{name}` — колонки, row_count, sample_rows

## Prompts

- `explain_table(table, detail?)` — описание таблицы
- `query_data(table, question)` — генерация SQL

## Подключение к n8n

**Settings → MCP → Add Server:**
- Name: `PostgreSQL MCP`
- Transport: `Streamable HTTP`
- URL: `http://localhost:9002/mcp`
- Headers: `Authorization: Bearer REDACTED_KEY`

После этого в workflow добавь **MCP Client** узел, выбери сервер — tools появятся в выпадающем списке.
