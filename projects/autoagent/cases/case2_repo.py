#!/usr/bin/env python3
"""Кейс 2 — Агент по репозиторию: Planner → Coding Agent → тесты → отчёт.

Флоу:
  1. Triage/Planner читает репозиторий и вывод упавших тестов, находит баги.
  2. Coding Agent (multi-model: планирование qwen3-235b, код glm-5.2) правит файлы.
  3. Тесты запускаются на исправленной копии, до 3 итераций.
  4. Reporter собирает отчёт: баги → правки (diff) → результат тестов.

Запуск:
  python case2_repo.py
"""

import os, sys, json, shutil, subprocess, difflib
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE))
from auto_zen import llm, safe, strip_code_fences, validate_python, ROLE_MODELS  # noqa: E402

SAMPLE = os.path.join(BASE, "sample_repo")
OUT_DIR = os.path.join(BASE, "out")
os.makedirs(OUT_DIR, exist_ok=True)

IGNORE = shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc")


def make_run_dir(prefix: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUT_DIR, f"{prefix}_{ts}")
    os.makedirs(path, exist_ok=True)
    return path


# ─── Helpers ─────────────────────────────────────────────────

def copy_repo(src: str, dst: str):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=IGNORE)


def run_tests(cwd: str) -> tuple[bool, str]:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=180,
    )
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode == 0, out.strip()


def repo_sources(root: str) -> dict[str, str]:
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("tests", "__pycache__", ".pytest_cache")]
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root).replace("\\", "/")
            with open(path, "r", encoding="utf-8") as f:
                files[rel] = f.read()
    return files


def make_diff(old: str, new: str, rel: str, max_lines: int = 80) -> str:
    if old == new:
        return ""
    lines = list(difflib.unified_diff(
        old.splitlines(), new.splitlines(),
        fromfile=f"a/{rel}", tofile=f"b/{rel}", lineterm="",
    ))
    if len(lines) > max_lines:
        lines = lines[:max_lines] + ["... (diff обрезан)"]
    return "\n".join(lines)


def ask_coder(rel: str, code: str, bugs: str, test_output: str, note: str = "") -> str:
    system = (
        "Ты — Coder. Исправь баги в файле. Верни ТОЛЬКО полный исправленный код файла — "
        "без markdown-фенсов, без пояснений и без тестов. Тесты менять нельзя, "
        "публичный API сохранить. Код должен компилироваться на Python 3."
    )
    user = (
        f"Файл: {rel}\n\nСписок багов:\n{bugs}\n\n"
        f"Вывод упавших тестов:\n{test_output[-2500:]}\n\n"
        f"Исходный код:\n{code}"
    )
    if note:
        user += f"\n\nЗамечание к предыдущему ответу: {note}"
    fixed = strip_code_fences(llm(system, user, temp=0.1, role="coder"))
    err = validate_python(fixed)
    if err:
        print(safe(f"      [coder] синтаксис не прошёл: {err[:120]}"))
        fixed = strip_code_fences(llm(system, user + f"\n\nПредыдущий ответ не компилируется:\n{err}", temp=0.1, role="coder"))
        if validate_python(fixed):
            return ""
    return fixed


# ─── Main ────────────────────────────────────────────────────

