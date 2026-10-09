import os, re, subprocess, sys, time
import bench_free as b

OC = r'C:\Users\valen\AppData\Local\Zed\external_agents\registry\opencode\v_1.18.34_236ce8f55c2ac138_97619089081f3a69\opencode.exe'
ANSI = re.compile(r'\x1b\[[0-9;]*m')


def ask_cli(model, prompt, timeout=180):
    last_err = 'empty cli response'
    for _ in range(2):
        try:
            r = subprocess.run(
                [OC, 'run', '-m', 'opencode/' + model, prompt],
                capture_output=True, text=True, encoding='utf-8',
                errors='replace', timeout=timeout,
            )
            out = ANSI.sub('', r.stdout or '')
            lines = [l for l in out.splitlines() if l.strip() and not l.strip().startswith('>')]
            ans = '\n'.join(lines).strip()
            if ans:
                return ans
        except Exception as e:
            last_err = str(e)[:80]
        time.sleep(5)
    raise RuntimeError(last_err)


def patched_ask(model, prompt, max_tokens=256, attempts=6):
    return ask_cli(model, prompt)


if __name__ == '__main__':
    targets = sys.argv[1:] or ['big-pickle']
    b.ask = patched_ask
    b.run_tqa(targets)
    b.run_gsm_bbh(targets)
    b.print_table()
