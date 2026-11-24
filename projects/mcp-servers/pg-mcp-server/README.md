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
- Пароль БД роли `mcp_ro` — в `%USERPROFILE%\mcp_db.env` (строка `PG_PASSWORD=...`, вне git).

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
| `PG_USER` / `PG_PASSWORD` / `PG_DATABASE` | `mcp_ro` (в скрипте запуска) / — / `testPost2` | Подключение к PostgreSQL |

## Роль БД: только чтение, без SUPERUSER

Read-only транзакция запрещает запись, но **не чтение**. Пока сервер ходил под
`postgres` (SUPERUSER), через `select` были доступны `pg_read_file` (любой файл
на хосте БД) и `pg_shadow` (хэши паролей ролей). Это закрыто двумя слоями:

1. **Роль `mcp_ro`** — `NOSUPERUSER`, `CONNECT` + `USAGE` на `public` + `SELECT`
   на существующие и будущие таблицы. Скрипты:
   `db/roles/01_create_mcp_ro.sql` (создать/выровнять права),
   `db/roles/02_check_mcp_ro.sql` (доказать, что запись, `pg_shadow` и
   `pg_read_file` закрыты).
2. **Фильтр в `select`** — функции, читающие файлы хоста или состояние сессии,
   отклоняются с `function "<имя>" is not allowed`: `pg_read_file`,
   `pg_read_binary_file`, `pg_ls_dir`, `pg_ls_waldir`, `pg_ls_logdir`,
   `pg_ls_tmpdir`, `pg_stat_file`, `lo_import`, `lo_export`, `lo_get`,
   `dblink*`, `pg_terminate_backend`, `pg_cancel_backend`, `pg_reload_conf`,
   `set_config`, `pg_sleep`.

Первый слой — настоящая граница (её держит PostgreSQL), второй — страховка на
случай, если сервер снова запустят суперпользователем.

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
node test_server.mjs     # инструменты, ресурсы, промпты + запись на одноразовой таблице
node test_readonly.mjs   # 5/5: дефолт read-only, health, отказ write, запрет CTE
```

`test_server.mjs` поднимает свой инстанс с `READ_ONLY=0` (ему нужен пользователь
с правами на запись — по умолчанию `postgres`), `test_readonly.mjs` — без
переменной `READ_ONLY`, чтобы проверять именно безопасный дефолт. Оба работают
на отдельных портах (`9992`, `9993`) и сами себя останавливают.

Проверка роли БД отдельно:

```powershell
psql -U postgres -d testPost2 -f db\roles\01_create_mcp_ro.sql
psql -U mcp_ro  -d testPost2 -f db\roles\02_check_mcp_ro.sql   # ждём 6 x OK
```

## Ограничения

- Один общий пул на процесс, без пулера запросов.
- Аудит (`AUDIT_FILE`) пишется синхронно в JSONL: `ts`, `kind`, `event`, `ok`, `ms`.
- `select` без `LIMIT` автоматически ограничивается `ROW_LIMIT` строками
  (по умолчанию 100). Явный `LIMIT` в запросе клиента не переопределяется —
  это осознанное поведение «дефолт, а не потолок»: жёсткий предел на стороне
  сервера не реализован.