def main():
    run_dir = make_run_dir("repo_run")
    baseline_dir = os.path.join(run_dir, "repo_baseline")
    fixed_dir = os.path.join(run_dir, "repo_fixed")
    print(safe(f"\n{'='*60}\n  Кейс 2. Агент по репозиторию\n{'='*60}"))
    print(safe(f"  Папка прогона: {run_dir}"))

    print(safe("\n[1/5] Triage/Planner: чтение репозитория и запуск тестов..."))
    copy_repo(SAMPLE, baseline_dir)
    sources = repo_sources(SAMPLE)
    ok, base_out = run_tests(baseline_dir)
    print(safe(f"  Файлов: {len(sources)} | baseline тесты: {'PASSED' if ok else 'FAILED'}"))
    print(safe("\n" + base_out[-1200:] + "\n"))
    with open(os.path.join(run_dir, "baseline_pytest.txt"), "w", encoding="utf-8") as f:
        f.write(base_out)

    code_text = "\n\n".join(f"--- {rel} ---\n{code}" for rel, code in sources.items())
    bugs = llm(
        "Ты — Planner/Coding Agent. Дан небольшой репозиторий и вывод pytest. "
        "Найди причины падений и верни нумерованный список багов: файл, функция, "
        "в чём баг и как исправить. Кратко, без воды.",
        f"Код:\n{code_text}\n\nВывод pytest:\n{base_out[-3000:]}",
        temp=0.1, role="planner",
    )
    print(safe("--- НАЙДЕННЫЕ БАГИ ---"))
    print(safe(bugs.strip()[:1500]))
    print(safe("----------------------\n"))

    print(safe("[2/5] Coding Agent: исправление файлов..."))
    copy_repo(SAMPLE, fixed_dir)
    final_out, passed = base_out, False
    for attempt in range(1, 4):
        print(safe(f"\n  Итерация {attempt}/3:"))
        feedback = final_out
        for rel, orig in sources.items():
            print(safe(f"    - {rel}"))
            fixed = ask_coder(rel, orig, bugs, feedback)
            if not fixed:
                print(safe("      [skip] правка не удалась, файл остаётся как есть"))
                continue
            path = os.path.join(fixed_dir, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
            with open(path, "w", encoding="utf-8") as f:
                f.write(fixed)
        print(safe("  [3/5] Tester: запуск pytest на исправленной копии..."))
        passed, final_out = run_tests(fixed_dir)
        print(safe("  " + final_out.splitlines()[-1] if final_out else "  (нет вывода)"))
        if passed:
            break

    print(safe(f"\n  Итог тестов: {'PASSED' if passed else 'FAILED'}"))
    print(safe(final_out[-1500:] + "\n"))
    with open(os.path.join(run_dir, "final_pytest.txt"), "w", encoding="utf-8") as f:
        f.write(final_out)

    print(safe("[4/5] Diff по изменённым файлам..."))
    diffs = []
    for rel, orig in sources.items():
        path = os.path.join(fixed_dir, rel)
        new = open(path, "r", encoding="utf-8").read() if os.path.exists(path) else orig
        d = make_diff(orig, new, rel)
        if d:
            diffs.append(f"### {rel}\n```diff\n{d}\n```")
            print(safe(f"    изменён: {rel}"))

    print(safe("[5/5] Reporter: итоговый отчёт..."))
    report = llm(
        "Ты — Reporter. Составь отчёт на русском в markdown: исходное состояние тестов, "
        "найденные баги, что изменено по файлам (по diff), финальный результат pytest. "
        "Не выдумывай детали, которых нет во входных данных.",
        f"Баги:\n{bugs}\n\nBaseline pytest:\n{base_out[-1800:]}\n\n"
        f"Финальный pytest:\n{final_out[-1800:]}\n\nИзменения:\n" + "\n\n".join(diffs)[:6000],
        temp=0.2, role="reporter",
    )
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(run_dir, "report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Отчёт агента по репозиторию\n\n"
                f"- Baseline: {'PASSED' if ok else 'FAILED'}\n"
                f"- После правок: {'PASSED' if passed else 'FAILED'}\n\n{report}")
    with open(os.path.join(run_dir, "run_info.json"), "w", encoding="utf-8") as f:
        json.dump({
            "created": datetime.now().isoformat(timespec="seconds"),
            "models": ROLE_MODELS,
            "baseline_passed": ok,
            "final_passed": passed,
            "files_changed": [line.splitlines()[0][4:] for line in diffs],
        }, f, ensure_ascii=False, indent=2)
    print(safe(f"\n  [Done] ВСЁ в одной папке — открой её:\n  {run_dir}"))
    print(safe("    report.md · baseline_pytest.txt · final_pytest.txt · "
               "repo_baseline/ · repo_fixed/ · run_info.json"))


if __name__ == "__main__":
    main()
