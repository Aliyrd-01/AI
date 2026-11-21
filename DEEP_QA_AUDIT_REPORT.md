# Полный отчёт глубокого тестирования и аудита безопасности (Senior QA & AppSec)
**Проект:** Portfolio Hub & AI Agents
**Дата аудита:** 21 ноября 2026 г.  
**Роль аудитора:** Senior QA Engineer / Application Security Specialist  
**Область тестирования:** Полный стек (RAG Core & UI, PostgreSQL MCP Server, n8n Automation Workflows, Hallucination Benchmark, AutoAgent Framework, Unified Agent, Инфраструктура Docker/Caddy).

---

## 1. Исполнительное резюме (Executive Summary)

В ходе углублённого аудита кодовой базы и динамического тестирования компонентов портфолио было проведено всестороннее тестирование функциональности, отказоустойчивости, изоляции окружений и безопасности:
- **Всего проверено подсистем:** 6 (RAG, MCP, n8n, Benchmark, AutoAgent, Infra).
- **Всего выявлено дефектов и уязвимостей:** 8 новых проблем глубокого уровня (в дополнение к 20 базовым, исправленным ранее).
- **Критических (Critical):** 1 (уязвимости в цепочке npm-зависимостей корневого MCP).
- **Высоких (High):** 2 (логический обход `READ_ONLY` через инвертированный CTE; ложный отказ Strict Grounding в режиме QA).
- **Средних (Medium):** 3 (выполнение команд без экранирования в `LocalEnv` AutoAgent; чужие ID в n8n JSON; падение `test_readonly.mjs` в изолированной среде).
- **Низких / Архитектурных (Low):** 2 (раскрытие внутренних провайдеров/моделей в RAG UI; противоречие между витриной MCP и агентом).

---

## 2. Сводная таблица найденных проблем

| ID | Компонент | Уровень | Дефект / Уязвимость | Статус проверки |
|:---|:---|:---:|:---|:---:|
| **SEC-01** | `projects/mcp-servers` | 🔴 **CRITICAL** | 44 уязвимости npm (2 Critical, 30 High), включая `proxy-addr` IP spoofing, `@modelcontextprotocol/sdk` data leak, `@hono/node-server` Path Traversal | Подтверждено динамическим `npm audit` |
| **SEC-02** | `pg-mcp-server/server.js` | 🟠 **HIGH** | Обход проверки `READ_ONLY` через инвертированный CTE (`WITH x AS (SELECT 1) DELETE FROM ...`) в инструменте `select` | Подтверждено эксплойт-тестом в Node.js AST |
| **BUG-01** | `hub/views/1_RAG.py` | 🟠 **HIGH** | Ложный отказ (False Refusal) при валидных источниках в режиме QA из-за пропуска `remap_citation_ids` | Подтверждено анализом пайплайна строк 967–980 |
| **SEC-03** | `autoagent/local_env.py` | 🟡 **MEDIUM** | Выполнение shell-команд через прямую интерполяцию строк в bash без экранирования `shlex.quote` | Подтверждено анализом AST `subprocess.Popen` |
| **BUG-02** | `projects/mcp-servers` | 🟡 **MEDIUM** | Неочищенный экспорт n8n `build_pg_mcp_server.json` с чужими `instanceId` и `credentials` | Подтверждено инспекцией JSON |
| **BUG-03** | `pg-mcp-server` | 🟡 **MEDIUM** | Контрактный тест `test_readonly.mjs` падает по таймауту 20с в изолированном окружении со скрытием ошибок | Подтверждено запуском в Windows Sandbox |
| **UI-01** | `hub/views/1_RAG.py` | 🟢 **LOW** | Раскрытие внутренних моделей, апстрим-провайдера (Qubax) и эндпоинтов трейсинга LangSmith в публичном UI | Подтверждено кодом строк 836, 856 |
| **UI-02** | `hub/views/4_MCP.py` | 🟢 **LOW** | Архитектурное несоответствие: витрина MCP рекламирует 10 RW-инструментов, противореча режиму `read-only` | Подтверждено сниппетом `TOOLS_SNIPPET` |

---

## 3. Детальный разбор проблем и доказательства (Proof of Concept)

