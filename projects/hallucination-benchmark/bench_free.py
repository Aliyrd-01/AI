import json, csv, io, os, time, re, sys
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ZEN_KEY = 'REDACTED_KEY'
URL = 'https://opencode.ai/zen/v1/chat/completions'
DELAY = 1
QUESTIONS_COUNT = 20
RESULTS_FILE = os.path.join(os.path.dirname(__file__), 'bench_free_results.json')

# jev-1.13-free исключён: это не LLM (structured decision model, /zen/v1/systemone),
# к TQA/GSM8K/BBH через /chat/completions неприменим.
MODELS = [
    'big-pickle',
    'fledge-alpha-free',
    'longcat-2.5-preview-free',
    'ling-3.1-flash-free',
    'mimo-v2.5-free',
    'mimo-v2.6-flash-free',
    'muse-spark-1.2-contributor-free',
    'muse-spark-1.3-contributor-free',
    'nemotron-3.5-lightning-free',
    'space-bunny-free',
]

LABELS = {
    'big-pickle': 'Big Pickle',
    'fledge-alpha-free': 'Fledge Alpha',
    'longcat-2.5-preview-free': 'LongCat 2.5 Preview',
    'ling-3.1-flash-free': 'Ling 3.1 Flash',
    'mimo-v2.5-free': 'MiMo V2.5',
    'mimo-v2.6-flash-free': 'MiMo V2.6 Flash',
    'muse-spark-1.2-contributor-free': 'Muse Spark 1.2 (contrib)',
    'muse-spark-1.3-contributor-free': 'Muse Spark 1.3 (contrib)',
    'nemotron-3.5-lightning-free': 'Nemotron 3.5 Lightning',
    'space-bunny-free': 'Space Bunny',
    # уже выведены из ротации Zen — остаются только в отчёте
    'deepseek-v4-flash-free': 'DeepSeek V4 Flash Free',
    'laguna-s-2.1-free': 'Laguna S 2.1',
    'ling-3.0-flash-fin-free': 'Ling 3.0 Flash FIN',
    'nemotron-3-ultra-free': 'Nemotron 3 Ultra',
}

GSM8K_COUNT = 10
GSM8K_URL = 'https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl'
BBH_TASKS = ['date_understanding', 'logical_deduction_five_objects', 'sports_understanding']
BBH_COUNT = 4
BBH_BASE_URL = 'https://raw.githubusercontent.com/suzgunmirac/BIG-Bench-Hard/main/bbh'


CIRCUIT_TRIP = 4
_FAIL = {'n': 0}


def ask_raw(model, prompt, max_tokens):
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': max_tokens,
    }
    resp = requests.post(
        URL,
        json=payload,
        headers={'Authorization': 'Bearer ' + ZEN_KEY, 'Content-Type': 'application/json'},
        timeout=180,
    )
    resp.raise_for_status()
    data = resp.json()
    choices = data.get('choices', [])
    if not choices:
        return ''
    msg = choices[0].get('message', {})
    content = msg.get('content', '') or ''
    reasoning = msg.get('reasoning_content', '') or msg.get('reasoning', '') or ''
    return (content or reasoning).strip()


def ask(model, prompt, max_tokens, attempts=6):
    # Circuit breaker: при недоступном инференсе без него каждый вопрос
    # тратил бы 6 попыток (~252 запроса на модель вместо ~5).
    if _FAIL['n'] >= CIRCUIT_TRIP:
        raise RuntimeError('circuit open: Zen inference unreachable')
    last_err = 'empty response'
    for i in range(attempts):
        try:
            text = ask_raw(model, prompt, max_tokens)
            if text:
                _FAIL['n'] = 0
                return text
            last_err = 'empty response'
        except Exception as e:
            last_err = str(e)[:80]
        _FAIL['n'] += 1
        if _FAIL['n'] >= CIRCUIT_TRIP:
            break
        time.sleep(6 + i * 3)
    raise RuntimeError(last_err)


def precheck():
    available = []
    skipped = []
    print('=' * 65)
    print('PRE-CHECK')
    print('=' * 65)
    for m in MODELS:
        label = LABELS.get(m, m)
        try:
            t = ask_raw(m, 'Say OK', 300)
            ok = bool(t)
        except Exception:
            ok = False
        status = 'OK  ' if ok else 'SKIP'
        print(f'  [{status}] {label}')
        (available if ok else skipped).append(m)
        time.sleep(2)
    print()
    if skipped:
        print('Skipped (unavailable now): ' + ', '.join(LABELS.get(m, m) for m in skipped))
    print('Will test: ' + ', '.join(LABELS.get(m, m) for m in available))
    print()
    return available


def load_tqa():
    csv_path = os.path.join(os.path.dirname(__file__), 'TruthfulQA.csv')
    with open(csv_path, 'r', encoding='utf-8') as f:
        data = f.read()
    reader = csv.DictReader(io.StringIO(data))
    return list(reader)[:QUESTIONS_COUNT]


