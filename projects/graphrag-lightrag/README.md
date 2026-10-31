# 🕸️ GraphRAG & LightRAG Knowledge Graph Service

Интеграция графового RAG на базе **LightRAG** для обработки сложной взаимосвязанной документации и извлечения сущностей и отношений (Entity-Relation Extraction).

## 🚀 Архитектура и стек

- **Движок**: LightRAG (Docker-контейнер `lightrag-runner`, порт `9621`)
- **LLM**: Qwen 2.5 (1.5B / 7B) через локальный Ollama
- **Embeddings**: Nomic-Embed-Text
- **Хранилище графа**: NetworkX / NanoVectorDB / Qdrant
- **Режимы поиска**:
  - `local`: поиск по контекстным сущностям
  - `global`: глобальный синтез по всему графу знаний
  - `mix`: гибридный поиск (local + global + vector)

## 📁 Структура

```
projects/graphrag-lightrag/
├── STARTUP.md       # Инструкции по управлению Docker-контейнером
├── inputs/          # Папка для автоматической индексации документов
├── rag01-10.docx    # Исходная база знаний
└── README.md        # Этот файл
```

## 🛠️ Запуск и проверка

```powershell
# Запуск контейнера
docker start lightrag-runner

# Проверка health
curl.exe http://localhost:9621/health

# Пример запроса через API
curl.exe -X POST http://localhost:9621/query `
  -H "Content-Type: application/json" `
  -d '{"query": "Основные архитектурные компоненты системы", "mode": "mix"}'
```