### 🔴 SEC-01: Критические CVE в зависимостях `projects/mcp-servers`
* **Файлы:** `projects/mcp-servers/package.json`, `projects/mcp-servers/package-lock.json`.
* **Описание:** 
  Хотя в подпапке `projects/mcp-servers/pg-mcp-server` зависимости были обновлены до `express 5.2.1` (0 уязвимостей), в корневой папке `projects/mcp-servers/` находится устаревший `package-lock.json`, содержащий:
  1. `proxy-addr (1.1.0 - 2.0.7)`: **CRITICAL (GHSA-jqcg-44mw-7w3h)** — IP-спуфинг через IPv4-mapped IPv6 trust subnet при проксировании запросов клиентом.
  2. `@modelcontextprotocol/sdk (<=1.31.0)`: **HIGH** — утечка сессионных данных между клиентами при параллельных запросах.
  3. `@hono/node-server (<=2.1.2)`: **HIGH (GHSA-frvp-7c67-39w9)** — Path Traversal на Windows через экранированный обратный слэш (`%5C`) в статическом сервере файлов.
  4. `@fastify/busboy (<=3.2.1)`: **HIGH (GHSA-x8mw-p69m-v3mx, GHSA-gxm5-99cw-xjw9)** — DoS и CRLF-инъекции через заголовки multipart.
  5. `@faker-js/faker (<=10.4.0)`: **HIGH (GHSA-qxc2-j82w-r537)** — произвольное выполнение кода через `helpers.fake`.
* **Рекомендация:**
  Удалить `projects/mcp-servers/node_modules` и `package-lock.json`, актуализировать корневой `package.json` либо объединить его с сервисом `pg-mcp-server`.

---

### 🟠 SEC-02: Логический обход проверки `READ_ONLY` в `pg-mcp-server/server.js`
* **Файл:** `projects/mcp-servers/pg-mcp-server/server.js` (строки 117–125).
* **Уязвимый код:**
  ```javascript
  case "select": {
    if (typeof args.sql !== "string") throw new Error("Missing argument: sql");
    if (!/^\s*select\b|^\s*with\b/i.test(args.sql)) throw new Error("select tool accepts SELECT or WITH queries only");
    if (/;/.test(args.sql.trim().replace(/\s*;?\s*$/, ""))) throw new Error("Multiple SQL statements separated by ';' are forbidden");
    // data-modifying CTE: WITH x AS (DELETE ...) SELECT ... — в read-only запрещено
    if (READ_ONLY && /\bwith\b[\s\S]*\bas\s*\(\s*(insert|update|delete|merge)\b/i.test(args.sql)) {
      throw new Error(`Server is in READ_ONLY mode: data-modifying CTE is not available`);
    }
    rows = await runSql(limitSelect(args.sql));
    break;
  }
  ```
* **Доказательство уязвимости (PoC):**
  Регулярное выражение ищет `as ( insert|update|delete|merge` **внутри** подзапроса CTE.
  Если злоумышленник или скомпрометированный агент передает:
  ```sql
  WITH dummy AS (SELECT 1) DELETE FROM leads_leads
  ```
  1. Запрос начинается с `WITH` -> проходит проверку `!/^\s*select\b|^\s*with\b/i`.
  2. Не содержит точки с запятой -> проходит проверку `/;/`.
  3. Внутри `as (...)` находится `SELECT 1`, а не `DELETE` -> проверка `/\bas\s*\(\s*(insert|update|delete|merge)\b/i` возвращает `false`!
  4. Проверка пройдена, запрос передается в пул базы данных!
  5. **В режиме `READ_ONLY=0`:** Запрос беспрепятственно удаляет данные через инструмент, названный `select`.
  6. **В режиме `READ_ONLY=1`:** Сервер выставляет транзакционный флаг `poolConfig.options = "-c default_transaction_read_only=on"`, но если БД работает за пулером (PgBouncer) или опция не применилась, защита уровня приложения полностью пробита.
* **Рекомендация по исправлению:**
  Запретить любые вхождения DML-команд во всем теле запроса инструмента `select`:
  ```javascript
  if (/\b(insert|update|delete|drop|alter|truncate|merge|grant|revoke)\b/i.test(args.sql)) {
    throw new Error("select tool rejects data-modifying keywords");
  }
  ```

