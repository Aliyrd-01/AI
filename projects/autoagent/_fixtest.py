import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auto_zen as az

path = r"D:\trading\landing2\CryptoInsightX1\CryptoInsightX\crypto-analyzer\trading_app.py"
code = az.read_file(path)
bug3 = ("3. В функции normalize_symbol стейблкоин BUSD ошибочно интерпретируется как пара B/USD. "
        "Нужно добавить BUSD в known_quotes и проверять до суффиксного разбиения.")

t0 = time.time()
print("Fixer...", flush=True)
fixed = az.llm(
    "Ты — Fixer. Верни ПОЛНЫЙ исправленный файл целиком (все строки, без сокращений), "
    "устранив указанный баг. Отвечай ТОЛЬКО кодом, без пояснений и без markdown-фенсов. "
    "Не обрывай файл — верни его полностью до конца.",
    f"Исходный код:\n{code}\n\nИсправить баг:\n{bug3}"
)
fixed = az.strip_code_fences(fixed)
print("validate...", round(time.time()-t0), "s", flush=True)
err = az.validate_python(fixed)
if err:
    print("FAILED, retry:", err[:300], flush=True)
    fixed = az.llm(
        f"Твой предыдущий ответ содержит ошибку Python:\n{err}\n\n"
        "Верни ПОЛНЫЙ исправленный файл целиком, без ошибок. Только код.",
        f"Исходный код:\n{code}\n\nИсправить баг:\n{bug3}"
    )
    fixed = az.strip_code_fences(fixed)
    err = az.validate_python(fixed)

print("COMPILE:", "OK" if not err else "FAIL", flush=True)
if not err:
    # проверка семантики: BUSD должен давать BUSD/USDT, а не B/USD
    import re
    has_known = 'known_quotes' in fixed and 'BUSD' in fixed
    print("BUSD in known_quotes:", has_known, flush=True)
    out = os.path.join(az.FIXED_DIR, "trading_app_fixed.py")
    with open(out, "w", encoding="utf-8") as f:
        f.write(fixed)
    print("saved:", out, flush=True)
else:
    print("ERROR:", err[:500], flush=True)
