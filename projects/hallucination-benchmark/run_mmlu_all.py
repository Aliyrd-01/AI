import json, os, time, sys, io
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

QUESTIONS_COUNT = 50

def ask(provider, model, prompt):
    if provider == 'opencode-zen':
        payload = {'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 200, 'temperature': 0}
        resp = requests.post('https://opencode.ai/zen/v1/chat/completions', json=payload,
            headers={'Authorization': 'Bearer ' + ZEN_KEY, 'Content-Type': 'application/json'}, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        msg = data['choices'][0]['message']
        return msg.get('content', '') or msg.get('reasoning_content', '') or msg.get('reasoning', '') or ''
    elif provider == 'mistral':
        payload = {'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 200, 'temperature': 0}
        resp = requests.post('https://api.mistral.ai/v1/chat/completions', json=payload,
            headers={'Authorization': 'Bearer ' + MISTRAL_KEY, 'Content-Type': 'application/json'}, timeout=60)
        resp.raise_for_status()
        return resp.json()['choices'][0]['message'].get('content', '') or ''
    elif provider == 'openrouter':
        payload = {'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 200, 'temperature': 0}
        resp = requests.post('https://openrouter.ai/api/v1/chat/completions', json=payload,
            headers={'Authorization': 'Bearer ' + OPENROUTER_KEY, 'Content-Type': 'application/json'}, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        msg = data['choices'][0]['message']
        return msg.get('content', '') or msg.get('reasoning_content', '') or msg.get('reasoning', '') or ''
    return ''

def extract_letter(text):
    for ch in text.strip().upper():
        if ch in 'ABCD':
            return ch
    return '?'

with open('D:\\AI\\hallucination-benchmark\\mmlu_500.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)[:QUESTIONS_COUNT]

log_path = 'D:\\AI\\hallucination-benchmark\\mmlu_results.json'
results = {}

for provider, model, label in MODELS:
    sys.stdout.write(f'\nTesting: {label}\n')
    sys.stdout.flush()
    correct = 0
    errors = 0
    for i, q in enumerate(questions):
        choices_str = '\n'.join([f'{chr(65+j)}. {c}' for j, c in enumerate(q['choices'])])
        prompt = f"Question: {q['question']}\n\n{choices_str}\n\nAnswer with ONLY the letter (A, B, C, or D):"
        try:
            answer_text = ask(provider, model, prompt)
            answer = extract_letter(answer_text)
            expected = chr(65 + q['answer'])
            if answer == expected:
                correct += 1
        except Exception as e:
            errors += 1
            if errors <= 2:
                sys.stdout.write(f'  ERROR: {str(e)[:60]}\n')
                sys.stdout.flush()
        time.sleep(DELAY)

    acc = correct / len(questions) * 100
    results[model] = {'label': label, 'accuracy': acc, 'correct': correct, 'total': len(questions), 'errors': errors}
    sys.stdout.write(f'  {label}: {correct}/{len(questions)} = {acc:.1f}%\n')
    sys.stdout.flush()
    time.sleep(2)

with open(log_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

sys.stdout.write('\n' + '=' * 55 + '\n')
sys.stdout.write(f'{"Model":35s} {"MMLU":>7s}\n')
sys.stdout.write('-' * 55 + '\n')
for _, model, label in MODELS:
    r = results.get(model, {})
    acc = r.get('accuracy', 0)
    bar = '#' * int(acc / 5)
    sys.stdout.write(f'{label:35s} {acc:5.1f}%  {bar}\n')
sys.stdout.write('-' * 55 + '\n')
sys.stdout.flush()
