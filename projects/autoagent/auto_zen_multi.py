#!/usr/bin/env python3
"""AutoAgent Zen Multi-Model — многоагентная система с оркестрацией.

Использование:
  python auto_zen_multi.py main            # Интерактивное меню
  python auto_zen_multi.py user "запрос"   # Разовый запуск

Особенности:
  - Main Agent (оркестратор) распределяет задачи
  - Sub-agents работают с разными бесплатными моделями
  - Каждая модель оптимальна для своего типа задач
"""

import os, sys, time, json, re, asyncio, glob
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import httpx

# ─── Config ──────────────────────────────────────────────────

# OpenCode Zen
OC_KEY = "REDACTED_KEY"
OC_URL = "https://opencode.ai/zen/v1/chat/completions"

# Mistral API (прямое подключение)
MISTRAL_KEY = "REDACTED_KEY"
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"

# ─── Multi-Model Configuration ───────────────────────────────
# 3 модели: DeepSeek V4 Flash, Big Pickle, Mistral Medium 3.5

MODELS = {
    # DeepSeek V4 Flash — быстрый, хорош для планирования
    "deepseek": {"id": "deepseek-v4-flash-free", "provider": "zen"},
    
    # Big Pickle — мощный, хорош для генерации текста
    "bigpickle": {"id": "big-pickle", "provider": "zen"},
    
    # Mistral Medium 3.5 — прямое подключение к Mistral API
    "mistral": {"id": "mistral-medium-latest", "provider": "mistral"},
}

# Роли агентов и их модели (распределение между 3 моделями)
AGENT_ROLES = {
    "triage": "deepseek",          # Определяет тип задачи
    "planner": "deepseek",         # Разбивает на подзадачи
    "executor": "mistral",         # Выполняет подзадачи (код)
    "reviewer": "mistral",         # Проверяет результат
    "tester": "deepseek",          # Тестирует код
    "reporter": "bigpickle",       # Составляет отчёт
    "bug_analyzer": "mistral",     # Анализирует баги
    "fixer": "mistral",            # Исправляет баги
    "doc_writer": "bigpickle",     # Пишет документацию
    "security": "mistral",         # Проверяет безопасность
    "style": "mistral",            # Проверяет стиль
}

BASE = os.path.dirname(os.path.abspath(__file__))

OUTPUT_DIR = os.path.join(BASE, "Output")
REPORT_DIR = os.path.join(BASE, "Report")
DOCS_DIR = os.path.join(BASE, "Documentation")
FIXED_DIR = os.path.join(BASE, "Fixed")
for d in [OUTPUT_DIR, REPORT_DIR, DOCS_DIR, FIXED_DIR]:
    os.makedirs(d, exist_ok=True)

# ─── LLM Multi-Model ────────────────────────────────────────

def safe(text: str) -> str:
    try:
        return text.encode("cp1251", errors="replace").decode("cp1251")
    except Exception:
        return text

def get_model_for_role(role: str) -> str:
    """Получает модель для роли агента."""
    model_key = AGENT_ROLES.get(role, "mistral")
    model_info = MODELS.get(model_key, MODELS["mistral"])
    return model_info["id"]

def llm(system: str, user: str, temp: float = 0.3, role: str = None, model: str = None) -> str:
    """Вызов LLM с поддержкой разных моделей и провайдеров."""
    if model is None:
        model_key = AGENT_ROLES.get(role, "mistral") if role else "mistral"
        model_info = MODELS.get(model_key, MODELS["mistral"])
    else:
        # Ищем модель по id
        model_info = None
        for v in MODELS.values():
            if v["id"] == model:
                model_info = v
                break
        if not model_info:
            model_info = {"id": model, "provider": "zen"}
    
    model_id = model_info["id"]
    provider = model_info["provider"]
    
    print(safe(f"    (LLM [{model_id}] обрабатывает...)"))
    t0 = time.time()
    
    # Определяем URL и ключ
    if provider == "mistral":
        api_url = MISTRAL_URL
        api_key = MISTRAL_KEY
    else:
        api_url = OC_URL
        api_key = OC_KEY
    
    # Fallback: основная модель, потом другие из我们的 3
    fallback_models = [
        MODELS["bigpickle"],
        MODELS["deepseek"],
        MODELS["mistral"]
    ]
    models_to_try = [model_info] + [m for m in fallback_models if m["id"] != model_id]
    
    for current in models_to_try:
        current_id = current["id"]
        current_provider = current["provider"]
        
        if current_provider == "mistral":
            cur_url = MISTRAL_URL
            cur_key = MISTRAL_KEY
        else:
            cur_url = OC_URL
            cur_key = OC_KEY
        
        for attempt in range(2):
            try:
                r = httpx.post(
                    cur_url,
                    headers={"Authorization": f"Bearer {cur_key}", "Content-Type": "application/json"},
                    json={
                        "model": current_id,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        "temperature": temp,
                        "max_tokens": 4096,
                    },
                    timeout=300,
                )
                elapsed = time.time() - t0
                data = r.json()
                
                if "error" in data:
                    error_msg = data["error"].get("message", str(data["error"]))
                    raise Exception(f"API error: {error_msg}")
                
                if "choices" not in data or not data["choices"]:
                    raise Exception(f"No choices: {str(data)[:100]}")
                
                choice = data["choices"][0]["message"]
                content = choice.get("content")
                reasoning = choice.get("reasoning") or choice.get("reasoning_content")
                
                if not content and reasoning:
                    content = reasoning
                
                if not content:
                    content = choice.get("refusal") or ""
                
                suffix = " [fallback]" if current_id != model_id else ""
                print(safe(f"    (LLM ответил за {elapsed:.0f}s, модель: {current_id}{suffix})"))
                return content
                
            except httpx.TimeoutException:
                print(safe(f"    (Таймаут {attempt+1}/2, модель: {current_id})"))
                if attempt < 1:
                    time.sleep(2)
            except Exception as e:
                print(safe(f"    (Ошибка {attempt+1}/2: {e}, модель: {current_id})"))
                if attempt < 1:
                    time.sleep(2)
    
    return f"[Модель {model_id} не ответила]"

