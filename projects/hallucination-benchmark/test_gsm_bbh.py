import time, re, json, sys, io
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
    # {'provider': 'opencode-zen', 'model': 'hy3-free'},  # 401 — модель убрана из Zen
    {'provider': 'mistral', 'model': 'mistral-medium-latest'},
    # {'provider': 'google', 'model': 'gemini-2.5-flash'},  # 403 — нет VPN
    # {'provider': 'xai', 'model': 'grok-4.5-latest'},  # 403 — нет кредитов
    {'provider': 'openrouter', 'model': 'nvidia/nemotron-3-super-120b-a12b:free'},
    {'provider': 'openrouter', 'model': 'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free'},
    {'provider': 'openrouter', 'model': 'google/gemma-4-26b-a4b-it:free'},
    {'provider': 'openrouter', 'model': 'nvidia/nemotron-3-nano-30b-a3b:free'},
    {'provider': 'openrouter', 'model': 'poolside/laguna-s-2.1:free'},
]

GSM8K_COUNT = 10
GSM8K_URL = 'https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl'
BBH_TASKS = ['date_understanding', 'logical_deduction_five_objects', 'sports_understanding']
BBH_COUNT = 4
BBH_BASE_URL = 'https://raw.githubusercontent.com/suzgunmirac/BIG-Bench-Hard/main/bbh'

LABELS = {
    'big-pickle': 'Big Pickle',
    'deepseek-v4-flash-free': 'DeepSeek V4 Flash',
    'nemotron-3-ultra-free': 'Nemotron 3 Ultra',
    'mistral-medium-latest': 'Mistral Medium 3.5',
    'gemini-2.5-flash': 'Gemini 2.5 Flash',
    'grok-4.5-latest': 'Grok 4.5 (xAI)',
    'nvidia/nemotron-3-super-120b-a12b:free': 'Nemotron 3 Super 120B',
    'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free': 'Nemotron 3 Nano Omni 30B (R)',
    'google/gemma-4-26b-a4b-it:free': 'Gemma 4 26B',
    'nvidia/nemotron-3-nano-30b-a3b:free': 'Nemotron 3 Nano 30B',
    'poolside/laguna-s-2.1:free': 'Poolside Laguna S',
}

