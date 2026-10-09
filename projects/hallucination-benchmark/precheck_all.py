import sys
import bench_free as b

models = [
    'big-pickle',
    'deepseek-v4-flash-free',
    'laguna-s-2.1-free',
    'ling-3.0-flash-fin-free',
    'mimo-v2.5-free',
    'muse-spark-1.2-contributor-free',
    'nemotron-3.5-lightning-free',
    'nemotron-3-ultra-free',
]

alive = []
for m in models:
    ok = False
    err = ''
    try:
        t = b.ask(m, 'Say OK', 300, attempts=5)
        ok = bool(t)
    except Exception as e:
        err = str(e)[:60]
    print(('ALIVE ' if ok else 'DOWN  ') + m + ('' if ok else ('  ' + err)))
    if ok:
        alive.append(m)

print()
print('ALIVE:', alive)
