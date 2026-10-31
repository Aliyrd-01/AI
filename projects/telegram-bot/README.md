# 🤖 Telegram RAG Support & Lead-Generation Bot

Телеграм-бот с интеграцией в локальный RAG-движок (LightRAG) и воронку обработки лидов через n8n и PostgreSQL CRM.

## 🌟 Возможности

1. **RAG Q&A**: Ответы на вопросы пользователей по внутренней документации компании с цитированием первоисточников.
2. **Lead Form WebApp**: Встроенная HTML5-форма (`lead_form.html`) для сбора квалификационных данных о потенциальном клиенте.
3. **Escalation**: Автоматическая эскалация сложных запросов операторам через n8n webhook workflow (`telegram-lightrag-workflow.json`).

## 📁 Структура

```
projects/telegram-bot/
├── tg_lightrag_bot.py                 # Основной сервис бота (long-polling)
├── lead_form.html                     # WebApp форма квалификации лида
├── telegram-lightrag-workflow.json    # Сценарий автоматизации в n8n
└── README.md                          # Документация проекта
```

## 🚀 Запуск бота

```powershell
# Установка токена бота
$env:TELEGRAM_BOT_TOKEN = "your_bot_token"
$env:LIGHTRAG_URL = "http://localhost:9621/query"

# Запуск
python tg_lightrag_bot.py
```
