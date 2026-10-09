import json, os, time, sys, io, subprocess, tempfile, traceback
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ZEN_KEY = 'REDACTED_KEY'
GOOGLE_KEY = 'REDACTED_KEY'
XAI_KEY = 'REDACTED_KEY'
MISTRAL_KEY = 'REDACTED_KEY'
OPENROUTER_KEY = 'REDACTED_KEY'
DELAY = 1

MODELS = [
    {'provider': 'opencode-zen', 'model': 'big-pickle'},
    {'provider': 'opencode-zen', 'model': 'deepseek-v4-flash-free'},
    {'provider': 'opencode-zen', 'model': 'nemotron-3-ultra-free'},
    {'provider': 'mistral', 'model': 'mistral-medium-latest'},
    {'provider': 'openrouter', 'model': 'nvidia/nemotron-3-super-120b-a12b:free'},
    {'provider': 'openrouter', 'model': 'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free'},
    {'provider': 'openrouter', 'model': 'google/gemma-4-26b-a4b-it:free'},
]

LABELS = {
    'big-pickle': 'Big Pickle',
    'deepseek-v4-flash-free': 'DeepSeek V4 Flash',
    'nemotron-3-ultra-free': 'Nemotron 3 Ultra',
    'mistral-medium-latest': 'Mistral Medium 3.5',
    'nvidia/nemotron-3-super-120b-a12b:free': 'Nemotron 3 Super 120B',
    'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free': 'Nemotron Nano Omni 30B (R)',
    'google/gemma-4-26b-a4b-it:free': 'Gemma 4 26B',
}

if len(sys.argv) > 2 and sys.argv[1] == '--model':
    target = sys.argv[2].lower()
    filtered = [m for m in MODELS if m['model'] == target or LABELS.get(m['model'], '').lower() == target]
    if not filtered:
        print(f'Model "{target}" not found. Available:')
        for cfg in MODELS:
            print(f'  {cfg["model"]:45s} {LABELS.get(cfg["model"], "")}')
        sys.exit(1)
    MODELS = filtered

PROBLEMS_COUNT = 164
if len(sys.argv) > 3 and sys.argv[1] == '--model':
    PROBLEMS_COUNT = int(sys.argv[3])

# --- API functions ---

