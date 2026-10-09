import sys
import bench_free as b

targets = sys.argv[1:] or ['big-pickle', 'muse-spark-1.2-contributor-free', 'mimo-v2.5-free']
alive = []
for m in targets:
    try:
        t = b.ask(m, 'What is 2+2? Reply with just the number.', 400, attempts=4)
        ok = bool(t and t.strip())
    except Exception:
        ok = False
    print(('ALIVE ' if ok else 'DOWN  ') + b.LABELS.get(m, m))
    if ok:
        alive.append(m)

print()
print('Targets alive:', [b.LABELS.get(m, m) for m in alive])
if alive:
    b.run_tqa(alive)
    b.run_gsm_bbh(alive)
b.print_table()
