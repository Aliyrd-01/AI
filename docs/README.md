# AI Portfolio Hub — RAG + n8n

Один проект (Streamlit multi-page), который собирает наработки в один сайт с одной ссылкой:
**Home** (лендинг) · **RAG** (интерактивное демо) · **n8n** (3 воркфлоу) · **Projects** (карточки).

Локально → позже VPS. Qdrant-индекс живёт в Qdrant Cloud; контейнер тонкий (Streamlit + FastEmbed).

## Запуск локально

```powershell
pip install -r requirements.txt
streamlit run hub/Home.py
# http://localhost:8501
```

Публичная ссылка (бесплатно, без аккаунта) — двойной клик:

```
tools\start-hub-public.cmd
```

## Docker

```powershell
docker compose up --build
# http://localhost:7860
```

## VPS (этап позже)

`docker compose` + `Caddyfile` (домен + автоматический HTTPS) впереди контейнера `hub:7860`.

## Структура

```
hub/
  Home.py              лендинг + карточки
  pages/1_RAG.py       RAG-демо (гибридный поиск, цитаты, метрики)
  pages/2_n8n.py       3 воркфлоу: диаграммы из JSON + описания
  pages/3_Projects.py  прочие проекты
  rag/                 код RAG (retrieval, generation, common)
  eval/                метрики, eval-скрипты, результаты
  assets/n8n/          экспорты n8n + ассеты
tools/                 публичный запуск (cloudflared)
```

## n8n-воркфлоу в портфолио

1. **Automated AI Content Publisher** — RSS → LLM → Telegram.
2. **Lead Qualification & Scoring** — webhook → MCP (Postgres CRM) → A/B промптов → CRM.
3. **AI Support & Escalation** — Telegram → LLM-классификатор → оператор.

## Безопасность

- `.env` и `tools/` не коммитятся.
- n8n показывается визуально (диаграмма + JSON), редактор и креды наружу не публикуются.