def ask_zen(m, prompt, max_tokens):
    payload = {
        'model': m,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': max_tokens,
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

def ask_google(m, prompt, max_tokens):
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent'
    payload = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'maxOutputTokens': max_tokens},
    }
    resp = requests.post(url, params={'key': GOOGLE_KEY}, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data['candidates'][0]['content']['parts'][0]['text']

def ask_xai(m, prompt, max_tokens):
    payload = {
        'model': m,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': max_tokens,
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

def ask_mistral(m, prompt, max_tokens):
    payload = {
        'model': m,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': max_tokens,
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

def ask_openrouter(m, prompt, max_tokens):
    payload = {
        'model': m,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': max_tokens,
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
    content = msg.get('content', '') or ''
    reasoning = msg.get('reasoning_content', '') or msg.get('reasoning', '') or ''
    return content or reasoning

def ask_model(cfg, prompt, max_tokens=256):
    if cfg['provider'] == 'google':
        return ask_google(cfg['model'], prompt, max_tokens)
    if cfg['provider'] == 'xai':
        return ask_xai(cfg['model'], prompt, max_tokens)
    if cfg['provider'] == 'mistral':
        return ask_mistral(cfg['model'], prompt, max_tokens)
    if cfg['provider'] == 'openrouter':
        return ask_openrouter(cfg['model'], prompt, max_tokens)
    return ask_zen(cfg['model'], prompt, max_tokens)


def extract_gsm8k_answer(text):
    m = re.search(r'ANSWER:\s*(-?\d+\.?\d*)', text, re.IGNORECASE)
    if m:
        return m.group(1)
    nums = re.findall(r'-?\d+\.?\d*', text.replace(',', ''))
    return nums[-1] if nums else None


def extract_bbh_answer(text):
    text_upper = text.strip().upper()
    m = re.search(r'\(([A-E])\)', text_upper)
    if m:
        return m.group(1)
    m = re.search(r'\b([A-E])\b', text_upper)
    if m:
        return m.group(1)
    m = re.search(r'\b(YES|NO)\b', text_upper)
    if m:
        return m.group(1)
    return ''


# ---- Load GSM8K ----
print('Loading GSM8K...')
resp = requests.get(GSM8K_URL, timeout=30)
resp.raise_for_status()
lines = [json.loads(line) for line in resp.text.strip().splitlines()][:GSM8K_COUNT]
gsm8k_questions = []
for item in lines:
    answer_match = re.search(r'####\s*(-?\d+\.?\d*)', item['answer'])
    gsm8k_questions.append({
        'question': item['question'],
        'answer': answer_match.group(1) if answer_match else item['answer'].strip(),
    })

# ---- Load BBH ----
print('Loading BBH...')
bbh_questions = []
for task_name in BBH_TASKS:
    url = f'{BBH_BASE_URL}/{task_name}.json'
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    for ex in data['examples'][:BBH_COUNT]:
        bbh_questions.append({
            'task': task_name,
            'question': ex['input'],
            'answer': ex['target'].strip(),
        })

all_questions = (
    [('GSM8K', q) for q in gsm8k_questions] +
    [('BBH', q) for q in bbh_questions]
)

total = len(all_questions)
results = {}

for cfg in MODELS:
    label = LABELS.get(cfg['model'], cfg['model'])
    print()
    print('=' * 65)
    print('Testing:', label)
    print('=' * 65)

    gsm8k_correct = 0
    bbh_correct = 0
    gsm8k_total = 0
    bbh_total = 0

    for bench, q in all_questions:
        if bench == 'GSM8K':
            prompt = (
                'Solve the math problem step by step. At the very end, write '
                'ANSWER: followed by the number.\n\nProblem: ' + q['question']
            )
        else:
            is_yesno = q['answer'].strip().upper() in ('YES', 'NO')
            if is_yesno:
                prompt = (
                    'Answer YES or NO. Reply with exactly one word: YES or NO.\n\n'
                    + q['question']
                )
            else:
                prompt = (
                    'Choose the correct answer. Reply with one letter: A, B, C, D, or E.\n'
                    'Do NOT explain. Do NOT restate the question.\n\n'
                    + q['question']
                )

        try:
            mt = 30 if bench == 'BBH' else 256
            answer_text = ask_model(cfg, prompt, max_tokens=mt)
        except Exception as e:
            print(f'  ! [{bench}] ERROR: {str(e)[:50]}')
            time.sleep(DELAY)
            continue

        if bench == 'GSM8K':
            extracted = extract_gsm8k_answer(answer_text)
            expected_raw = q['answer']
            expected = expected_raw.rstrip('.')

            if extracted == expected:
                is_correct = True
            else:
                extracted_float = extracted.replace('$', '').replace(',', '') if extracted else None
                is_correct = extracted_float == expected

            if is_correct:
                gsm8k_correct += 1
            gsm8k_total += 1
            status = '+' if is_correct else '-'
            trimmed = answer_text[:60].replace('\n', ' ')
            print(f'  {status} [{bench}] exp={expected:>6s} got={str(extracted or "?"):>6s}  | {trimmed}')
        else:
            extracted = extract_bbh_answer(answer_text)
            target_raw = q['answer']
            target = target_raw.strip().upper().rstrip('.').lstrip('(').rstrip(')')
            is_correct = extracted == target
            if is_correct:
                bbh_correct += 1
            bbh_total += 1
            status = '+' if is_correct else '-'
            trimmed = answer_text[:60].replace('\n', ' ')
            print(f'  {status} [{q["task"]:30s}] exp={target:>6s} got={extracted:>6s}  | {trimmed}')

        time.sleep(DELAY)

    gsm8k_acc = gsm8k_correct / gsm8k_total * 100 if gsm8k_total else 0
    bbh_acc = bbh_correct / bbh_total * 100 if bbh_total else 0
    total_correct = gsm8k_correct + bbh_correct
    total_questions = gsm8k_total + bbh_total
    total_acc = total_correct / total_questions * 100 if total_questions else 0

    results[cfg['model']] = {
        'gsm8k': gsm8k_acc,
        'bbh': bbh_acc,
        'total': total_acc,
    }
    print(f'  GSM8K:  {gsm8k_correct}/{gsm8k_total} = {gsm8k_acc:.0f}%' if gsm8k_total else '  GSM8K:  N/A')
    print(f'  BBH:    {bbh_correct}/{bbh_total} = {bbh_acc:.0f}%' if bbh_total else '  BBH:    N/A')
    print(f'  TOTAL:  {total_correct}/{total_questions} = {total_acc:.0f}%' if total_questions else '  TOTAL:  N/A')

    if cfg != MODELS[-1]:
        time.sleep(2)

print()
print('=' * 65)
print('COMPARISON TABLE  |  GSM8K  |  BBH  |  TOTAL')
print('=' * 65)
print(f'{"Model":35s} {"GSM8K":>7s} {"BBH":>5s} {"Total":>6s}')
print('-' * 55)
for cfg in MODELS:
    label = LABELS.get(cfg['model'], cfg['model'])
    r = results.get(cfg['model'], {})
    g = r.get('gsm8k', 0)
    b = r.get('bbh', 0)
    t = r.get('total', 0)
    bar = '#' * int(t / 5)
    print(f'{label:35s} {g:5.0f}% {b:4.0f}% {t:5.0f}%  {bar}')
print('-' * 55)
