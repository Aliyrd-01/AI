# LightRAG — Startup Instructions

LightRAG запущен в **Docker** (контейнер `lightrag-runner`, порт 9621).
Стартует автоматически при загрузке Docker.

## Проверка

```powershell
# Статус контейнера
docker ps | Select-String lightrag

# Health check
curl.exe http://localhost:9621/health
```

Сервер доступен на `http://localhost:9621`.

## Если контейнер не запущен

```powershell
docker start lightrag-runner
```

## Модели

| Модель | Назначение | Бэкенд |
|---|---|---|
| `qwen2.5:1.5b` | LLM для ответов | Ollama |
| `nomic-embed-text` | Embedding для поиска | Ollama |

## Структура

```
D:\AI\GraphRAG_LightRag\lightrag-test\
├── .env              # конфиг (модели, URL)
├── rag_storage/      # векторные индексы
├── inputs/           # исходные документы
└── STARTUP.md        # эта инструкция
```
