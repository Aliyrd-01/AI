#!/usr/bin/env python3
"""AutoAgent Zen — многоагентная система на естественном языке.

Использование:
  auto-zen main            # Интерактивное меню
  auto-zen user "запрос"   # Разовый запуск

Принцип (как в статье):
  1. Пользователь вводит задачу на естественном языке
  2. Triage Agent определяет тип задачи
  3. Planner разбивает на подзадачи
  4. Executor выполняет каждую подзадачу
  5. Compiler собирает итоговый отчёт
"""

import os, sys, time, json, re, asyncio, glob
from datetime import datetime
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import httpx

# ─── Config ──────────────────────────────────────────────────

BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE, ".env"), override=True)

# Provider: Qubax (OpenAI-compatible), configured via .env.
OC_KEY = os.getenv("OPENAI_API_KEY", "")
_BASE_URL = os.getenv("API_BASE_URL") or os.getenv("OPENAI_API_BASE", "https://api.qubax.ai/v1")
OC_URL = _BASE_URL.rstrip("/") + "/chat/completions"
MODEL = os.getenv("COMPLETION_MODEL", "qwen3-235b-a22b-2507")

# Per-phase models (multi-model orchestration). Each falls back to MODEL.
ROLE_MODELS = {
    "triage":   os.getenv("TRIAGE_MODEL", MODEL),
    "planner":  os.getenv("PLANNER_MODEL", MODEL),
    "coder":    os.getenv("CODER_MODEL", MODEL),
    "reporter": os.getenv("REPORTER_MODEL", MODEL),
}


def _infer_role(system: str) -> str:
    """Map a phase to a model role from its system prompt."""
    s = (system or "").lower()
    if "triage" in s:
        return "triage"
    if any(k in s for k in ("planner", "buganalyzer", "разбей задачу")):
        return "planner"
    if any(k in s for k in ("reporter", "docwriter", "docreviewer", "составитель отчёт", "составитель отчет", "напиши документацию")):
        return "reporter"
    if any(k in s for k in ("fixer", "tester", "code review", "pep8", "безопасн", "уязвим", "эксперт, выполняющий")):
        return "coder"
    return "general"

OUTPUT_DIR = os.path.join(BASE, "Output")
REPORT_DIR = os.path.join(BASE, "Report")
DOCS_DIR = os.path.join(BASE, "Documentation")
FIXED_DIR = os.path.join(BASE, "Fixed")
for d in [OUTPUT_DIR, REPORT_DIR, DOCS_DIR, FIXED_DIR]:
    os.makedirs(d, exist_ok=True)

# ─── LLM ─────────────────────────────────────────────────────

def safe(text: str) -> str:
    try:
        return text.encode("cp1251", errors="replace").decode("cp1251")
    except Exception:
        return text

def llm(system: str, user: str, temp: float = 0.3, role: str | None = None) -> str:
    role = role or _infer_role(system)
    model = ROLE_MODELS.get(role, MODEL)
    print(safe(f"    (LLM[{role}:{model}] обрабатывает...)"))
    t0 = time.time()
    for attempt in range(3):
        try:
            r = httpx.post(
                OC_URL,
                headers={"Authorization": f"Bearer {OC_KEY}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temp,
                },
                timeout=600,
            )
            elapsed = time.time() - t0
            print(safe(f"    (LLM[{role}] ответил за {elapsed:.0f}s)"))
            return r.json()["choices"][0]["message"]["content"]
        except httpx.TimeoutException:
            elapsed = time.time() - t0
            print(safe(f"    (Таймаут {attempt+1}/3 на {elapsed:.0f}s)"))
            if attempt < 2:
                time.sleep(3)
            else:
                raise
        except Exception as e:
            elapsed = time.time() - t0
            print(safe(f"    (Ошибка {attempt+1}/3: {e})"))
            if attempt < 2:
                time.sleep(2)
            else:
                raise

# ─── File helpers ────────────────────────────────────────────