# ─── File helpers ────────────────────────────────────────────

def read_file(path: str) -> str:
    if not os.path.exists(path):
        path = os.path.join(BASE, path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл не найден: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def strip_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
    if t.endswith("```"):
        t = t.rsplit("```", 1)[0]
    return t.strip()

def validate_python(code_str: str):
    import py_compile, tempfile
    tmp = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code_str)
            tmp = f.name
        py_compile.compile(tmp, doraise=True)
        return None
    except py_compile.PyCompileError as e:
        return str(e)
    except Exception as e:
        return str(e)
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except Exception:
                pass

IGNORE_DIRS = {"venv", ".venv", "env", ".env", "node_modules", "__pycache__",
               ".git", ".svn", "venv_", "venv_*", ".mypy_cache", ".pytest_cache",
               "build", "dist", ".egg-info", "htmlcov", ".tox", "rollback", "_rollback"}

def _find_py_files(root: str) -> list[str]:
    result = []
    root = os.path.normpath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d.lower() not in IGNORE_DIRS
                       and not d.lower().startswith("_rollback")
                       and not d.lower().startswith("venv")
                       and not d.startswith(".")]
        for f in filenames:
            if f.endswith(".py"):
                result.append(os.path.join(dirpath, f))
    return sorted(result)

def find_file_in_query(query: str) -> tuple[str, str, str]:
    m = re.search(r'((?:[A-Za-z]:[\\/])?(?:[\w\-]+[\\/])*[\w\-]+\.\w{1,5})', query)
    if m:
        fname = m.group(1)
        try:
            code = read_file(fname)
            query_clean = query.replace(fname, "").strip()
            return query_clean, code, fname
        except FileNotFoundError:
            pass
        except Exception:
            return query, ""
    m = re.search(r'((?:[A-Za-z]:[\\/])(?:[\w\-]+[\\/])*[\w\-]+)', query)
    if m:
        dname = m.group(1)
        if os.path.isdir(dname):
            py_files = sorted(glob.glob(os.path.join(dname, "*.py")))
            if not py_files:
                py_files = sorted(glob.glob(os.path.join(dname, "**", "*.py"), recursive=True))
            if py_files:
                words = [w for w in re.findall(r'\w{4,}', query.lower())]
                matched = [f for f in py_files if any(w in os.path.basename(f).lower() for w in words)]
                fname = (matched or sorted(py_files, key=lambda f: -os.path.getsize(f)))[0]
                try:
                    code = read_file(fname)
                    query_clean = query.replace(dname, "").strip()
                    return query_clean, code, fname
                except Exception:
                    return query, ""
    return query, "", ""

def find_project_in_query(query: str) -> tuple[str, list[tuple[str, str]]]:
    m = re.search(r'((?:[A-Za-z]:[\\/])(?:[\w\-]+[\\/])*[\w\-]+)', query)
    if not m:
        return query, []
    dname = m.group(1)
    if not os.path.isdir(dname):
        return query, []
    py_files = _find_py_files(dname)
    if not py_files:
        print(safe(f"  [WARN] В проекте '{dname}' нет .py файлов."))
        return query, []
    files = []
    for f in py_files:
        try:
            files.append((f, read_file(f)))
        except Exception:
            pass
    query_clean = query.replace(dname, "").strip()
    return query_clean, files

# ─── Triage with Multi-Model ────────────────────────────────

TASK_TYPES = {
    "code_review": "Ревью кода — найти ошибки, проблемы стиля, уязвимости",
    "documentation": "Написание документации к коду",
    "bug_fix": "Исправление багов в коде",
    "research": "Исследование, поиск информации, анализ данных",
    "general": "Общий вопрос, генерация кода, объяснение",
}

