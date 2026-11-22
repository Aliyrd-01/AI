# PostgreSQL MCP Server

MCP-сервер к PostgreSQL (`testPost2` на `localhost:5432`) на официальном
`@modelcontextprotocol/sdk`. Транспорт — Streamable HTTP, точка входа `POST /mcp`.
По умолчанию работает **в режиме только для чтения**.

## Запуск

```powershell
# из папки projects/mcp-servers (скрипт сам подставит PG_* и токен)
.\start-pg-mcp-server.ps1

# или напрямую (переменные окружения уже должны быть выставлены)
node server.js
```

- Порт: **9002** (`PORT`)
- MCP: `POST http://localhost:9002/mcp`
- Health: `GET http://localhost:9002/health` → `{ok, read_only, auth_required}`
- Авторизация: `Authorization: Bearer <token>`, токен = `REMOTE_SECRET_KEY` сервера.
  Локально он хранится в `%USERPROFILE%\mcp_token.env` (строка `MCP_TOKEN=...`, вне git).

Сервер **не стартует** с пустым `REMOTE_SECRET_KEY` (exit 1). Для локальных
экспериментов без токена есть единственный обход — `ALLOW_NO_AUTH=1`.

## Переменные окружения

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `PORT` | `9002` | HTTP-порт |
| `REMOTE_SECRET_KEY` | — | Bearer-токен; пустой = отказ старта |
| `ALLOW_NO_AUTH` | `0` | `1` — разрешить старт без токена (локально) |
| `READ_ONLY` | `1` | `0` — разрешить write-инструменты |
| `ROW_LIMIT` | `100` | Автоматический `LIMIT` для `select` |
| `AUDIT_FILE` | — | Путь к JSONL-аудиту вызовов |
| `PG_HOST` / `PG_PORT` | `localhost` / `5432` | Подключение к PostgreSQL |
| `PG_USER` / `PG_PASSWORD` / `PG_DATABASE` | `postgres` / — / `testPost2` | Подключение к PostgreSQL |

## Режим только для чтения

При `READ_ONLY=1` (по умолчанию):

- доступны `list_tables`, `describe_table`, `select`;
- `insert`, `update`, `delete_rows`, `create_table`, `add_column`,
  `create_index`, `run_sql` возвращают ошибку `READ_ONLY`;
- защита продублирована на уровне БД: пул открывается с
  `options=-c default_transaction_read_only=on`, поэтому write не пройдёт,
  даже если проверка в коде будет обойдена;
- `select` принимает только `SELECT`/`WITH`, один запрос, и отклоняет
  DML/DDL внутри тела (включая `WITH x AS (SELECT 1) DELETE ...`).

Write-инструменты включаются только явным `READ_ONLY=0` — это режим
администрирования, ответственность за SQL лежит на вызывающей стороне.

## Инструменты

| Инструмент | Назначение | Аргументы | Read-only |
|---|---|---|---|
| `list_tables` | Список таблиц схемы `public` | — | да |
| `describe_table` | Колонки и типы таблицы | `table` | да |
| `select` | Чтение данных (`SELECT`/`WITH`) | `sql` | да |
| `insert` | Вставка строк | `table`, `data` | нет |
| `update` | Обновление строк | `table`, `set`, `where` | нет |
| `delete_rows` | Удаление строк | `table`, `where` | нет |
| `create_table` | DDL: создание таблицы | `sql` | нет |
| `add_column` | DDL: новая колонка | `table`, `column_def` | нет |
| `create_index` | DDL: индекс | `table`, `columns` | нет |
| `run_sql` | Произвольный SQL | `sql` | нет |

Идентификаторы таблиц и колонок проверяются по шаблону `^[A-Za-z_][A-Za-z0-9_]{0,62}$`,
значения передаются параметрами (`$1`), а не склейкой строки.

## Ресурсы и промпты

- Ресурсы: `postgres://tables`, `postgres://table/{name}`
- Промпты: `explain_table(table, detail?)`, `query_data(table, question)`

## Проверки

```powershell
node test_server.mjs     # tools/list + успешный select
node test_readonly.mjs   # 4/4: health, read-инструменты, отказ write, запрет CTE
```

Сервер, который поднимает `test_readonly.mjs`, работает на порту `9993` и сам
себя останавливает; `stderr` дочернего процесса печатается при неудачном старте.

## Ограничения

- Один общий пул на процесс, без пулера запросов.
- Аудит (`AUDIT_FILE`) пишется синхронно в JSONL: `ts`, `kind`, `event`, `ok`, `ms`.
- `select` ограничен `ROW_LIMIT` строками (по умолчанию 100).
