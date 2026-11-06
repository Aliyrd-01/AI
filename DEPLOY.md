# Deploy — как отвязать хаб от локальной машины

Хаб — обычное Streamlit-приложение: эмбеддинги считаются локально через FastEmbed
(модель скачивается в контейнер), а Qdrant и LLM — внешние API. Никаких зависимостей
от домашнего компьютера в коде нет, кроме опционального CRM-моста (MCP).

Ниже три способа получить постоянный публичный URL. Вариант 1 — самый быстрый и бесплатный.

---

## Вариант 1 (рекомендуется): Streamlit Community Cloud — ~5 минут, бесплатно

Постоянный адрес вида `https://<app>.streamlit.app`, машина не нужна.

1. Репозиторий уже на GitHub: `https://github.com/Aliyrd-01/AI` (ветка `main`).
2. Откройте https://share.streamlit.io → **New app** → GitHub → репозиторий `Aliyrd-01/AI`,
   ветка `main`, **Main file path**: `hub/Home.py`.
3. **Advanced settings** → Python **3.12** → **Secrets** — вставьте (значения из локального `.env`):

```toml
QUBAX_API_BASE = "https://api.qubax.ai/v1"
QUBAX_API_KEY = "..."
QUBAX_MODELS = "qwen3-235b-a22b-2507"
AGENT_MODEL = "qwen3-235b-a22b-2507"
OPENAI_API_BASE = "https://opencode.ai/zen/v1"
OPENAI_API_KEY = "..."
QDRANT_URL = "https://<cluster>.cloud.qdrant.io:6333"
QDRANT_API_KEY = "..."
GEMINI_API_KEY = "..."
OPENROUTER_API_KEY = "..."
OPENROUTER_MODEL = "..."
MISTRAL_API_KEY = "..."
MCP_URL = "http://localhost:9002/mcp"
MCP_TOKEN = ""
FASTEMBED_CACHE_PATH = "/tmp/fastembed"
```

4. **Deploy**. Первый старт 3–5 минут (ставится FastEmbed-модель).

`hub/Home.py` сам переносит `st.secrets` в переменные окружения — код менять не нужно.

Что будет работать без MCP: все разделы, RAG-демо, Benchmarks, Testing, Integrations,
Security, Projects, записанные прогоны Unified Agent. Живые CRM-вопросы честно сообщат,
что база недоступна (это заложенное поведение).

Если нужен полностью рабочий CRM — поднимите MCP-сервер рядом (вариант 2) и укажите
`MCP_URL` в секретах на публичный адрес MCP.

---

## Вариант 2: свой VPS + Docker (полный стек, включая CRM)

На сервере (Ubuntu, 2 ГБ RAM хватит):

```bash
git clone https://github.com/Aliyrd-01/AI.git && cd AI
cp .env.example .env      # заполнить ключи
docker compose up -d --build
```

`docker-compose.yml` публикует хаб на `127.0.0.1:7860` — наружу отдаём через Caddy
(в репозитории есть `Caddyfile`): HTTPS и домен ставятся автоматически.

MCP-мост к CRM поднимается отдельно (`projects/mcp-servers/start-pg-mcp-server.ps1`
для Windows; на Linux — `node projects/mcp-servers/pg-mcp-server/server.js`) и требует
доступный PostgreSQL. После этого в `.env` укажите `MCP_URL=http://<host>:9002/mcp`
и `MCP_TOKEN`.

Проверка: `curl -f http://localhost:7860/_stcore/health` → `ok`.

---

## Вариант 3: Hugging Face Spaces (бесплатно, Docker SDK)

1. New Space → SDK: **Docker** → Blank.
2. Загрузите содержимое репозитория (или подключите GitHub).
3. Dockerfile уже слушает `7860` — порт Spaces. Секреты — в Settings → Variables and secrets
   (имена те же, что в списке выше).

---

## Почему trycloudflare «работает только у меня»

`cloudflared tunnel --url http://localhost:8501` — это туннель **к вашей машине**:
процесс на компьютере принимает трафик и проксирует его в локальный Streamlit.
Пока машина/туннель живы — ссылка работает; при перезапуске адрес меняется, а сети
некоторых провайдеров блокируют `*.trycloudflare.com`. Это не проблема приложения,
а свойство быстрого туннеля. Для клиентов используйте варианты 1–3.

---

## Чек-лист перед показом клиенту

- [ ] Проверить `https://<app>/RAG` с телефона на мобильном интернете (не с домашнего Wi-Fi).
- [ ] Прогнать `Contacts`, `Testing`, `Integrations` на английском языке.
- [ ] Убедиться, что в `.env`/секретах нет лишних ключей и что `.env` не в репозитории.
- [ ] Для UA: либо поднять MCP (вариант 2), либо оставить режим «Записанные прогоны» —
      он работает без базы.