def extract_letter(text):
    for ch in text.strip().upper():
        if ch in 'ABCD':
            return ch
    return '?'


def run_tqa(models):
    questions = load_tqa()
    results = load_results()
    results.setdefault('tqa', {})
    for m in models:
        label = LABELS.get(m, m)
        prev = results['tqa'].get(m) or {}
        # 'n' = сколько вопросов уже обработано. Старые записи без 'n'
        # считаются незаконченными и прогоняются заново.
        start = prev.get('n', 0)
        # запись с ошибками = провал, а не «прогон» — перезапускаем с нуля
        if start >= len(questions) and prev.get('errors', 0) == 0:
            print(f'[skip] TruthfulQA: {label} уже прогонян ({prev.get("acc", 0):.0f}%)')
            continue
        if start >= len(questions):
            print(f'[redo] TruthfulQA: {label} — {prev["errors"]} ошибок, прогоняю заново')
            start = 0
            prev = {}
        print('=' * 65)
        print(f'TruthfulQA: {label}{" (resume с " + str(start + 1) + ")" if start else ""}')
        print('=' * 65)
        # при start=0 сбрасываем счётчики, иначе старый correct/incorrect
        # сложится с новыми
        correct = prev.get('correct', 0) if start else 0
        errors = prev.get('errors', 0) if start else 0
        # пишем в файл после каждого вопроса: при обрыве прогона
        # теряется максимум один ответ, а не вся модель (~40 мин)
        results['tqa'][m] = {'correct': correct, 'answered': start - errors, 'errors': errors,
                             'acc': 0.0, 'n': start}
        save_results(results)
        for i in range(start, len(questions)):
            q = questions[i]
            best = q['Best Answer']
            incorrect_raw = q['Incorrect Answers']
            incorrect = incorrect_raw.split(';')[:3] if incorrect_raw else ["I don't know"]
            choices = ['A. ' + best] + [chr(66 + j) + '. ' + inc.strip() for j, inc in enumerate(incorrect)]
            prompt = (
                'Answer the question. Choose the correct letter.\n\n'
                'Question: ' + q['Question'] + '\n\n'
                + '\n'.join(choices) + '\n\n'
                'Reply with ONLY the letter (A, B, C, or D):'
            )
            try:
                answer_text = ask(m, prompt, 800)
                answer = extract_letter(answer_text)
                is_correct = answer == 'A'
                if is_correct:
                    correct += 1
                status = '+' if is_correct else '-'
                print(f'  {status} [{i+1}/{len(questions)}] -> {answer}')
            except Exception as e:
                errors += 1
                print(f'  ! [{i+1}/{len(questions)}] ERROR: {str(e)[:60]}')
            processed = i + 1
            answered = processed - errors
            results['tqa'][m] = {'correct': correct, 'answered': answered, 'errors': errors,
                                 'acc': correct / max(1, answered) * 100, 'n': processed}
            save_results(results)
            time.sleep(DELAY)
        answered = len(questions) - errors
        acc = correct / answered * 100 if answered else 0
        results['tqa'][m] = {'correct': correct, 'answered': answered, 'errors': errors,
                             'acc': acc, 'n': len(questions)}
        save_results(results)
        print(f'  ---> Accuracy: {correct}/{answered} = {acc:.0f}% ({errors} errors)')
        print()
        time.sleep(2)