---

### 🟠 BUG-01: Ложный отказ Strict Grounding в режиме QA (RAG)
* **Файл:** `hub/views/1_RAG.py` (строки 965–980).
* **Описание дефекта:**
  В режиме диалога (`dialog_mode`, строки 755–759) цитаты нормализуются и ремаппятся:
  ```python
  remapped = remap_citation_ids(answer, doc_numbering)
  if remapped != answer:
      answer = remapped
  answer, leaked = strip_prompt_leak(answer)
  ```
  В режиме QA (дефолтный режим страницы, строки 967–979):
  ```python
  repaired = normalize_citations(answer, retrieved_ids, corpus["source"])
  if repaired != answer:
      answer = repaired
  cited = {str(did) for _, did in extract_citations(answer)}
  issues, _cited, _has_issues = verify_grounding(
      answer, retrieved_ids, len(docs), numbering=doc_numbering)
  if strict_grounding:
      gate = apply_strict_grounding(answer, retrieved_ids, refusal=T["refuse"],
                                    numbering=doc_numbering)
  ```
  Здесь **нет вызова `remap_citation_ids`**!
  Когда LLM генерирует цитату по позиции документа (`[1](msmarco#1)` вместо `[1](msmarco#597651)`):
  - `verify_grounding` проверяет: входит ли `"1"` в список `retrieved_ids` (`['597651', ...]`).
  - Возвращает ошибку: `issues = ["doc 1 not in retrieved set"]`.
  - `apply_strict_grounding` видит `issues` и принудительно заменяет корректный ответ модели на отказ `Отказано: ответ не опирается на найденные документы`.
  - В результате запрос `what color is amber urine` при высоком скоре `0.81` и найденных документах отклонялся UI как ложный отказ.
* **Рекомендация:**
  Добавить вызов `remap_citation_ids` и `strip_prompt_leak` перед `verify_grounding` в строках 967–973.

---

### 🟡 SEC-03: Выполнение shell-команд через прямую интерполяцию строк в `LocalEnv`
* **Файл:** `projects/autoagent/autoagent/environment/local_env.py` (строки 74–77).
* **Уязвимый код:**
  ```python
  def run_command(self, command, stream_callback=None):
      assert self.conda_sh is not None, "Conda.sh not found"
      modified_command = f"/bin/bash -c 'source {self.conda_sh} && conda activate auto && cd {self.docker_workplace} && {command}'"
      process = subprocess.Popen(modified_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
  ```
* **Описание риска:**
  Параметр `command` встраивается внутрь одинарных кавычек bash без предварительного экранирования (`shlex.quote`). Если агент передаст имя файла или аргумент, содержащий одинарную кавычку (например, `' && rm -rf ...`), произойдёт выход за пределы кавычек bash и выполнение произвольной команды на хосте с правами текущего пользователя.
* **Рекомендация:**
  Использовать список аргументов `subprocess.Popen(['/bin/bash', '-c', ...])` с безопасной конкатенацией через `shlex.quote(command)`.

---

### 🟡 BUG-02: Чужие `instanceId` и `credentials` в `build_pg_mcp_server.json`
* **Файл:** `projects/mcp-servers/build_pg_mcp_server.json`.
* **Описание:**
  Файл представляет собой экспорт воркфлоу n8n, но в отличие от файлов в `hub/assets/n8n/`, не был обезличен:
  - Строка 24: `"credentials": { "postgres": { "id": "Yak6RLpeEJfeq6hb", "name": "Postgres account" } }`
  - Строка 648: `"instanceId": "fd9a85cb5fad5f7e754e8f04be7f2ed4c198062572fab2e912fefc2d50bd00a3"`
  - Строка 650: `"id": "PbdktOoU4P9cKtOa"`
  При импорте в чистую установку n8n эти ноды будут привязаны к несуществующему идентификатору подключения.
* **Рекомендация:**
  Удалить внутренние идентификаторы `id` и `instanceId`, оставив понятную заглушку.

---

