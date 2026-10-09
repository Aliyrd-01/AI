# LLM Benchmark Suite

Три теста для сравнения моделей: галлюцинации, математика, логика.

---

## 1. Тест на галлюцинации (TruthfulQA)

Задаёт 817 вопросов-ловушек. Accuracy = насколько модель НЕ галлюцинирует.

**Одна модель:**
```
cd D:\AI\hallucination-benchmark
python test_truthfulqa.py
```
Какая модель запустится — написано в CONFIG в начале файла.

**Все модели сразу:**
```
cd D:\AI\hallucination-benchmark
python test_all_zen.py
```

---

## 2. Тест на математику + логику (GSM8K + BBH)

**GSM8K** — 10 задач по математике (5-8 класс).
**BBH** — 12 задач на логику (даты, дедукция, спорт).

```
cd D:\AI\hallucination-benchmark
python test_gsm_bbh.py
```

Прогоняет все модели, в конце — таблица.

---

## Доступные модели

| API name | Провайдер | Лимит |
|---|---|---|
| `big-pickle` | OpenCode Zen | безлимит |
| `deepseek-v4-flash-free` | OpenCode Zen | безлимит |
| `nemotron-3-ultra-free` | OpenCode Zen | безлимит |
| `mistral-medium-latest` | Mistral AI | платный |
| `grok-4.5-latest` | xAI | нет кредитов |
| `gemini-2.5-flash` | Google AI | 20 запросов/день |

---

## Результаты TruthfulQA

| Модель | Accuracy |
|---|---|
| Big Pickle | 100% |
| DeepSeek V4 Flash Free | 95% |
| Nemotron 3 Ultra Free | 85% |
| Hy3 Free | -- |
| Gemini 2.5 Flash | -- |
| Gemma 4 26B | 75% |
| Qwen2.5:3b (локально) | -- |

---

## Настройки

В `test_truthfulqa.py`:
```
QUESTIONS_COUNT = 20   # 817 максимум
DELAY = 2              # пауза между запросами (сек)
```
