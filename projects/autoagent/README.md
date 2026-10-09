# AutoAgent (HKUDS) — запуск через Qubax

Это форк фреймворка **AutoAgent** (HKUDS), настроенный на модель `qwen3-235b-a22b-2507`
через **Qubax API**. Многоагентная система: `System Triage Agent`
маршрутизирует задачу под-агентам (**File Surfer**, **Web Surfer**, **Coding**).

## Быстрый старт

```powershell
auto main
```

Открывается интерактивное меню:

```
Please select the mode:
 > user mode        # многоагентный режим — вводишь задачу
   agent editor     # создание агентов описанием
   workflow editor  # создание workflow описанием
   exit
```

Выбери **user mode** и вводи задачу на естественном языке, например:

```
Tell me what you want to do: проанализируй файл trading_app.py на баги
```

Система сама разобьёт задачу, вызовет нужных под-агентов и вернёт результат.

## Как это работает (как в статье)

1. `System Triage Agent` получает задачу и определяет, какой под-агент нужен
2. Под-агенты выполняют работу (чтение файлов, анализ кода, поиск в вебе)
3. Результат собирается и возвращается пользователю

## Важные настройки (`.env`)

```
OPENAI_API_KEY=...             # ключ Qubax
OPENAI_API_BASE=https://api.qubax.ai/v1
API_BASE_URL=https://api.qubax.ai/v1
COMPLETION_MODEL=qwen3-235b-a22b-2507
FN_CALL=True                   # Qubax-модель поддерживает OpenAI tool-calls
```

Модель переведена с OpenCode Zen (`big-pickle`) на **Qubax** (`qwen3-235b-a22b-2507`).
Проверено: обычный ответ и **tool-calls** работают (был возвращён `get_time`).

### Модели по фазам (multi-model)

`auto_zen.py` выбирает модель под фазу — `ROLE_MODELS` из `.env`:

| Роль | Модель (Qubax) | Фазы |
|---|---|---|
| `triage` | `qwen3-32b` | маршрутизация задачи |
| `planner` | `qwen3-235b-a22b-2507` | планирование, анализ багов |
| `coder` | `glm-5.2` | реализация, фиксы, ревью, тесты |
| `reporter` | `glm-4.7-flash` | отчёты, документация |

Роль определяется по системному промпту (`_infer_role`). Проверено: все 4 роли отвечают.

## Что было восстановлено для запуска на этой машине

В оригинальном чекауте не хватало частей, нужных для `auto main`:

- **`evaluation/`** и **`loop_utils/`** — пакеты, требуемые `autoagent/cli.py`
  (созданы минимальные заглушки, т.к. их нет в этом чекауте)
- Установлены зависимости: `pdfminer.six`, `python-pptx`, `opentelemetry-*`,
  `puremagic`, `pathvalidate`
- В `autoagent/cli.py` исправлено:
  - Agent-Editor импорты сделаны необязательными (т янут тяжёлый `chromadb`)
  - `BrowserEnv` сделан необязательным (нужен Chromium, которого нет)
  - `local_env` по умолчанию `True` (Docker не установлен)
  - добавлена перекодировка stdout в UTF-8 (Windows cp1251)

## Структура

```
D:\AI\AutoAgent\
├── autoagent/           # фреймворк (оригинал HKUDS, с правками)
├── evaluation/          # заглушка (нужна cli.py)
├── loop_utils/          # заглушка (нужна cli.py)
├── .env                 # ключи + FN_CALL=False
├── setup.cfg            # entry point: auto
├── README.md
├── auto_zen.py          # альтернативный CLI (без фреймворка, на httpx)
└── ws/                  # локальное окружение (создаётся при запуске)
```

## Альтернатива: `auto_zen.py`

Если `auto main` по какой-то причине не подходит, `auto_zen.py` — самодостаточный
CLI (httpx → OpenCode Zen, без фреймворка), повторяющий тот же UX:

```powershell
python auto_zen.py main        # меню
python auto_zen.py user "задача"   # разовый запуск
```

> Примечание: `auto_zen.py` — это моя надстройка, НЕ часть фреймворка.
> Основной путь — `auto main` (реальный AutoAgent).
