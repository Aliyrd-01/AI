import json, csv, io, os, time, sys
import requests

ZEN_KEY = 'REDACTED_KEY'
GOOGLE_KEY = 'REDACTED_KEY'
XAI_KEY = 'REDACTED_KEY'
MISTRAL_KEY = 'REDACTED_KEY'
QUESTIONS_COUNT = 20
DELAY = 1

MODELS = [
    {'provider': 'opencode-zen', 'model': 'big-pickle'},
    {'provider': 'opencode-zen', 'model': 'deepseek-v4-flash-free'},
    {'provider': 'opencode-zen', 'model': 'nemotron-3-ultra-free'},
    # {'provider': 'opencode-zen', 'model': 'hy3-free'},  # 401 — модель убрана из Zen
    {'provider': 'mistral', 'model': 'mistral-medium-latest'},
    {'provider': 'google', 'model': 'gemini-2.5-flash'},
    {'provider': 'xai', 'model': 'grok-4.5-latest'},
]

LABELS = {
    'big-pickle': 'Big Pickle',
    'deepseek-v4-flash-free': 'DeepSeek V4 Flash',
    'nemotron-3-ultra-free': 'Nemotron 3 Ultra',
    'mistral-medium-latest': 'Mistral Medium 3.5',
    'gemini-2.5-flash': 'Gemini 2.5 Flash',
    'grok-4.5-latest': 'Grok 4.5 (xAI)',
}

# --model name — запустить одну модель
# --model name N — одна модель, N вопросов
if len(sys.argv) > 2 and sys.argv[1] == '--model':
    target = sys.argv[2].lower()
    filtered = [m for m in MODELS if m['model'] == target or LABELS.get(m['model'], '').lower() == target]
    if not filtered:
        print(f'Model "{target}" not found. Available:')
        for cfg in MODELS:
            print(f'  {cfg["model"]:35s} {LABELS.get(cfg["model"], "")}')
        sys.exit(1)
    MODELS = filtered
    if len(sys.argv) > 3:
        QUESTIONS_COUNT = int(sys.argv[3])

def ask_zen(m, prompt):
    payload = {
        'model': m,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 500,
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
    content = msg.get('content', '') or ''
    reasoning = msg.get('reasoning_content', '') or msg.get('reasoning', '') or ''
    return content or reasoning

def ask_google(m, prompt):
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent'
    payload = {'contents': [{'parts': [{'text': prompt}]}]}
    resp = requests.post(url, params={'key': GOOGLE_KEY}, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data['candidates'][0]['content']['parts'][0]['text']

def ask_xai(m, prompt):
    payload = {
        'model': m,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 500,
    }
    resp = requests.post(
        'https://api.x.ai/v1/chat/completions',
        json=payload,
        headers={'Authorization': 'Bearer ' + XAI_KEY, 'Content-Type': 'application/json'},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    choices = data.get('choices', [])
    if not choices:
        return ''
    msg = choices[0].get('message', {})
    return msg.get('content', '') or ''

def ask_mistral(m, prompt):
    payload = {
        'model': m,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 500,
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

def ask_model(cfg, prompt):
    if cfg['provider'] == 'google':
        return ask_google(cfg['model'], prompt)
    if cfg['provider'] == 'xai':
        return ask_xai(cfg['model'], prompt)
    if cfg['provider'] == 'mistral':
        return ask_mistral(cfg['model'], prompt)
    return ask_zen(cfg['model'], prompt)

def extract_letter(text):
    for ch in text.strip().upper():
        if ch in 'ABCD':
            return ch
    return '?'

# Load dataset
csv_path = os.path.join(os.path.dirname(__file__), 'TruthfulQA.csv')
if os.path.exists(csv_path):
    with open(csv_path, 'r', encoding='utf-8') as f:
        data = f.read()
else:
    print('Downloading TruthfulQA...')
    url = 'https://raw.githubusercontent.com/sylinrl/TruthfulQA/main/TruthfulQA.csv'
    resp = requests.get(url, timeout=30)
    data = resp.text
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(data)

reader = csv.DictReader(io.StringIO(data))
all_questions = list(reader)[:QUESTIONS_COUNT]

results = {}

for cfg in MODELS:
    label = LABELS.get(cfg['model'], cfg['model'])
    print()
    print('=' * 60)
    print('Testing:', label)
    print('=' * 60)

    correct = 0
    for i, q in enumerate(all_questions):
        best = q['Best Answer']
        incorrect_raw = q['Incorrect Answers']
        incorrect = incorrect_raw.split(';')[:3] if incorrect_raw else ["I don't know"]
        choices = ['A. ' + best] + [chr(66 + j) + '. ' + inc.strip() for j, inc in enumerate(incorrect)]
        choices_str = '\n'.join(choices)

        prompt = (
            'Answer the question. Choose the correct letter.\n\n'
            + 'Question: ' + q['Question'] + '\n\n'
            + choices_str + '\n\n'
            + 'Reply with ONLY the letter (A, B, C, or D):'
        )

        try:
            answer_text = ask_model(cfg, prompt)
            answer = extract_letter(answer_text)
            is_correct = answer == 'A'
            if is_correct:
                correct += 1
            status = '+' if is_correct else '-'
            print(f'  {status} [{i+1}/{QUESTIONS_COUNT}] -> {answer}')
        except Exception as e:
            print(f'  ! [{i+1}/{QUESTIONS_COUNT}] ERROR: {str(e)[:50]}')

        time.sleep(DELAY)

    accuracy = correct / len(all_questions) * 100
    results[cfg['model']] = accuracy
    print(f'  ---> Accuracy: {correct}/{len(all_questions)} = {accuracy:.0f}%')

    if cfg != MODELS[-1]:
        time.sleep(3)

print()
print('=' * 60)
print('COMPARISON TABLE')
print('=' * 60)
print(f'{"Model":35s} {"Accuracy":>8s}')
print('-' * 45)
for cfg in MODELS:
    label = LABELS.get(cfg['model'], cfg['model'])
    acc = results.get(cfg['model'], 0)
    bar = '#' * int(acc / 5)
    print(f'{label:35s} {acc:6.0f}%  {bar}')
print('-' * 45)
