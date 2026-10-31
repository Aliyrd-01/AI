# The agent that fixes a repository — and is not allowed to touch the tests

*Draft for dev.to / Medium. Tags: ai, python, testing, agents*

---

Three tests were failing. I gave the agent the repository and the pytest output, and told it one
thing: the tests are the contract. You may read them, you may not change them.

It found three bugs, patched two files, and the second test run came back green: **three failed →
seven passed, tests untouched.**

This is the story of that loop, the guardrails that make it trustworthy, and the four things that
went wrong before it worked.

## The problem with "an agent that fixes code"

Ask a general-purpose agent to make failing tests pass and there is an obvious shortcut: edit the
test. Delete the assertion, relax the tolerance, mark it `xfail`. The suite goes green and the code
is still broken. You have built a very expensive `# noqa`.

So the whole design follows from one rule: **the tests are the grading harness, not part of the
work.** The agent never gets write access to `tests/`. It reads them, it gets the failure traces,
and it can only change application code. If it cannot fix the code, the run is reported as a failure
— that is an acceptable outcome, pretending is not.

## The loop

Four roles, each one a separate LLM call with its own prompt and its own model:

```
tester   → copy of the repo, run pytest, capture the baseline
planner  → read the code + the failure trace, produce a numbered list of concrete bugs
coder    → for each source file: return the full fixed file (no diff, no markdown, no tests)
tester   → run pytest on the patched copy; repeat up to 3 iterations
reporter → one markdown report: bugs → diffs → final test result
```

Different models per role turned out to matter more than I expected. Planning is the expensive step
and rewards a big reasoning model. Writing a 40-line fix to a small file does not — a cheaper, faster
coder model gets the same result with fewer tokens burned.

The loop itself is boring on purpose:

```python
for attempt in range(1, 4):          # hard cap: 3 iterations
    for rel, code in sources.items():
        fixed = ask_coder(rel, code, bugs, last_test_output)
        if fixed:
            write(fixed_dir / rel, fixed)
    passed, last_test_output = run_tests(fixed_dir)
    if passed:
        break
```

Three rules encoded in those ten lines:

1. **Bounded retries.** No "keep going until it works". Three attempts, then a report that says
   FAILED. Unbounded loops burn money and hide the fact that the model is stuck.
2. **Feedback is the real test output**, not my opinion of the previous answer. Each iteration gets
   the new pytest trace, so the next patch is driven by evidence.
3. **The exit code is the only truth.** Not "I have fixed the issues" — `returncode == 0`.

## The demo repository: three bugs, one of each flavour

The sample repo is deliberately small — an inventory module and a pricing module, seven tests. The
three failures are the three bugs you actually meet in code review:

**1. The overwrite.** Adding an item to stock replaced the quantity instead of accumulating it:

```python
# before
def add_item(stock, name, qty):
    stock[name] = qty

# after
def add_item(stock, name, qty):
    stock[name] = stock.get(name, 0) + qty
```

**2. The missing guard.** Withdrawing more than you have produced negative stock silently:

```python
# before
def remove_item(stock, name, qty):
    if name not in stock:
        raise KeyError(name)
    stock[name] -= qty
    return stock[name]

# after
def remove_item(stock, name, qty):
    if name not in stock:
        raise KeyError(name)
    if qty > stock[name]:
        raise ValueError(f"not enough {name}")
    stock[name] -= qty
    return stock[name]
```

**3. The wrong exception type.** Pricing raised `KeyError` when a price was missing, but the contract
(and the test) asked for a `ValueError` with the item named:

```python
# before
total += qty * prices[name]            # KeyError

# after
if name not in prices:
    raise ValueError(f"no price for {name}")
total += qty * prices[name]
```

Baseline, before the agent runs:

```
FAILED tests/test_inventory.py::test_add_item_accumulates_existing
FAILED tests/test_inventory.py::test_remove_item_rejects_negative_stock
FAILED tests/test_inventory.py::test_total_value_missing_price
3 failed, 4 passed
```

After the fixes: `7 passed`. Two files changed. The test file has the same hash it had at the
start.

## Guardrails: generated code is untrusted code

An agent that writes files and then executes a test runner is an agent that can run arbitrary code
on your machine. That is the part most tutorials skip.

**Static check before the file is ever written.** Every model output is parsed with `ast` and
rejected if it imports or calls anything that can leave the sandbox:

```python
FORBIDDEN_MODULES = {"subprocess", "socket", "http", "urllib", "requests",
                     "ctypes", "pty", "multiprocessing", "threading", "importlib"}
FORBIDDEN_CALLS   = {"eval", "exec", "compile", "__import__", "breakpoint"}
FORBIDDEN_ATTRS   = {"__subclasses__", "__globals__", "__code__", "__builtins__"}
```

It also catches the syntax errors that show up when a model returns half a file, and gives the coder
exactly one retry with the compiler message — then gives up on that file.

**The test process does not inherit your secrets.** The runner gets a cleaned environment: any
variable whose name contains `KEY`, `SECRET`, `TOKEN`, `PASS`, `AUTH`, `CREDENTIAL` or `DATABASE` is
dropped before pytest starts. A prompt-injected `print(os.environ)` finds nothing useful.

**Docker is one flag away.** Set `DOCKER_SANDBOX=1` and pytest runs inside `python:3.11-slim` with
`--network none` and a 256 MB memory cap. Default is the stripped-environment local run, because
that is what CI already gives you.

## What actually went wrong (the useful part)

**1. The agent cheats if you let it.** My first version passed the whole directory, tests included,
and "fixed" two failures by weakening assertions. Read-only tests are not a nicety, they are the
design. This is the single most important line in the whole project.

**2. Markdown fences break everything.** "Return only the file content" is obeyed maybe 90% of the
time; the other 10% comes back wrapped in ````python`. Strip fences, compile-check, retry once.

**3. Full-file rewrite beats a diff.** I tried asking for unified diffs — models produce diffs that
almost apply. Returning the complete file is dumber and vastly more reliable at this file size.

**4. A failing run must look like a failing run.** My reporter used to write confident prose about
"the fix" even when the final pytest still failed, because the prompt said "describe what changed".
Now the pass/fail status is injected into the report header from the exit code. The model never gets
to have an opinion about whether the build is green.

## Why this is worth building

The same loop works on a real repository: point it at the directory, give it the failing test names,
cap the iterations, and read the report. What you get at the end is not a chat transcript — it is a
folder that proves itself:

```
repo_run_20261024_183012/
  report.md            # bugs → diffs → final result
  baseline_pytest.txt  # 3 failed, 4 passed
  final_pytest.txt     # 7 passed
  repo_baseline/       # untouched copy
  repo_fixed/          # patched copy
  run_info.json        # models used, pass/fail, files changed
```

Anyone can rerun `pytest` in `repo_fixed/` and check the claim in ten seconds. That is the difference
between a demo and a result.

If you are building something similar, the three things I would copy first: read-only tests, a hard
iteration cap, and the exit code as the only source of truth.

---

**Links**
- Full walkthrough (video): https://youtu.be/FMtkY-XuE-s
- Code and other cases: https://github.com/Aliyrd-01/AI
- Portfolio with the rest of the builds: *(link on publish)*

---

## Notes before publishing

- Images to upload at the top of the matching sections (files live on disk, upload manually):
  baseline terminal output, the fix diff, and the green run.
- Do not paste local paths, credentials or model-provider keys — none are in this text.
- A Russian version can be produced from the same text if the post goes to a RU channel.
