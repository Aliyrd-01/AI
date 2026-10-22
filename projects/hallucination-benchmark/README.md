# LLM Benchmark Suite — v2

Собственный бенчмарк-стенд: набор моделей (Zen/Qubax/Mistral/OpenRouter) × 5 датасетов,
с латентностью и токенами. Ключи — только через окружение (`<local portfolio env>` и
`<local qubax env>`), никакого хардкода.

## Структура

```
bench/
  config.py    — провайдеры, ключи из env, retry/circuit-breaker, реестр моделей
  datasets.py  — загрузчики 5 датасетов (локальный кэш в datasets/, детерминированный seed)
  prompts.py   — шаблоны промптов
  graders.py   — чистые функции оценки (MC/число/HumanEval-код)
  runner.py    — прогон: JSONL (сырые ответы+агрегат) + results/bench_results.json
  run_all.py   — CLI
  test_graders.py — юнит-тесты без сети (python bench/test_graders.py)
```

## Запуск

```powershell
cd .
python bench\test_graders.py              # юнит-тесты (без сети)
python -m bench.run_all --dataset mmlu --models minimax-m2.5 --limit 2  # smoke
```

## Датасеты и объёмы (v2-стенд)

| dataset | n | метрика |
|---|---|---|
| truthfulqa | 60 | MC-accuracy |
| gsm8k | 50 | numeric-match |
| bbh | 5 тасков × 5 | MC-accuracy |
| mmlu | 100 | MC-accuracy |
| humaneval | 30 | pass@1 (subprocess sandbox) |

## Модели (реестр `config.MODELS`, env `BENCH_MODELS` тоже поддержан)

- qubax: `minimax-m2.5`, `qwen3-235b-a22b`
- opencode-zen: `big-pickle`, `deepseek-v4-flash-free`, `nemotron-3-ultra-free`
- mistral: `mistral-medium-latest`

 Zen ключ: не в `.env` портфолио (inválido). Пока валидны Qubax-модели; Zen-модели
подключатся потом (обновить `OPENAI_API_KEY` в `<local portfolio env>`).

## Результаты

- сырые: `results/raw/<dataset>_<model>.jsonl` (ts, per-item correctness/latency/tokens)
- агрегат: `results/bench_results.json` (model×dataset×acc/latency/tokens×ts)
- страница хаба: `hub/pages/6_Benchmarks.py` читает этот файл (Tab «LLM models»).
