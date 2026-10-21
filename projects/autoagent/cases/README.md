# Cases — три кейса агентов AutoAgent

Реализации трёх сценариев из портфолио (страница Agents). Все кейсы используют
общий LLM-слой `auto_zen.llm` и модели из `.env` (planner / coder / reporter),
ключи в коде не хранятся.

| Кейс | Флоу | Результат |
|---|---|---|
| 1. Research-ассистент | Planner → Web Surfer (DuckDuckGo) + File Surfer (`sources/`) → Compiler | папка `out/research_<ts>/`: `report.md`, `report.docx`, `sources.json`, `sources/` с полными текстами |
| 2. Агент по репозиторию | Planner → Coding Agent (multi-model) → pytest (до 3 итераций) → Reporter | папка `out/repo_run_<ts>/`: `report.md`, логи тестов, `repo_baseline/`, `repo_fixed/` |
| 3. Документы → данные | File Surfer (txt/md/docx/pdf) → извлечение JSON → pandas-валидация | папка `out/docs_run_<ts>/`: CSV, items CSV, сводка, `insert.sql`, копии документов |

**Каждый запуск создаёт одну папку** — всё по этому прогону лежит внутри неё,
искать файлы по разным местам не нужно.

## Запуск

Из корня AutoAgent:

```powershell
python cases/case1_research.py
python cases/case1_research.py "ваш вопрос" --pages 8
python cases/case1_research.py "ваш вопрос" --demo   # без абсолютных путей в выводе (для записи видео)
python cases/case2_repo.py
python cases/case3_docs_to_data.py
```

## Структура

```
cases/
  case1_research.py        # research-ассистент
  case2_repo.py            # агент по репозиторию
  case3_docs_to_data.py    # извлечение данных из документов
  sources/                 # локальная база знаний для File Surfer
  sample_repo/             # демо-репозиторий с багами и тестами
  sample_docs/             # демо-документы (txt + docx)
  out/                     # по одной папке на прогон: research_<ts>/, repo_run_<ts>/, docs_run_<ts>/
```

## Модели по фазам

- Планирование и анализ — `PLANNER_MODEL` (qwen3-235b)
- Правки кода — `CODER_MODEL` (glm-5.2)
- Итоговые отчёты — `REPORTER_MODEL` (glm-4.7-flash)
- Triage/извлечение — `TRIAGE_MODEL` (qwen3-32b)

## Замечания

- Кейс 1 ищет в интернете через HTML-выдачу DuckDuckGo, скачивает страницы и
  ограничивает текст 3500 символами; локальные документы подмешиваются через
  File Surfer (по совпадению ключевых слов).
- Кейс 2 не меняет `sample_repo/`: baseline и правки выполняются в копиях внутри
  папки прогона (`repo_baseline/` и `repo_fixed/`); тесты агенту менять запрещено.
- Кейс 3 не пишет в БД напрямую: генерирует `insert.sql`, который выполняется
  через MCP-инструмент PostgreSQL. Строки с замечаниями (арифметика, дубликаты,
  пропуски) в SQL не попадают.
- В папке прогона кейса 3 лежат копии исходных документов (`documents/`), чтобы
  результат можно было проверить, не возвращаясь в `sample_docs/`.
