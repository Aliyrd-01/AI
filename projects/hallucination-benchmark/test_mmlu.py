import json, os, time, sys, io
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

# --model name — запустить одну модель
# --model name N — одна модель, N вопросов
if len(sys.argv) > 2 and sys.argv[1] == '--model':
    target = sys.argv[2].lower()
    filtered = [m for m in MODELS if m['model'] == target or LABELS.get(m['model'], '').lower() == target]
    if not filtered:
        print(f'Model "{target}" not found. Available:')
        for cfg in MODELS:
            print(f'  {cfg["model"]:45s} {LABELS.get(cfg["model"], "")}')
        sys.exit(1)
    MODELS = filtered

QUESTIONS_COUNT = 500
if len(sys.argv) > 3 and sys.argv[1] == '--model':
    QUESTIONS_COUNT = int(sys.argv[3])

# --- API functions ---

def ask_zen(m, prompt):
    payload = {
        'model': m,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 200,
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
    content = msg.get('content', '') or ''
    reasoning = msg.get('reasoning_content', '') or msg.get('reasoning', '') or ''
    return content or reasoning

def ask_google(m, prompt):
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent'
    payload = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'maxOutputTokens': 200, 'temperature': 0},
    }
    resp = requests.post(url, params={'key': GOOGLE_KEY}, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data['candidates'][0]['content']['parts'][0]['text']

def ask_mistral(m, prompt):
    payload = {
        'model': m,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 200,
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
        'max_tokens': 200,
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

def extract_letter(text):
    text = text.strip().upper()
    for ch in text:
        if ch in 'ABCD':
            return ch
    return '?'

# --- Load MMLU ---
csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mmlu_500.json')
if not os.path.exists(csv_path):
    print('mmlu_500.json not found. Run the download script first.')
    sys.exit(1)

with open(csv_path, 'r', encoding='utf-8') as f:
    questions = json.load(f)[:QUESTIONS_COUNT]

print(f'Loaded {len(questions)} MMLU questions')

# --- Subject breakdown ---
subjects = {}
for q in questions:
    s = q.get('subject', 'unknown')
    subjects[s] = subjects.get(s, 0) + 1
print(f'Subjects: {len(subjects)}')

results = {}
subject_results = {}

for cfg in MODELS:
    label = LABELS.get(cfg['model'], cfg['model'])
    print()
    print('=' * 60)
    print('Testing:', label)
    print('=' * 60)

    correct = 0
    errors = 0
    for i, q in enumerate(questions):
        choices = q['choices']
        choices_str = '\n'.join([f'{chr(65+j)}. {c}' for j, c in enumerate(choices)])

        prompt = (
            f"Question: {q['question']}\n\n"
            f"{choices_str}\n\n"
            f"Answer with ONLY the letter (A, B, C, or D):"
        )

        try:
            answer_text = ask_model(cfg, prompt)
            answer = extract_letter(answer_text)
            expected = chr(65 + q['answer'])
            is_correct = answer == expected
            if is_correct:
                correct += 1

            subject = q.get('subject', 'unknown')
            if subject not in subject_results:
                subject_results[subject] = {}
            if cfg['model'] not in subject_results[subject]:
                subject_results[subject][cfg['model']] = {'correct': 0, 'total': 0}
            subject_results[subject][cfg['model']]['total'] += 1
            if is_correct:
                subject_results[subject][cfg['model']]['correct'] += 1

            status = '+' if is_correct else '-'
            if (i + 1) % 50 == 0 or i == 0:
                print(f'  {status} [{i+1}/{len(questions)}] subj={q["subject"][:20]:20s} -> {answer}')
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f'  ! [{i+1}/{len(questions)}] ERROR: {str(e)[:50]}')

        time.sleep(DELAY)

    total_done = correct + errors
    accuracy = correct / len(questions) * 100
    results[cfg['model']] = {
        'accuracy': accuracy,
        'correct': correct,
        'total': len(questions),
        'errors': errors,
    }
    print(f'\n  Accuracy: {correct}/{len(questions)} = {accuracy:.1f}% ({errors} errors)')

    if cfg != MODELS[-1]:
        time.sleep(3)

# --- Final table ---
print()
print('=' * 70)
print('MMLU RESULTS (500 questions, 57 subjects)')
print('=' * 70)
print(f'{"Model":40s} {"Accuracy":>8s} {"Correct":>7s}')
print('-' * 57)
for cfg in MODELS:
    label = LABELS.get(cfg['model'], cfg['model'])
    r = results.get(cfg['model'], {})
    acc = r.get('accuracy', 0)
    corr = r.get('correct', 0)
    total = r.get('total', 0)
    bar = '#' * int(acc / 5)
    print(f'{label:40s} {acc:6.1f}% {corr}/{total}  {bar}')
print('-' * 57)

# --- Subject breakdown (top 10 hardest/easiest) ---
print()
print('SUBJECT BREAKDOWN (per model):')
print('-' * 70)
for model_name in [cfg['model'] for cfg in MODELS]:
    label = LABELS.get(model_name, model_name)
    print(f'\n{label}:')
    subject_accs = []
    for subj, data in subject_results.items():
        if model_name in data:
            d = data[model_name]
            acc = d['correct'] / d['total'] * 100 if d['total'] else 0
            subject_accs.append((subj, acc, d['correct'], d['total']))
    subject_accs.sort(key=lambda x: x[1])
    print(f'  Hardest: {subject_accs[0][0]:30s} {subject_accs[0][1]:5.1f}% ({subject_accs[0][2]}/{subject_accs[0][3]})')
    print(f'  Easiest: {subject_accs[-1][0]:30s} {subject_accs[-1][1]:5.1f}% ({subject_accs[-1][2]}/{subject_accs[-1][3]})')