def triage_task(query: str, code_hint: bool) -> str:
    """Triage с использованием оркестратора."""
    q = query.lower()
    if any(w in q for w in ["баг", "исправ", "fix", "ошибк", "bug", "почин"]):
        return "bug_fix"
    if any(w in q for w in ["документ", "docs", "опис", "document"]):
        return "documentation"
    if any(w in q for w in ["ревью", "review", "провер", "анализ код", "code review"]):
        return "code_review"
    
    types_desc = "\n".join(f"- {k}: {v}" for k, v in TASK_TYPES.items())
    hint = " (рядом с запросом есть файл с кодом)" if code_hint else ""
    r = llm(
        f"Ты — triage-агент. Определи тип задачи пользователя{hint}.\n"
        f"Доступные типы:\n{types_desc}\n"
        "Ответь ТОЛЬКО одним словом — ключом типа.",
        query,
        temp=0.1,
        role="triage",
    )
    for k in TASK_TYPES:
        if k in r.strip().lower():
            return k
    return "general"

# ─── Multi-Agent Handlers ───────────────────────────────────

async def handle_code_review(query: str, code: str, file_path: str = ""):
    """Code Review — 4 агента с разными моделями."""
    if not code:
        print(safe("  [ERROR] Не указан файл для ревью"))
        return
    base = os.path.basename(file_path) if file_path else "code"
    filename = re.sub(r"[^a-zA-Z0-9_\u0400-\u04FF]", "_", base)
    
    # Параллельный запуск аналитиков
    print(safe("  [1/4] Triage Agent (deepseek-v4-flash-free): анализ кода..."))
    triage = llm("Ты — специалист по code review. Проанализируй код, составь план ревью.",
                 f"Код:\n\n{code[:4000]}", role="triage")
    
    print(safe(f"  [2/4] Style Agent ({get_model_for_role('style')}): проверка стиля..."))
    style = llm("Ты — эксперт по стилю Python (PEP8). Найди проблемы стиля.",
                f"Код:\n\n{code[:4000]}", role="style")
    
    print(safe(f"  [3/4] Security Agent ({get_model_for_role('security')}): проверка безопасности..."))
    security = llm("Ты — специалист по безопасности. Найди уязвимости.",
                   f"Код:\n\n{code[:4000]}", role="security")
    
    print(safe("  [4/4] Reporter (big-pickle): составление отчёта..."))
    report = llm(
        "Ты — составитель отчётов на русском в markdown.",
        f"Файл: {filename}\n\nПлан ревью:\n{triage[:1000]}\n\nСтиль:\n{style[:1000]}\n\nБезопасность:\n{security[:1000]}",
        role="reporter"
    )
    path = os.path.join(REPORT_DIR, f"review_report_{filename}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    print(safe(f"  [Done] Отчёт: {path}"))
    return path

async def handle_documentation(query: str, code: str, file_path: str = ""):
    """Documentation — 3 агента с разными моделями."""
    if not code:
        print(safe("  [ERROR] Не указан файл для документирования"))
        return
    base = os.path.basename(file_path) if file_path else "code"
    filename = re.sub(r"[^a-zA-Z0-9_\u0400-\u04FF]", "_", base)
    
    print(safe("  [1/3] DocPlanner (deepseek-v4-flash-free): структура документации..."))
    plan = llm("Ты — DocPlanner. Составь структуру документации для этого кода.",
               f"Код:\n\n{code[:4000]}", role="planner")
    
    print(safe(f"  [2/3] DocWriter ({get_model_for_role('doc_writer')}): написание документации..."))
    docs = llm("Ты — DocWriter. Напиши документацию на русском в markdown.",
               f"Код:\n\n{code[:4000]}\n\nСтруктура:\n{plan[:1000]}", role="doc_writer")
    
    print(safe(f"  [3/3] DocReviewer ({get_model_for_role('reviewer')}): проверка и финализация..."))
    final = llm("Ты — DocReviewer. Проверь и доработай документацию.",
                f"Документация:\n\n{docs[:4000]}", role="reviewer")
    
    path = os.path.join(DOCS_DIR, f"docs_{filename}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(final)
    print(safe(f"  [Done] Документация: {path}"))
    return path

def _apply_patch(original: str, new_parts: str) -> str:
    lines = original.split("\n")
    new_headers = re.findall(r'^((?:async\s+)?(?:def|class)\s+\w+)', new_parts, re.MULTILINE)
    if not new_headers:
        return original
    for header in new_headers:
        header_stripped = header.strip()
        start_idx = -1
        for i, ln in enumerate(lines):
            if ln.strip().startswith(header_stripped):
                start_idx = i
                break
        if start_idx == -1:
            continue
        base_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
        end_idx = len(lines)
        for j in range(start_idx + 1, len(lines)):
            if lines[j].strip() == "":
                continue
            indent = len(lines[j]) - len(lines[j].lstrip())
            if indent <= base_indent and (lines[j].strip().startswith("def ") or lines[j].strip().startswith("class ") or lines[j].strip().startswith("async ")):
                end_idx = j
                break
            if indent == 0 and base_indent == 0 and lines[j].strip().startswith("@"):
                end_idx = j
                break
        np_lines = new_parts.split("\n")
        np_start = -1
        for k, nl in enumerate(np_lines):
            if nl.strip().startswith(header_stripped):
                np_start = k
                break
        if np_start == -1:
            continue
        np_end = len(np_lines)
        for k in range(np_start + 1, len(np_lines)):
            if np_lines[k].strip() == "":
                continue
            np_indent = len(np_lines[k]) - len(np_lines[k].lstrip())
            if np_indent <= base_indent and (np_lines[k].strip().startswith("def ") or np_lines[k].strip().startswith("class ") or np_lines[k].strip().startswith("async ")):
                np_end = k
                break
        replacement = "\n".join(np_lines[np_start:np_end])
        lines[start_idx:end_idx] = [replacement]
    return "\n".join(lines)

def _extract_relevant_code(code: str, bug_desc: str, max_lines: int = 800) -> str:
    lines = code.split("\n")
    names = re.findall(r'(?:функци[яи]|def|class|метод[а]?)\s+(\w+)', bug_desc, re.IGNORECASE)
    if not names:
        names = re.findall(r'\b(normalize_symbol|known_quotes)\b', bug_desc, re.IGNORECASE)
    if not names:
        return "\n".join(lines[:max_lines]) + "\n# ... (обрезано)"
    result_lines = []
    seen_ranges = set()
    for name in set(names):
        for i, ln in enumerate(lines):
            if re.match(rf'\s*(?:async\s+)?def\s+{re.escape(name)}\s*\(', ln) or \
               re.match(rf'\s*class\s+{re.escape(name)}\s*[:\(]', ln):
                start = max(0, i - 3)
                j = i + 1
                depth = 0
                while j < len(lines):
                    stripped = lines[j].strip()
                    if stripped == "":
                        j += 1
                        continue
                    indent = len(lines[j]) - len(lines[j].lstrip())
                    if indent == 0 and depth == 0 and (stripped.startswith("def ") or stripped.startswith("class ") or stripped.startswith("async ") or stripped.startswith("@") and not ln.strip().startswith("@")):
                        break
                    if stripped.startswith("def ") or stripped.startswith("class ") or stripped.startswith("async "):
                        if indent <= len(lines[i]) - len(lines[i].lstrip()):
                            break
                    j += 1
                end = min(len(lines), j + 2)
                rng = (start, end)
                if rng not in seen_ranges:
                    seen_ranges.add(rng)
                    result_lines.append(f"# --- {name} (строки {start+1}-{end}) ---")
                    result_lines.extend(lines[start:end])
                    result_lines.append("")
    if not result_lines:
        return "\n".join(lines[:max_lines]) + "\n# ... (обрезано)"
    return "\n".join(result_lines)

async def handle_bug_fix(query: str, code: str, file_path: str = "", interactive: bool = True):
    """Bug Fix — интерактивный с multi-model оркестрацией."""
    if not code:
        print(safe("  [ERROR] Не указан файл для исправления"))
        return
    base = os.path.basename(file_path) if file_path else "code"
    slug = re.sub(r"[^a-zA-Z0-9_\u0400-\u04FF]", "_", base)
    lines_total = len(code.split("\n"))
    
    # ─── ШАГ 0: Оркестратор планирует ───
    print(safe(f"  [0/4] Orchestrator ({get_model_for_role('planner')}): планирование..."))
    plan = llm(
        "Ты — оркестратор. Определи стратегию анализа кода:\n"
        "1. Какие участки кода потенциально проблемные\n"
        "2. На что обратить внимание в первую очередь\n"
        "3. Какие типы багов искать\n"
        "Ответь кратко.",
        f"Файл: {base} ({lines_total} строк)\n\nКод:\n{code[:3000]}",
        role="planner",
    )
    print(safe(f"  Стратегия: {plan[:200]}...\n"))
    
    # ─── ШАГ 1: Анализ багов ───
    print(safe(f"  [1/4] BugAnalyzer ({get_model_for_role('bug_analyzer')}): поиск багов..."))
    code_snippet = code if lines_total <= 2000 else "\n".join(code.split("\n")[:2000]) + "\n# ... (обрезано)"
    analysis = llm(
        "Ты — BugAnalyzer. Найди ВСЕ баги в коде. Верни нумерованный список "
        "(1. ... 2. ...), каждый баг с кратким описанием и локацией в коде.",
        f"Код:\n\n{code_snippet}",
        role="bug_analyzer"
    )
    print(safe("\n--- СПИСОК БАГОВ ---\n"))
    print(safe(analysis))
    print(safe("\n--------------------\n"))

    if interactive:
        sel = input(safe("  Какие баги исправить? (напр. '1,3,5' / 'all' / 'exit'): ")).strip()
        if sel.lower() in ("exit", "quit", "q"):
            print(safe("  [Отмена] Возврат в меню."))
            return
        if sel.lower() == "all":
            selected = analysis
        else:
            nums = [int(n) for n in re.findall(r"\d+", sel)]
            selected_lines = []
            for line in analysis.split("\n"):
                for n in nums:
                    if re.match(rf"\s*{n}[\.\)]", line):
                        selected_lines.append(line)
                        break
            selected = "\n".join(selected_lines) if selected_lines else analysis
    else:
        selected = analysis

    relevant_code = _extract_relevant_code(code, selected)
    print(safe(f"  (код файла: {lines_total} строк, отправлено Fixer: {len(relevant_code.split(chr(10)))} строк)"))

    fixed_relevant = ""
    last_feedback = ""
    status = "FAILED"
    test_result = ""

    for attempt in range(3):
        print(safe(f"  [2/4] Fixer ({get_model_for_role('fixer')}): попытка {attempt+1}/3..."))
        if last_feedback:
            fix_prompt = (
                "Ты — Fixer. Верни ТОЛЬКО исправленные функции/классы (целиком, без сокращений). "
                f"Твой предыдущий fix НЕ УСТРАНИЛ баги. Вот замечания тестера:\n{last_feedback}\n\n"
                "Верни исправленный код этих функций. Только код, без пояснений и без markdown-фенсов."
            )
        else:
            fix_prompt = (
                "Ты — Fixer. Верни ТОЛЬКО исправленные функции/классы (целиком, без сокращений). "
                "Устрани указанные баги. Только код, без пояснений и без markdown-фенсов."
            )
        fixed_relevant = llm(fix_prompt, f"Исходные функции/классы:\n{relevant_code}\n\nИсправить баги:\n{selected}",
                            role="fixer")
        fixed_relevant = strip_code_fences(fixed_relevant)

        patched = _apply_patch(code, fixed_relevant)
        err = validate_python(patched)
        if err:
            print(safe(f"  [Fixer] Патч не компилируется: {err[:200]}"))
            last_feedback = f"Patch SyntaxError: {err}"
            if attempt == 2:
                status = "SYNTAX_ERROR"
                test_result = last_feedback
            continue

        print(safe(f"  [3/4] Tester ({get_model_for_role('tester')}): проверка попытки {attempt+1}/3..."))
        test_result = llm(
            "Ты — Tester. Проверь исправленный код. Ответь строго с новой строки:\n"
            "Строка 1: 'OK' если все выбранные баги устранены, или 'FAIL: <причина>' если нет.\n"
            "Строка 2 и далее: подробное объяснение, что именно не исправлено, если FAIL.",
            f"Выбранные баги:\n{selected}\n\nИзменённый код:\n{fixed_relevant[:3000]}\n\nРезультат склейки (первые/последние 50 строк):\n"
            f"{chr(10).join(patched.split(chr(10))[:50])}\n...\n{chr(10).join(patched.split(chr(10))[-50:])}",
            role="tester"
        )
        verdict = test_result.strip().split("\n", 1)[0].strip()
        if verdict.upper().startswith("OK"):
            status = "OK"
            break
        else:
            last_feedback = test_result
            status = "FAILED"
            print(safe(f"  [Tester] Баги ещё не исправлены. Повтор..."))

    print(safe("  [4/4] Reporter (big-pickle): отчёт..."))
    report = llm(
        "Ты — Reporter на русском. Составь отчёт: какие баги выбраны → что исправлено → "
        f"{'все исправлено' if status == 'OK' else 'проблемы остались'} → результат проверки.",
        f"Выбранные баги:\n{selected[:1000]}\n\n"
        f"Статус: {status}\n\n"
        f"Результат теста:\n{test_result[:1500]}",
        role="reporter"
    )
    fixed_path = os.path.join(FIXED_DIR, f"{slug}_fixed.py")
    with open(fixed_path, "w", encoding="utf-8") as f:
        f.write(patched if status == "OK" else fixed_relevant)
    report_path = os.path.join(FIXED_DIR, f"fix_report_{slug}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(safe(f"  [Done] Исправленный файл: {fixed_path}"))
    print(safe(f"  [Done] Отчёт: {report_path}"))
    return report_path

async def handle_project_bug_fix(query: str, files: list[tuple[str, str]], interactive: bool = True):
    """Bug Fix для всего проекта с multi-model оркестрацией."""
    if not files:
        print(safe("  [ERROR] Нет файлов для анализа"))
        return

    # ─── ШАГ 0: Оркестратор планирует ───
    print(safe(f"  [0/4] Orchestrator ({get_model_for_role('planner')}): планирование..."))
    file_list = "\n".join(f"  - {os.path.basename(f)} ({len(c.split(chr(10)))} строк)" for f, c in files[:20])
    plan = llm(
        "Ты — оркестратор. Проанализируй список файлов проекта и определи:\n"
        "1. Какие файлы потенциально содержат баги (по названию/структуре)\n"
        "2. Приоритет анализа (важные файлы first)\n"
        "3. Сколько файлов нужно проанализировать\n"
        "Ответь кратко: список приоритетных файлов и порядок анализа.",
        f"Задача: {query}\n\nФайлы проекта ({len(files)} шт):\n{file_list}",
        role="planner",
    )
    print(safe(f"  План: {plan[:200]}...\n"))

    # ─── ШАГ 1: Анализ багов ───
    print(safe(f"  [1/4] BugAnalyzer ({get_model_for_role('bug_analyzer')}): анализ {len(files)} файлов проекта..."))
    all_bugs = {}
    for fpath, fcode in files:
        short = os.path.basename(fpath)
        lines_total = len(fcode.split("\n"))
        code_snippet = fcode if lines_total <= 2000 else "\n".join(fcode.split("\n")[:2000]) + "\n# ... (обрезано)"
        print(safe(f"    -> {short} ({lines_total} строк)"))
        analysis = llm(
            "Ты — BugAnalyzer. Найди ВСЕ баги в коде. Верни нумерованный список "
            "(1. ... 2. ...), каждый баг с кратким описанием и локацией в коде.",
            f"Код:\n\n{code_snippet}",
            role="bug_analyzer"
        )
        if analysis.strip():
            all_bugs[short] = {"path": fpath, "code": fcode, "analysis": analysis}

    if not all_bugs:
        print(safe("  Багов не найдено."))
        return

    print(safe(f"\n--- СПИСОК БАГОВ ПО ФАЙЛАМ ---\n"))
    combined_list = []
    idx = 1
    for fname, data in all_bugs.items():
        print(safe(f"\n  [{fname}]"))
        for line in data["analysis"].strip().split("\n"):
            print(safe(f"    {line}"))
            combined_list.append((idx, fname, line))
            idx += 1
    print(safe(f"\n------------------------------\n"))

    if interactive:
        sel = input(safe("  Какие баги исправить? (напр. '1,3,5' / 'all' / 'exit'): ")).strip()
        if sel.lower() in ("exit", "quit", "q"):
            print(safe("  [Отмена] Возврат в меню."))
            return
    else:
        sel = "all"

    selected_nums = {int(n) for n in re.findall(r"\d+", sel)} if sel.lower() != "all" else "all"
    files_to_fix = {}
    for i, fname, bug_line in combined_list:
        if selected_nums == "all" or i in selected_nums:
            if fname not in files_to_fix:
                d = all_bugs[fname]
                files_to_fix[fname] = {"path": d["path"], "code": d["code"], "bugs": []}
            files_to_fix[fname]["bugs"].append(bug_line)

    print(safe(f"\n  Выбрано багов для исправления: {sum(len(v['bugs']) for v in files_to_fix.values())} "
               f"в {len(files_to_fix)} файлах\n"))

    fixed_files = {}
    for fname, data in files_to_fix.items():
        print(safe(f"\n  --- {fname} ---"))
        code = data["code"]
        selected = "\n".join(data["bugs"])
        relevant_code = _extract_relevant_code(code, selected)

        fixed_relevant = ""
        last_feedback = ""
        status = "FAILED"
        test_result = ""

        for attempt in range(3):
            print(safe(f"  Fixer ({get_model_for_role('fixer')}): попытка {attempt+1}/3..."))
            if last_feedback:
                fix_prompt = (
                    "Ты — Fixer. Верни ТОЛЬКО исправленные функции/классы (целиком). "
                    f"Твой предыдущий fix НЕ УСТРАНИЛ баги. Замечания:\n{last_feedback}\n"
                    "Верни исправленный код. Только код, без пояснений."
                )
            else:
                fix_prompt = (
                    "Ты — Fixer. Верни ТОЛЬКО исправленные функции/классы (целиком). "
                    "Устрани указанные баги. Только код, без пояснений."
                )
            fixed_relevant = llm(fix_prompt, f"Исходный код:\n{relevant_code}\n\nИсправить:\n{selected}",
                                role="fixer")
            fixed_relevant = strip_code_fences(fixed_relevant)
            patched = _apply_patch(code, fixed_relevant)
            err = validate_python(patched)
            if err:
                print(safe(f"  [Fixer] Патч не компилируется: {err[:200]}"))
                last_feedback = f"SyntaxError: {err}"
                if attempt == 2:
                    status = "SYNTAX_ERROR"
                    test_result = last_feedback
                continue

            print(safe(f"  Tester ({get_model_for_role('tester')}): проверка..."))
            test_result = llm(
                "Ты — Tester. Ответь строго с новой строки:\n"
                "Строка 1: 'OK' если баги устранены, или 'FAIL: <причина>' если нет.\n"
                "Строка 2+: подробности.",
                f"Баги:\n{selected}\n\nИзменённый код:\n{fixed_relevant[:3000]}",
                role="tester"
            )
            verdict = test_result.strip().split("\n", 1)[0].strip()
            if verdict.upper().startswith("OK"):
                status = "OK"
                break
            else:
                last_feedback = test_result
                status = "FAILED"

        fixed_files[fname] = {"path": data["path"], "patched": patched,
                               "status": status, "test": test_result}

    print(safe("\n  [4/4] Reporter (big-pickle): итоговый отчёт..."))
    summary = "\n".join(
        f"- {f}: {v['status']}" for f, v in fixed_files.items()
    )
    report = llm(
        "Ты — Reporter на русском. Составь отчёт по исправлению багов в проекте:\n"
        "какие файлы затронуты → какие баги исправлены → статус.",
        f"Файлы:\n{summary}\n\nДетали:\n" +
        "\n".join(f"--- {f} ---\nСтатус: {v['status']}\nТест: {v['test'][:500]}"
                  for f, v in fixed_files.items()),
        role="reporter"
    )
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(FIXED_DIR, f"project_fix_report_{ts}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(safe(f"\n  [Done] Отчёт: {report_path}"))
    for fname, data in fixed_files.items():
        out = os.path.join(FIXED_DIR, f"{os.path.splitext(fname)[0]}_fixed.py")
        with open(out, "w", encoding="utf-8") as f:
            f.write(data["patched"])
        print(safe(f"  [Done] {fname} -> {out}"))
    return report_path

async def handle_research(query: str, code: str = ""):
    """Исследование/анализ — многоагентный режим с разными моделями."""
    context = f"\nКонтекст (код):\n{code[:2000]}" if code else ""
    
    print(safe("  [1/3] Planner (deepseek-v4-flash-free): разбиваю на подзадачи..."))
    plan = llm(
        "Ты — Planner. Разбей задачу на 2-4 конкретные подзадачи. "
        "Ответь строго списком, каждая строка с '-'.",
        f"{query}{context}",
        temp=0.4,
        role="planner",
    )
    tasks = [t.strip().lstrip("- ").strip() for t in plan.split("\n") if t.strip().startswith("-")]
    if not tasks:
        tasks = [query]
    print(safe(f"    Разбито на {len(tasks)} подзадач"))
    
    results = []
    print(safe("  [2/3] Executor (mistral): выполняю подзадачи..."))
    for i, task in enumerate(tasks):
        print(safe(f"    [{i+1}/{len(tasks)}] {task[:120]}"))
        r = llm(
            "Ты — эксперт, выполняющий подзадачу. Ответь подробно и структурированно. На русском.",
            f"Подзадача: {task}\n\nКонтекст: {query}{context}",
            temp=0.3,
            role="executor",
        )
        results.append({"task": task, "result": r})
        print(safe(f"      -> {len(r)} chars"))
    
    print(safe("  [3/3] Compiler (big-pickle): собираю итоговый ответ..."))
    combined = "\n\n".join(
        f"### Подзадача: {r['task']}\n{r['result']}" for r in results
    )
    final = llm(
        "Ты — составитель отчётов. Объедини результаты в один связный ответ на русском в markdown.",
        combined,
        temp=0.3,
        role="reporter",
    )
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^a-zA-Z0-9_\u0400-\u04FF]", "_", query[:40])
    path = os.path.join(OUTPUT_DIR, f"result_{slug}_{ts}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(final)
    print(safe(f"  [Done] Результат: {path}"))
    return path

# ─── Run ─────────────────────────────────────────────────────

async def run_query(query: str, interactive: bool = False) -> str:
    t0 = time.time()
    print(safe(f"\n{'='*60}"))
    print(safe(f"  {query[:300]}"))
    print(safe(f"{'='*60}"))

    query_clean, files = find_project_in_query(query)
    code, file_path = "", ""
    is_project = len(files) > 1
    if is_project:
        print(safe(f"  [Project] Найдено {len(files)} .py файлов"))
    else:
        query_clean, code, file_path = find_file_in_query(query)

    task_type = triage_task(query_clean, len(files) > 0 or bool(code))
    type_name = TASK_TYPES.get(task_type, task_type)
    print(safe(f"  [Triage] Тип задачи: {type_name}\n"))

    if task_type == "bug_fix" and is_project:
        result = await handle_project_bug_fix(query_clean, files, interactive)
    elif task_type == "code_review":
        result = await handle_code_review(query_clean, code, file_path)
    elif task_type == "documentation":
        result = await handle_documentation(query_clean, code, file_path)
    elif task_type == "bug_fix":
        result = await handle_bug_fix(query_clean, code, file_path, interactive)
    else:
        result = await handle_research(query_clean, code)
    elapsed = time.time() - t0
    print(safe(f"\n  [Done] {elapsed:.0f}s"))
    return result

# ─── Interactive ─────────────────────────────────────────────

async def user_mode_loop():
    print(safe("\n  === User Mode (Multi-Model) ==="))
    print(safe("  Введи задачу на естественном языке (или 'exit')."))
    print(safe("  Система сама определит тип задачи и распределит по моделям."))
    print(safe("  Модели:"))
    for role, model in MODELS.items():
        print(safe(f"    {role}: {model}"))
    print(safe("\n  Примеры:"))
    print(safe("    'Проверь код в test_sample.py' — code review"))
    print(safe("    'Напиши документацию для buggy_sample.py' — docs"))
    print(safe("    'Исправь баги в test_sample.py' — bug fix"))
    print(safe("    'Что нового в AI в 2026?' — исследование\n"))
    while True:
        try:
            query = input(safe("  > ")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if query.lower() in ("exit", "quit", "q"):
            break
        if not query:
            continue
        await run_query(query, interactive=True)

async def agent_editor_loop():
    print(safe("\n  === Agent Editor ==="))
    print(safe("  Опиши агента на естественном языке."))
    print(safe("  Например: 'Создай агента для анализа логов на Python'"))
    print(safe("  (или 'exit')\n"))
    while True:
        desc = input(safe("  > ")).strip()
        if desc.lower() in ("exit", "quit", "q"):
            break
        print(safe("    Генерирую агента..."))
        name = llm(
            "Придумай короткое имя агента (2-3 слова на англ) по описанию. Только имя.",
            desc, temp=0.2, role="orchestrator",
        ).strip()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(OUTPUT_DIR, f"agent_{name.replace(' ', '_')}_{ts}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"name": name, "description": desc, "created": ts},
                      f, ensure_ascii=False, indent=2)
        print(safe(f"  [OK] Агент '{name}' создан -> {path}\n"))

async def workflow_editor_loop():
    print(safe("\n  === Workflow Editor ==="))
    print(safe("  Опиши workflow на естественном языке."))
    print(safe("  Например: 'Сначала найди информацию, потом проанализируй, затем составь отчёт'"))
    print(safe("  (или 'exit')\n"))
    while True:
        desc = input(safe("  > ")).strip()
        if desc.lower() in ("exit", "quit", "q"):
            break
        print(safe("    Генерирую workflow..."))
        name = llm(
            "Придумай короткое имя workflow (2-3 слова на англ) по описанию. Только имя.",
            desc, temp=0.2, role="orchestrator",
        ).strip()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(OUTPUT_DIR, f"workflow_{name.replace(' ', '_')}_{ts}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"name": name, "description": desc, "created": ts},
                      f, ensure_ascii=False, indent=2)
        print(safe(f"  [OK] Workflow '{name}' создан -> {path}\n"))

# ─── Menu ───────────────────────────────────────────────────

BANNER = r"""
   ___        __        ___                  ___
  / _ \      / /       / _ \       ____     / _ \
 / // / __  / /   __  / // / __   / __ \   / // /
/ // / / / / /   / / / // / / /  / /_/ /  / // /
\___/ /_/ /_/   /_/ /___/ /_/   \____/  /___/
  OpenCode Zen  |  Multi-Model Orchestration
"""

async def main_menu():
    print(safe(BANNER))
    print(safe("  Multi-Model Configuration:"))
    for role, model in MODELS.items():
        print(safe(f"    {role}: {model}"))
    print(safe(f"\n  API: OpenCode Zen\n"))
    while True:
        print(safe("  Выбери режим:"))
        print(safe("    1 — User Mode (многоагентный режим)"))
        print(safe("    2 — Agent Editor (создание агентов)"))
        print(safe("    3 — Workflow Editor (создание workflow)"))
        print(safe("    4 — Exit\n"))
        try:
            choice = input(safe("  > ")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if choice in ("1", "user", "user mode"):
            await user_mode_loop()
        elif choice in ("2", "agent", "agent editor"):
            await agent_editor_loop()
        elif choice in ("3", "workflow", "workflow editor"):
            await workflow_editor_loop()
        elif choice in ("4", "exit", "quit", "q"):
            print(safe("\n  Goodbye!\n"))
            break
        else:
            print(safe("  Неверный выбор. Попробуй 1-4.\n"))

def main():
    import argparse
    p = argparse.ArgumentParser(description="AutoAgent Zen Multi-Model CLI")
    p.add_argument("mode", nargs="?", default="main",
                   help="main | user 'запрос'")
    p.add_argument("query", nargs="*", help="запрос для user mode")
    args = p.parse_args()
    if args.mode == "main":
        try:
            asyncio.run(main_menu())
        except KeyboardInterrupt:
            print()
    elif args.mode == "user":
        query = " ".join(args.query) if args.query else input("> ")
        try:
            asyncio.run(run_query(query))
        except KeyboardInterrupt:
            print()
    else:
        print(safe(f"Неизвестный режим: {args.mode}"))

if __name__ == "__main__":
    main()