def read_file(path: str) -> str:
    if not os.path.exists(path):
        # try relative to BASE
        path = os.path.join(BASE, path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл не найден: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def strip_code_fences(text: str) -> str:
    """Убирает обёртку ```python ... ``` если LLM вернул код в фенсе."""
    t = text.strip()
    if t.startswith("```"):
        # убираем первую строку (```python)
        t = t.split("\n", 1)[1] if "\n" in t else t
    if t.endswith("```"):
        t = t.rsplit("```", 1)[0]
    return t.strip()

def validate_python(code_str: str):
    """Возвращает текст ошибки или None, если код валиден."""
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
    """Рекурсивно ищет .py файлы в директории, исключая мусор."""
    result = []
    root = os.path.normpath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        # Исключаем служебные папки
        dirnames[:] = [d for d in dirnames if d.lower() not in IGNORE_DIRS
                       and not d.lower().startswith("_rollback")
                       and not d.lower().startswith("venv")
                       and not d.startswith(".")]
        for f in filenames:
            if f.endswith(".py"):
                result.append(os.path.join(dirpath, f))
    return sorted(result)

def find_file_in_query(query: str) -> tuple[str, str, str]:
    """Ищет путь к файлу в запросе.
    Возвращает (очищенный_запрос, содержимое_файла, путь_к_файлу)."""
    # Сначала ищем файл с расширением
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
    # Ищем директорию (путь без расширения)
    m = re.search(r'((?:[A-Za-z]:[\\/])(?:[\w\-]+[\\/])*[\w\-]+)', query)
    if m:
        dname = m.group(1)
        if os.path.isdir(dname):
            py_files = sorted(glob.glob(os.path.join(dname, "*.py")))
            if not py_files:
                py_files = sorted(glob.glob(os.path.join(dname, "**", "*.py"), recursive=True))
            if py_files:
                # Ищем файл по ключевым словам из запроса (≥4 символа), потом самый большой
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
    """Ищет ВСЕ .py файлы проекта в запросе.
    Возвращает (очищенный_запрос, список (путь, содержимое))."""
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

# ─── Triage ──────────────────────────────────────────────────

TASK_TYPES = {
    "code_review": "Ревью кода — найти ошибки, проблемы стиля, уязвимости",
    "documentation": "Написание документации к коду",
    "bug_fix": "Исправление багов в коде",
    "research": "Исследование, поиск информации, анализ данных",
    "general": "Общий вопрос, генерация кода, объяснение",
}

def triage_task(query: str, code_hint: bool) -> str:
    q = query.lower()
    # Приоритет ключевых слов (точнее LLM, быстрее)
    if any(w in q for w in ["баг", "исправ", "fix", "ошибк", "bug", "почин"]):
        return "bug_fix"
    if any(w in q for w in ["документ", "docs", "опис", "document"]):
        return "documentation"
    if any(w in q for w in ["ревью", "review", "провер", "анализ код", "code review"]):
        return "code_review"
    # LLM-фоллбэк
    types_desc = "\n".join(f"- {k}: {v}" for k, v in TASK_TYPES.items())
    hint = " (рядом с запросом есть файл с кодом)" if code_hint else ""
    r = llm(
        f"Ты — triage-агент. Определи тип задачи пользователя{hint}.\n"
        f"Доступные типы:\n{types_desc}\n"
        "Ответь ТОЛЬКО одним словом — ключом типа.",
        query,
        temp=0.1,
    )
    for k in TASK_TYPES:
        if k in r.strip().lower():
            return k
    return "general"

# ─── Dispatcher ──────────────────────────────────────────────

async def handle_code_review(query: str, code: str, file_path: str = ""):
    """Code Review — 4 агента (как в статье: ревью кода)."""
    if not code:
        print(safe("  [ERROR] Не указан файл для ревью"))
        return
    base = os.path.basename(file_path) if file_path else "code"
    filename = re.sub(r"[^a-zA-Z0-9_\u0400-\u04FF]", "_", base)
    print(safe("  [1/4] Triage Agent: анализ кода..."))
    triage = llm("Ты — специалист по code review. Проанализируй код, составь план ревью.",
                 f"Код:\n\n{code[:4000]}")
    print(safe("  [2/4] Style Agent: проверка стиля..."))
    style = llm("Ты — эксперт по стилю Python (PEP8). Найди проблемы стиля.",
                f"Код:\n\n{code[:4000]}")
    print(safe("  [3/4] Security Agent: проверка безопасности..."))
    security = llm("Ты — специалист по безопасности. Найди уязвимости.",
                   f"Код:\n\n{code[:4000]}")
    print(safe("  [4/4] Reporter: составление отчёта..."))
    report = llm(
        "Ты — составитель отчётов на русском в markdown.",
        f"Файл: {filename}\n\nПлан ревью:\n{triage[:1000]}\n\nСтиль:\n{style[:1000]}\n\nБезопасность:\n{security[:1000]}"
    )
    path = os.path.join(REPORT_DIR, f"review_report_{filename}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    print(safe(f"  [Done] Отчёт: {path}"))
    return path

async def handle_documentation(query: str, code: str, file_path: str = ""):
    """Documentation — 3 агента."""
    if not code:
        print(safe("  [ERROR] Не указан файл для документирования"))
        return
    base = os.path.basename(file_path) if file_path else "code"
    filename = re.sub(r"[^a-zA-Z0-9_\u0400-\u04FF]", "_", base)
    print(safe("  [1/3] DocPlanner: структура документации..."))
    plan = llm("Ты — DocPlanner. Составь структуру документации для этого кода.",
               f"Код:\n\n{code[:4000]}")
    print(safe("  [2/3] DocWriter: написание документации..."))
    docs = llm("Ты — DocWriter. Напиши документацию на русском в markdown.",
               f"Код:\n\n{code[:4000]}\n\nСтруктура:\n{plan[:1000]}")
    print(safe("  [3/3] DocReviewer: проверка и финализация..."))
    final = llm("Ты — DocReviewer. Проверь и доработай документацию.",
                f"Документация:\n\n{docs[:4000]}")
    path = os.path.join(DOCS_DIR, f"docs_{filename}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(final)
    print(safe(f"  [Done] Документация: {path}"))
    return path

def _apply_patch(original: str, new_parts: str) -> str:
    """Заменяет функции/классы в original на версии из new_parts."""
    lines = original.split("\n")
    # Ищем заголовки def/class в new_parts
    new_headers = re.findall(r'^((?:async\s+)?(?:def|class)\s+\w+)', new_parts, re.MULTILINE)
    if not new_headers:
        return original
    for header in new_headers:
        header_stripped = header.strip()
        # Ищем начало в original
        start_idx = -1
        for i, ln in enumerate(lines):
            if ln.strip().startswith(header_stripped):
                start_idx = i
                break
        if start_idx == -1:
            continue
        # Ищем конец: следующая def/class на том же уровне
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
        # Ищем тот же header в new_parts и вырезаем его тело
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
    """Извлекает релевантные куски кода по описанию бага.
    Ищет def/class упомянутые в баге и вырезает их с контекстом."""
    lines = code.split("\n")
    # Ищем имена функций/классов в описании бага
    names = re.findall(r'(?:функци[яи]|def|class|метод[а]?)\s+(\w+)', bug_desc, re.IGNORECASE)
    if not names:
        names = re.findall(r'\b(normalize_symbol|known_quotes)\b', bug_desc, re.IGNORECASE)
    if not names:
        return "\n".join(lines[:max_lines]) + "\n# ... (обрезано)"
    # Для каждого имени вырезаем её определение с окрестностями
    result_lines = []
    seen_ranges = set()
    for name in set(names):
        for i, ln in enumerate(lines):
            if re.match(rf'\s*(?:async\s+)?def\s+{re.escape(name)}\s*\(', ln) or \
               re.match(rf'\s*class\s+{re.escape(name)}\s*[:\(]', ln):
                # Находим конец функции/класса
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
    """Bug Fix — интерактивный: анализ → цикл Fixer↔Tester (до 3 попыток) → отчёт."""
    if not code:
        print(safe("  [ERROR] Не указан файл для исправления"))
        return
    base = os.path.basename(file_path) if file_path else "code"
    slug = re.sub(r"[^a-zA-Z0-9_\u0400-\u04FF]", "_", base)
    lines_total = len(code.split("\n"))
    print(safe("  [1/4] BugAnalyzer: поиск багов..."))
    # Для больших файлов отправляем только первые 2000 строк для анализа
    code_snippet = code if lines_total <= 2000 else "\n".join(code.split("\n")[:2000]) + "\n# ... (обрезано)"
    analysis = llm(
        "Ты — BugAnalyzer. Найди ВСЕ баги в коде. Верни нумерованный список "
        "(1. ... 2. ...), каждый баг с кратким описанием и локацией в коде.",
        f"Код:\n\n{code_snippet}"
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

    # Для больших файлов: извлекаем релевантные куски кода
    relevant_code = _extract_relevant_code(code, selected)
    print(safe(f"  (код файла: {lines_total} строк, отправлено Fixer: {len(relevant_code.split(chr(10)))} строк)"))

    fixed_relevant = ""
    last_feedback = ""
    status = "FAILED"
    test_result = ""

    for attempt in range(3):
        print(safe(f"  [2/4] Fixer: попытка {attempt+1}/3..."))
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
        fixed_relevant = llm(fix_prompt, f"Исходные функции/классы:\n{relevant_code}\n\nИсправить баги:\n{selected}")
        fixed_relevant = strip_code_fences(fixed_relevant)

        # Склеиваем фикс с оригиналом: заменяем старые определения на новые
        patched = _apply_patch(code, fixed_relevant)
        err = validate_python(patched)
        if err:
            print(safe(f"  [Fixer] Патч не компилируется: {err[:200]}"))
            last_feedback = f"Patch SyntaxError: {err}"
            if attempt == 2:
                status = "SYNTAX_ERROR"
                test_result = last_feedback
            continue

        print(safe(f"  [3/4] Tester: проверка попытки {attempt+1}/3..."))
        test_result = llm(
            "Ты — Tester. Проверь исправленный код. Ответь строго с новой строки:\n"
            "Строка 1: 'OK' если все выбранные баги устранены, или 'FAIL: <причина>' если нет.\n"
            "Строка 2 и далее: подробное объяснение, что именно не исправлено, если FAIL.",
            f"Выбранные баги:\n{selected}\n\nИзменённый код:\n{fixed_relevant[:3000]}\n\nРезультат склейки (первые/последние 50 строк):\n"
            f"{chr(10).join(patched.split(chr(10))[:50])}\n...\n{chr(10).join(patched.split(chr(10))[-50:])}"
        )
        verdict = test_result.strip().split("\n", 1)[0].strip()
        if verdict.upper().startswith("OK"):
            status = "OK"
            break
        else:
            last_feedback = test_result
            status = "FAILED"
            print(safe(f"  [Tester] Баги ещё не исправлены. Повтор..."))

    print(safe("  [4/4] Reporter: отчёт..."))
    report = llm(
        "Ты — Reporter на русском. Составь отчёт: какие баги выбраны → что исправлено → "
        f"{'все исправлено' if status == 'OK' else 'проблемы остались'} → результат проверки.",
        f"Выбранные баги:\n{selected[:1000]}\n\n"
        f"Статус: {status}\n\n"
        f"Результат теста:\n{test_result[:1500]}"
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

# ─── Project mode ──────────────────────────────────────

async def handle_project_bug_fix(query: str, files: list[tuple[str, str]], interactive: bool = True):
    """Bug Fix для всего проекта: анализ всех файлов → общий список → фикс → отчёт."""
    if not files:
        print(safe("  [ERROR] Нет файлов для анализа"))
        return

    print(safe(f"  [1/4] BugAnalyzer: анализ {len(files)} файлов проекта..."))
    all_bugs = {}
    for fpath, fcode in files:
        short = os.path.basename(fpath)
        lines_total = len(fcode.split("\n"))
        code_snippet = fcode if lines_total <= 2000 else "\n".join(fcode.split("\n")[:2000]) + "\n# ... (обрезано)"
        print(safe(f"    -> {short} ({lines_total} строк)"))
        analysis = llm(
            "Ты — BugAnalyzer. Найди ВСЕ баги в коде. Верни нумерованный список "
            "(1. ... 2. ...), каждый баг с кратким описанием и локацией в коде.",
            f"Код:\n\n{code_snippet}"
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

    # Группируем выбранные баги по файлам
    selected_nums = {int(n) for n in re.findall(r"\d+", sel)} if sel.lower() != "all" else "all"
    files_to_fix = {}  # {fname: {"code": ..., "bugs": ...}}
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
            print(safe(f"  Fixer: попытка {attempt+1}/3..."))
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
            fixed_relevant = llm(fix_prompt, f"Исходный код:\n{relevant_code}\n\nИсправить:\n{selected}")
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

            print(safe(f"  Tester: проверка..."))
            test_result = llm(
                "Ты — Tester. Ответь строго с новой строки:\n"
                "Строка 1: 'OK' если баги устранены, или 'FAIL: <причина>' если нет.\n"
                "Строка 2+: подробности.",
                f"Баги:\n{selected}\n\nИзменённый код:\n{fixed_relevant[:3000]}"
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

    # Отчёт по проекту
    print(safe("\n  [4/4] Reporter: итоговый отчёт..."))
    summary = "\n".join(
        f"- {f}: {v['status']}" for f, v in fixed_files.items()
    )
    report = llm(
        "Ты — Reporter на русском. Составь отчёт по исправлению багов в проекте:\n"
        "какие файлы затронуты → какие баги исправлены → статус.",
        f"Файлы:\n{summary}\n\nДетали:\n" +
        "\n".join(f"--- {f} ---\nСтатус: {v['status']}\nТест: {v['test'][:500]}"
                  for f, v in fixed_files.items())
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
    """Исследование/анализ — многоагентный режим (как в статье)."""
    context = f"\nКонтекст (код):\n{code[:2000]}" if code else ""
    print(safe("  [1/3] Planner: разбиваю на подзадачи..."))
    plan = llm(
        "Ты — Planner. Разбей задачу на 2-4 конкретные подзадачи. "
        "Ответь строго списком, каждая строка с '-'.",
        f"{query}{context}",
        temp=0.4,
    )
    tasks = [t.strip().lstrip("- ").strip() for t in plan.split("\n") if t.strip().startswith("-")]
    if not tasks:
        tasks = [query]
    print(safe(f"    Разбито на {len(tasks)} подзадач"))
    results = []
    print(safe("  [2/3] Executor: выполняю подзадачи..."))
    for i, task in enumerate(tasks):
        print(safe(f"    [{i+1}/{len(tasks)}] {task[:120]}"))
        r = llm(
            "Ты — эксперт, выполняющий подзадачу. Ответь подробно и структурированно. На русском.",
            f"Подзадача: {task}\n\nКонтекст: {query}{context}",
            temp=0.3,
        )
        results.append({"task": task, "result": r})
        print(safe(f"      -> {len(r)} chars"))
    print(safe("  [3/3] Compiler: собираю итоговый ответ..."))
    combined = "\n\n".join(
        f"### Подзадача: {r['task']}\n{r['result']}" for r in results
    )
    final = llm(
        "Ты — составитель отчётов. Объедини результаты в один связный ответ на русском в markdown.",
        combined,
        temp=0.3,
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

    # Сначала проверяем — это проект (директория) или одиночный файл?
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
    print(safe("\n  === User Mode ==="))
    print(safe("  Введи задачу на естественном языке (или 'exit')."))
    print(safe("  Система сама определит тип задачи и выполнит её."))
    print(safe("  Примеры:"))
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
            desc, temp=0.2,
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
            desc, temp=0.2,
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
  Qubax  |  AI agents
"""

async def main_menu():
    print(safe(BANNER))
    print(safe(f"  Model: {MODEL}"))
    print(safe(f"  API:   {OC_URL}\n"))
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
    p = argparse.ArgumentParser(description="AutoAgent Zen CLI")
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
