import json, os, time, sys, subprocess, tempfile
import requests

ZEN_KEY = 'REDACTED_KEY'
MISTRAL_KEY = 'REDACTED_KEY'
OPENROUTER_KEY = 'REDACTED_KEY'
DELAY = 1

MODELS = [
    ('opencode-zen', 'big-pickle', 'Big Pickle'),
    ('opencode-zen', 'deepseek-v4-flash-free', 'DeepSeek V4 Flash'),
    ('opencode-zen', 'nemotron-3-ultra-free', 'Nemotron 3 Ultra'),
    ('mistral', 'mistral-medium-latest', 'Mistral Medium 3.5'),
    ('openrouter', 'nvidia/nemotron-3-super-120b-a12b:free', 'Nemotron 3 Super 120B'),
    ('openrouter', 'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free', 'Nemotron Nano Omni 30B (R)'),
    ('openrouter', 'google/gemma-4-26b-a4b-it:free', 'Gemma 4 26B'),
]

PROBLEMS_COUNT = 50

def ask(provider, model, prompt):
    if provider == 'opencode-zen':
        payload = {'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 512, 'temperature': 0}
        resp = requests.post('https://opencode.ai/zen/v1/chat/completions', json=payload,
            headers={'Authorization': 'Bearer ' + ZEN_KEY, 'Content-Type': 'application/json'}, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        msg = data['choices'][0]['message']
        return msg.get('content', '') or msg.get('reasoning_content', '') or msg.get('reasoning', '') or ''
    elif provider == 'mistral':
        payload = {'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 512, 'temperature': 0}
        resp = requests.post('https://api.mistral.ai/v1/chat/completions', json=payload,
            headers={'Authorization': 'Bearer ' + MISTRAL_KEY, 'Content-Type': 'application/json'}, timeout=60)
        resp.raise_for_status()
        return resp.json()['choices'][0]['message'].get('content', '') or ''
    elif provider == 'openrouter':
        payload = {'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 512, 'temperature': 0}
        resp = requests.post('https://openrouter.ai/api/v1/chat/completions', json=payload,
            headers={'Authorization': 'Bearer ' + OPENROUTER_KEY, 'Content-Type': 'application/json'}, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        msg = data['choices'][0]['message']
        return msg.get('content', '') or msg.get('reasoning_content', '') or msg.get('reasoning', '') or ''
    return ''

def extract_code(text, entry_point):
    text = text.strip()
    if '```python' in text:
        text = text.split('```python')[1].split('```')[0]
    elif '```' in text:
        text = text.split('```')[1].split('```')[0]
    lines = text.strip().split('\n')
    code_lines = []
    started = False
    for line in lines:
        if line.strip().startswith('def '):
            started = True
        if started:
            if code_lines and not line.startswith(' ') and not line.startswith('\t') and line.strip():
                break
            code_lines.append(line)
    if code_lines:
        return '\n'.join(code_lines)
    return text.strip()

def run_test(code, test_code, timeout=10):
    full = code + '\n\n' + test_code
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(full)
            tmp = f.name
        result = subprocess.run(['python', tmp], capture_output=True, text=True, timeout=timeout)
        os.unlink(tmp)
        return result.returncode == 0
    except:
        try: os.unlink(tmp)
        except: pass
        return False

with open('D:\\AI\\hallucination-benchmark\\humaneval.json', 'r', encoding='utf-8') as f:
    problems = json.load(f)[:PROBLEMS_COUNT]

log_path = 'D:\\AI\\hallucination-benchmark\\humaneval_results.json'
results = {}

for provider, model, label in MODELS:
    sys.stdout.write(f'\nTesting: {label}\n')
    sys.stdout.flush()
    passed = 0
    errors = 0
    for i, prob in enumerate(problems):
        prompt = f"Complete the Python function.\n\n{prob['prompt']}\nWrite ONLY the function body. No explanation."
        try:
            response = ask(provider, model, prompt)
            code = extract_code(response, prob['entry_point'])
            full_func = prob['prompt'] + '\n' + code
            ok = run_test(full_func, prob['test'])
            if ok:
                passed += 1
        except Exception as e:
            errors += 1
            if errors <= 2:
                sys.stdout.write(f'  ERROR: {str(e)[:60]}\n')
                sys.stdout.flush()
        time.sleep(DELAY)
        if (i + 1) % 10 == 0:
            sys.stdout.write(f'  [{i+1}/{PROBLEMS_COUNT}] passed={passed}\n')
            sys.stdout.flush()

    pr = passed / len(problems) * 100
    results[model] = {'label': label, 'pass_rate': pr, 'passed': passed, 'total': len(problems), 'errors': errors}
    sys.stdout.write(f'  {label}: {passed}/{len(problems)} = {pr:.1f}%\n')
    sys.stdout.flush()
    time.sleep(2)

with open(log_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

sys.stdout.write('\n' + '=' * 55 + '\n')
sys.stdout.write(f'{"Model":35s} {"Pass@1":>7s}\n')
sys.stdout.write('-' * 55 + '\n')
for _, model, label in MODELS:
    r = results.get(model, {})
    pr = r.get('pass_rate', 0)
    p = r.get('passed', 0)
    t = r.get('total', 0)
    bar = '#' * int(pr / 2)
    sys.stdout.write(f'{label:35s} {pr:5.1f}% {p}/{t}  {bar}\n')
sys.stdout.write('-' * 55 + '\n')
sys.stdout.flush()