### 🟡 BUG-03: Падение `test_readonly.mjs` при отсутствии петлевого сетевого доступа
* **Файл:** `projects/mcp-servers/pg-mcp-server/test_readonly.mjs`.
* **Описание:**
  Тест запускает сервер с `stdio: "ignore"` и пытается в цикле опрашивать `http://localhost:9993/health`. В песочнице Windows без сетевого разрешения сокетные вызовы завершаются с ошибкой `EACCES (connect 127.0.0.1:9993)`. Скрипт не выводит ошибку сервера и молча завершается по таймауту 20с с `FAIL server did not become ready within 20s`. При запуске с сетевым разрешением тест проходит (**4/4 PASS**).
* **Рекомендация:**
  Захватывать `stderr` дочернего процесса и выводить его при невозможности соединиться.

---

### 🟢 UI-01: Раскрытие внутренней инфраструктуры в RAG UI
* **Файл:** `hub/views/1_RAG.py` (строки 97–98, 836, 856, 1177).
* **Описание:**
  В интерфейсе для посетителей выводятся технические подробности:
  - `LLM Qubax (qwen3-235b-a22b-2507)` — раскрывает апстрим-провайдера и точный служебный идентификатор модели.
  - `Observability: LangSmith (EU) (eu.api.smith.langchain.com)` — раскрывает адрес европейского инстанса LangSmith.
* **Рекомендация:**
  Для клиентской витрины заменить служебные имена на обезличенные описания: `LLM: 235B Enterprise Model`, `Observability: Active (Distributed Tracing)`.

---

### 🟢 UI-02: Архитектурное несоответствие в `hub/views/4_MCP.py`
* **Файл:** `hub/views/4_MCP.py` (строки 19–34).
* **Описание:**
  На странице MCP в блоке кода показан сервер с 10 инструментами: `insert`, `update`, `delete_rows`, `run_sql`, `create_table`, `add_column`. При этом в соседней вкладке `Unified Agent` акцентируется строгое ограничение `read-only SQL`. Это вводит клиента в заблуждение относительно реальной модели безопасности.
* **Рекомендация:**
  Добавить на страницу MCP пояснение: «По умолчанию сервер работает в защищённом режиме READ_ONLY=1 с отключением DDL/DML на уровне транзакций PostgreSQL. Режим полного доступа (RW) включается отдельной конфигурацией для задач администрирования».

---

## 4. Результаты запусков тестовых сьютов (Verification Matrix)

| Тестовый сьют | Команда | Результат | Статус |
|:---|:---|:---:|:---:|
| **RAG Unit Tests** | `python hub/eval/test_units.py` | 56/56 passed | ✅ PASS |
| **Resilience & Fault Tolerance** | `python -m pytest hub/eval/test_resilience.py` | 10/10 passed | ✅ PASS |
| **AutoAgent Fixed Inventory** | `python -m pytest hub/assets/agents/repo/repo_fixed/tests` | 7/7 passed | ✅ PASS |
| **AutoAgent Baseline Inventory** | `python -m pytest projects/autoagent/cases/sample_repo/tests` | 3 failed, 4 passed (эталон) | ✅ PASS |
| **Hallucination Benchmark Graders** | `python projects/hallucination-benchmark/bench/test_graders.py` | 38/38 passed | ✅ PASS |
| **Hub Views Navigation Smoke** | `python hub/eval/smoke_hub.py` | 12/12 views passed | ✅ PASS |
| **MCP Server Contract Test** | `node projects/mcp-servers/pg-mcp-server/test_readonly.mjs` | 4/4 passed (с сетью) | ✅ PASS |

---

## 5. Заключение

Проект обладает высоким качеством архитектуры (Lost-in-the-Middle ранжирование, RRF гибридный поиск, строгий AST-сендбокс в бенчмарках, транзакционная защита Postgres), однако требует точечного устранения описанных выше 3 ключевых проблем:
1. Исправление пропуска `remap_citation_ids` в `1_RAG.py` для исключения ложных отказов.
2. Усиление regex-санитизатора в `server.js` против инвертированных CTE.
3. Очистка устаревшего `package-lock.json` в корневой папке `projects/mcp-servers/`.
