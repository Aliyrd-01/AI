import json, time, sys, subprocess, tempfile
import requests

OR_KEY = 'REDACTED_KEY'

MODELS = [
    ('nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free', 'Nemotron Nano Omni 30B (R)'),
    ('google/gemma-4-26b-a4b-it:free', 'Gemma 4 26B'),
]

with open('D:\\AI\\hallucination-benchmark\\humaneval.json', 'r', encoding='utf-8') as f:
    problems = json.load(f)[:50]

def ask_or(model, prompt):
    payload = {'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 512, 'temperature': 0}
    resp = requests.post('https://openrouter.ai/api/v1/chat/completions', json=payload,
        headers={'Authorization': 'Bearer ' + OR_KEY, 'Content-Type': 'application/json'}, timeout=60)
    data = resp.json()
    if resp.status_code == 429:
        return None
    resp.raise_for_status()
    msg = data['choices'][0]['message']
    return msg.get('content', '') or msg.get('reasoning_content', '') or msg.get('reasoning', '') or ''

def extract_code(text, ep):
    text = text.strip()
    if '```python' in text: text = text.split('```python')[1].split('```')[0]
    elif '```' in text: text = text.split('```')[1].split('```')[0]
    lines = text.strip().split('\n')
    cl = []
    started = False
    for l in lines:
        if l.strip().startswith('def '): started = True
        if started:
            if cl and not l.startswith(' ') and not l.startswith('\t') and l.strip(): break
            cl.append(l)
    return '\n'.join(cl) if cl else text.strip()

def run_test(code, test):
    full = code + '\n\n' + test
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(full); tmp = f.name
        r = subprocess.run(['python', tmp], capture_output=True, text=True, timeout=10)
        os.unlink(tmp)
        return r.returncode == 0
    except:
        try: os.unlink(tmp)
        except: pass
        return False

for model, label in MODELS:
    sys.stdout.write('Testing: ' + label + '\n'); sys.stdout.flush()
    passed = 0
    for i, prob in enumerate(problems):
        prompt = 'Complete the Python function.\n\n' + prob['prompt'] + '\nWrite ONLY the function body. No explanation.'
        retries = 3
        while retries > 0:
            try:
                resp = ask_or(model, prompt)
                if resp is None:
                    retries -= 1
                    if retries > 0: time.sleep(5)
                    continue
                code = extract_code(resp, prob['entry_point'])
                full = prob['prompt'] + '\n' + code
                ok = run_test(full, prob['test'])
                if ok: passed += 1
                break
            except Exception as e:
                retries -= 1
                if retries == 0:
                    sys.stdout.write('  ERROR: ' + str(e)[:50] + '\n'); sys.stdout.flush()
                else:
                    time.sleep(5)
        time.sleep(3)
        if (i+1) % 10 == 0:
            sys.stdout.write('  [' + str(i+1) + '/50] passed='REDACTED'\n'); sys.stdout.flush()
    sys.stdout.write('  ' + label + ': ' + str(passed) + '/50 = ' + str(passed/50*100) + '%\n'); sys.stdout.flush()
