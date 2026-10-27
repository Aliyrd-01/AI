# MCP Servers — запуск и тест (runbook)

Компоненты:
- `pg-mcp-server/` — наш Node.js сервер к PostgreSQL (порт 9002)
- `start-mysql-mcp-server.ps1` — коробочный npm-пакет к MySQL (порт 9001)

---

## ШАГ 1. Запустить сервер + инспектор одной командой (рекомендуется)

Открой PowerShell и выполни две строки:

```powershell
cd <repo>\projects\mcp-servers
.\start-inspector.ps1
```

Обязательно дождись строк:

```
pg-mcp-server started, PID ...
Server is up: http://localhost:9002/mcp
Opening MCP Inspector ...
```

Это окно НЕ закрывай (в нём крутится сервер; свернул — не страшно).

Браузер откроется сам с MCP Inspector, наш сервер уже выбран.

В браузере:
1. **Connect**
2. вкладка **Tools** → **List Tools** — увидишь 10 инструментов
3. `list_tables` → **Run** → список таблиц
4. `select` → SQL `SELECT COUNT(*) FROM leads_leads` → **Run** → число

Завершение: вернись в окно PowerShell, нажми `Ctrl+C` — скрипт остановит сервер.

Если браузер не открылся сам: открой вручную `http://localhost:6274`
(и в UI: Transport = Streamable HTTP, URL = http://localhost:9002/mcp,
Header: `Authorization` = `Bearer <токен из start-pg-mcp-server.ps1>`, далее Connect).

---

## ШАГ 2. Вариант руками: сервер отдельно, инспектор отдельно

Терминал сервера (НЕ закрывать):
```powershell
cd <repo>\projects\mcp-servers
.\start-pg-mcp-server.ps1
```
Успех = баннер «PostgreSQL MCP Server / URL: http://localhost:9002/mcp».

Терминал инспектора:
```powershell
npx @modelcontextprotocol/inspector@latest --transport http --server-url http://localhost:9002/mcp --header "Authorization: Bearer <токен из скрипта сервера>"
```
(токен взять из `start-pg-mcp-server.ps1`, строка REMOTE_SECRET_KEY)

После установки зависимостей сервера (один раз):
```powershell
cd <repo>\projects\mcp-servers\pg-mcp-server
npm install
```

---

## ШАГ 3. Проверка доступности без браузера (сервер из ШАГА 2 ещё работает)

В любом новом окне (папка не важна):
```powershell
Invoke-RestMethod -Uri http://localhost:9002/mcp -Method Post `
  -ContentType "application/json" `
  -Headers @{ Accept = "application/json, text/event-stream" } `
  -Body '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}'
```
Ответ JSON — сервер доступен.

---

## ШАГ 4. MySQL MCP (готовый пакет, по желанию)

```powershell
cd <repo>\projects\mcp-servers
.\start-mysql-mcp-server.ps1
```
Эндпоинт: `POST http://localhost:9001/mcp`.
Коннект к БД — переменные окружения в скрипте (MYSQL_HOST/USER/PASS/DB), заполнить один раз.
В инспекторе: то же самое, только URL `http://localhost:9001/mcp`.

---

## ШАГ 5. Подключить к агенту в n8n

В воркфлоу: **AI Agent** → снизу поле инструментов → **MCP Client**:

| Параметр | Значение |
|----------|----------|
| Server Transport | `Streamable HTTP` |
| Endpoint | `http://localhost:9002/mcp` |
| Additional Headers | `Authorization: Bearer <токен>` |

В чат агенту: «покажи таблицы» / «сколько лидов» — агент сам выберет tool.
Пример воркфлоу: `MySQL-MCP.json` в этой папке (Chat Trigger → AI Agent → MCP Client).
