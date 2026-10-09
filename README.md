# AI Portfolio Hub

Один проект = один сайт с наработками: **Home · RAG · n8n · Agents · Benchmarks · Projects**.
Streamlit multi-page. Qdrant-индекс в облаке, контейнер тонкий.

## Как запустить

**Локально (двойной клик):**  `start.cmd`  → откроется http://localhost:8501

**Публичная ссылка (двойной клик):**  `start-public.cmd`  → в окне появится `trycloudflare.com`-URL
(нужен `tools/cloudflared.exe`; ПК должен быть включён).

**Docker:**
```powershell
docker compose up --build      # http://localhost:7860
```

**Вручную:**
```powershell
pip install -r requirements.txt
streamlit run hub/Home.py
```

## Структура

```
start.cmd / start-public.cmd     лаунчеры
hub/
  Home.py                        лендинг
  pages/1_RAG.py                 RAG-демо
  pages/2_n8n.py                 3 воркфлоу (диаграммы + видео + JSON)
  pages/3_Projects.py            проекты
  pages/4_Agents.py              AutoAgent + MCP
  pages/5_Benchmarks.py          метрики RAG + LLM Suite
  rag/                           код RAG (retrieval, generation, common)
  eval/                          метрики, eval-скрипты, результаты
  assets/n8n/                    экспорты n8n, видео, скрины
tools/                           публичный запуск (cloudflared) — в git не коммитится
Dockerfile / docker-compose.yml  локально и VPS
Caddyfile                        реверс-прокси + HTTPS (VPS)
```

## Секреты
`.env` (ключи Qdrant/LLM) — не коммитится. Шаблон: `.env.example`.