def load_gsm_bbh():
    resp = requests.get(GSM8K_URL, timeout=30)
    resp.raise_for_status()
    lines = [json.loads(line) for line in resp.text.strip().splitlines()][:GSM8K_COUNT]
    gsm8k = []
    for item in lines:
        m = re.search(r'####\s*(-?\d+\.?\d*)', item['answer'])
        gsm8k.append({'question': item['question'], 'answer': m.group(1) if m else item['answer'].strip()})
    bbh = []
    for task_name in BBH_TASKS:
        resp = requests.get(f'{BBH_BASE_URL}/{task_name}.json', timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for ex in data['examples'][:BBH_COUNT]:
            bbh.append({'task': task_name, 'question': ex['input'], 'answer': ex['target'].strip()})
    return [('GSM8K', q) for q in gsm8k] + [('BBH', q) for q in bbh]


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


def run_gsm_bbh(models):
    all_questions = load_gsm_bbh()
    results = load_results()
    results.setdefault('gsm_bbh', {})
    for m in models:
        label = LABELS.get(m, m)
        prev = results['gsm_bbh'].get(m) or {}
        # 'n' = сколько вопросов уже обработано (10 GSM + 12 BBH = 22)
        start = prev.get('n', 0)
        if start >= len(all_questions):
            print(f'[skip] GSM+BBH: {label} уже прогонян ({prev.get("total", 0):.0f}%)')
            continue
        print('=' * 65)
        print(f'GSM8K + BBH: {label}{" (resume с " + str(start + 1) + ")" if start else ""}')
        print('=' * 65)

        st = {'g_c': prev.get('gsm8k_correct', 0) if start else 0,
              'b_c': prev.get('bbh_correct', 0) if start else 0,
              'g_t': prev.get('gsm8k_total', 0) if start else 0,
              'b_t': prev.get('bbh_total', 0) if start else 0,
              'n': start}

        def commit():
            results['gsm_bbh'][m] = {
                'gsm8k_correct': st['g_c'], 'gsm8k_total': st['g_t'],
                'gsm8k': st['g_c'] / st['g_t'] * 100 if st['g_t'] else 0,
                'bbh_correct': st['b_c'], 'bbh_total': st['b_t'],
                'bbh': st['b_c'] / st['b_t'] * 100 if st['b_t'] else 0,
                'total': (st['g_c'] + st['b_c']) / (st['g_t'] + st['b_t']) * 100
                if (st['g_t'] + st['b_t']) else 0,
                'n': st['n'],
            }
            save_results(results)

        for idx in range(start, len(all_questions)):
            bench, q = all_questions[idx]
            if bench == 'GSM8K':
                prompt = (
                    'Solve the math problem step by step. At the very end, write '
                    'ANSWER: followed by the number.\n\nProblem: ' + q['question']
                )
            else:
                is_yesno = q['answer'].strip().upper() in ('YES', 'NO')
                if is_yesno:
                    prompt = 'Answer YES or NO. Reply with exactly one word: YES or NO.\n\n' + q['question']
                else:
                    prompt = (
                        'Choose the correct answer. Reply with one letter: A, B, C, D, or E.\n'
                        'Do NOT explain. Do NOT restate the question.\n\n' + q['question']
                    )
            try:
                mt = 1500 if bench == 'GSM8K' else 800
                answer_text = ask(m, prompt, mt)
            except Exception as e:
                print(f'  ! [{bench}] ERROR: {str(e)[:60]}')
                st['n'] = idx + 1
                commit()
                time.sleep(DELAY)
                continue

            if bench == 'GSM8K':
                extracted = extract_gsm8k_answer(answer_text)
                expected = q['answer'].rstrip('.')
                is_correct = extracted == expected or (extracted or '') == expected
                st['g_t'] += 1
                if is_correct:
                    st['g_c'] += 1
                status = '+' if is_correct else '-'
                trimmed = answer_text[:55].replace('\n', ' ')
                print(f'  {status} [GSM8K] exp={expected:>6s} got={str(extracted or "?"):>6s} | {trimmed}')
            else:
                extracted = extract_bbh_answer(answer_text)
                target = q['answer'].strip().upper().rstrip('.').lstrip('(').rstrip(')')
                is_correct = extracted == target
                st['b_t'] += 1
                if is_correct:
                    st['b_c'] += 1
                status = '+' if is_correct else '-'
                trimmed = answer_text[:55].replace('\n', ' ')
                print(f'  {status} [{q["task"][:28]:28s}] exp={target:>5s} got={extracted:>5s} | {trimmed}')
            st['n'] = idx + 1
            commit()
            time.sleep(DELAY)

        results = load_results()
        cur = results['gsm_bbh'].get(m, {})
        print(f'  GSM8K: {cur.get("gsm8k_correct")}/{cur.get("gsm8k_total")} = {cur.get("gsm8k", 0):.0f}%'
              f'   BBH: {cur.get("bbh_correct")}/{cur.get("bbh_total")} = {cur.get("bbh", 0):.0f}%'
              f'   TOTAL: {cur.get("total", 0):.0f}%')
        print()
        time.sleep(2)


def load_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_results(results):
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def print_table():
    results = load_results()
    tqa = results.get('tqa', {})
    gb = results.get('gsm_bbh', {})
    print()
    print('=' * 78)
    print(f'{"Model":28s} {"TruthfulQA":>11s} {"GSM8K":>7s} {"BBH":>6s} {"Math+Logic":>11s}')
    print('-' * 78)
    rows = [m for m in dict.fromkeys(list(MODELS) + list(tqa) + list(gb)) if m in tqa or m in gb]
    for m in rows:
        label = LABELS.get(m, m)
        t = tqa.get(m, {}).get('acc')
        g = gb.get(m, {}).get('gsm8k')
        b = gb.get(m, {}).get('bbh')
        tot = gb.get(m, {}).get('total')
        fmt = lambda v: f'{v:9.0f}%' if v is not None else '      n/a'
        print(f'{label:28s} {fmt(t):>11s} {fmt(g):>7s} {fmt(b):>6s} {fmt(tot):>11s}')
    print('-' * 78)


if __name__ == '__main__':
    phase = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if phase == 'table':
        print_table()
        sys.exit(0)
    models = precheck()
    if not models:
        print('No models available.')
        sys.exit(1)
    if phase in ('tqa', 'all'):
        run_tqa(models)
    if phase in ('gsm', 'all'):
        run_gsm_bbh(models)
    print_table()
