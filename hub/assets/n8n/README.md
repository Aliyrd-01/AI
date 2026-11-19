# n8n workflow exports

Готовые к импорту workflow: `ai_support_escalation.json`, `lead_qualification.json`,
`news_content_publisher.json`.

Экспорты намеренно **не активны** (`"active": false`) и не содержат чужих
credential ID — после импорта вы сами выбираете подключения и включаете workflow.

## Переменные окружения n8n

| Переменная | Где используется | Обязательна |
|---|---|---|
| `TELEGRAM_OPERATOR_CHAT_ID` | пересылка алертов оператору, проверка «это оператор?» | да (support, lead) |
| `RAG_API_URL` | запрос к RAG API (по умолчанию `http://localhost:8000`) | нет |

Нода `AI Response` обращается к `{{ $env.RAG_API_URL }}/query`. Если сервер
поднят локально, переменную можно не задавать — используется localhost.

## Какие подключения нужно создать после импорта

| Тип credential | Workflow |
|---|---|
| Telegram API (bot token) | все три |
| PostgreSQL | все три |
| OpenAI API (или совместимый endpoint) | support |
| Header Auth (LLM API A/B, Translate) | lead, news |
| Query Auth (SerpAPI image search) | news |
| Basic Auth (webhook) | lead |

## Порядок импорта

1. n8n → *Workflows* → *Import from file* → выберите JSON.
2. Откройте каждую ноду с ключом и выберите **своё** credential.
3. Задайте `TELEGRAM_OPERATOR_CHAT_ID` (и при необходимости `RAG_API_URL`) в
   настройках окружения n8n.
4. Включите workflow переключателем *Active*.