def ask_zen(m, prompt):
    payload = {
        'model': m,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 512,
        'temperature': 0,
    }
    resp = requests.post(
        'https://opencode.ai/zen/v1/chat/completions',
        json=payload,
        headers={'Authorization': 'Bearer ' + ZEN_KEY, 'Content-Type': 'application/json'},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    choices = data.get('choices', [])
    if not choices:
        return ''
    msg = choices[0].get('message', {})
    return msg.get('content', '') or msg.get('reasoning', '') or ''

def ask_google(m, prompt):
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent'
    payload = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'maxOutputTokens': 512, 'temperature': 0},
    }
    resp = requests.post(url, params={'key': GOOGLE_KEY}, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data['candidates'][0]['content']['parts'][0]['text']

def ask_mistral(m, prompt):
    payload = {
        'model': m,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 512,
        'temperature': 0,
    }
    resp = requests.post(
        'https://api.mistral.ai/v1/chat/completions',
        json=payload,
        headers={'Authorization': 'Bearer ' + MISTRAL_KEY, 'Content-Type': 'application/json'},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    choices = data.get('choices', [])
    if not choices:
        return ''
    return choices[0].get('message', {}).get('content', '') or ''

def ask_openrouter(m, prompt):
    payload = {
        'model': m,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 512,
        'temperature': 0,
    }
    resp = requests.post(
        'https://openrouter.ai/api/v1/chat/completions',
        json=payload,
        headers={'Authorization': 'Bearer ' + OPENROUTER_KEY, 'Content-Type': 'application/json'},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    choices = data.get('choices', [])
    if not choices:
        return ''
    msg = choices[0].get('message', {})
    return msg.get('content', '') or msg.get('reasoning', '') or ''

def ask_model(cfg, prompt):
    if cfg['provider'] == 'google':
        return ask_google(cfg['model'], prompt)
    if cfg['provider'] == 'mistral':
        return ask_mistral(cfg['model'], prompt)
    if cfg['provider'] == 'openrouter':
        return ask_openrouter(cfg['model'], prompt)
    return ask_zen(cfg['model'], prompt)

def extract_code(text, entry_point):
    """Extract function code from model response."""
    text = text.strip()

    if f'def {entry_point}' in text:
        start = text.index(f'def {entry_point}')
        code = text[start:]
        if '```' in code:
            code = code.split('```')[0]
        return code.strip()

    lines = text.split('\n')
    code_lines = []
    in_code = False
    for line in lines:
        if line.strip().startswith('def ') or in_code:
            in_code = True
            code_lines.append(line)
            if line.strip() and not line.startswith(' ') and not line.startswith('\t') and len(code_lines) > 1:
                code_lines.pop()
                break
    if code_lines:
        return '\n'.join(code_lines).strip()

    return text.strip()

def run_test(prompt_code, test_code, entry_point, timeout=10):
    """Execute code and run tests."""
    full_code = prompt_code + '\n\n' + test_code
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(full_code)
            tmp_path = f.name
        result = subprocess.run(
            ['python', tmp_path],
            capture_output=True, text=True, timeout=timeout,
        )
        os.unlink(tmp_path)
        return result.returncode == 0, result.stderr[:200] if result.returncode != 0 else ''
    except subprocess.TimeoutExpired:
        try:
            os.unlink(tmp_path)
        except:
            pass
        return False, 'timeout'
    except Exception as e:
        return False, str(e)[:100]

# --- Load HumanEval ---
data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'humaneval.json')
if not os.path.exists(data_path):
    print('humaneval.json not found.')
    sys.exit(1)

with open(data_path, 'r', encoding='utf-8') as f:
    problems = json.load(f)[:PROBLEMS_COUNT]

print(f'Loaded {len(problems)} HumanEval problems')

results = {}

for cfg in MODELS:
    label = LABELS.get(cfg['model'], cfg['model'])
    print()
    print('=' * 60)
    print('Testing:', label)
    print('=' * 60)

    passed = 0
    errors = 0
    for i, prob in enumerate(problems):
        prompt = (
            f"Complete the Python function.\n\n"
            f"{prob['prompt']}\n"
            f"Write ONLY the function body. No explanation."
        )

        try:
            response = ask_model(cfg, prompt)
            code = extract_code(response, prob['entry_point'])

            full_func = prob['prompt'] + '\n' + code
            ok, err = run_test(full_func, prob['test'], prob['entry_point'])
            if ok:
                passed += 1
            status = '+' if ok else '-'
        except Exception as e:
            errors += 1
            status = '!'
            err = str(e)[:50]

        if (i + 1) % 20 == 0 or i == 0:
            print(f'  {status} [{i+1}/{len(problems)}] {prob["task_id"]:15s} passed={passed}')

        time.sleep(DELAY)

    pass_rate = passed / len(problems) * 100
    results[cfg['model']] = {
        'passed': passed,
        'total': len(problems),
        'pass_rate': pass_rate,
        'errors': errors,
    }
    print(f'\n  Pass@1: {passed}/{len(problems)} = {pass_rate:.1f}% ({errors} errors)')

    if cfg != MODELS[-1]:
        time.sleep(3)

# --- Final table ---
print()
print('=' * 60)
print('HUMANEVAL RESULTS (pass@1)')
print('=' * 60)
print(f'{"Model":40s} {"Pass@1":>7s} {"Passed":>7s}')
print('-' * 55)
for cfg in MODELS:
    label = LABELS.get(cfg['model'], cfg['model'])
    r = results.get(cfg['model'], {})
    pr = r.get('pass_rate', 0)
    p = r.get('passed', 0)
    t = r.get('total', 0)
    bar = '#' * int(pr / 2)
    print(f'{label:40s} {pr:5.1f}% {p}/{t}  {bar}')
print('-' * 55)
