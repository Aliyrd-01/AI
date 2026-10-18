"""EN plan for the n8n demo videos (same frames/shots, English voiceover).

One voice (Piper en_US-ryan-high), slowed down (length-scale 1.3), detailed
business narration, same step structure as the RU plan (n8n_video_plan.py).

Run: python n8n_video_plan_en.py
Result: n8n_video_plan_en.json + docs/vo_n8n_en/<key>_<i>.wav + <key>_vo.wav
"""

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VO_DIR = os.path.join(HERE, "docs", "vo_n8n_en")
SHOT_DIR = os.path.join(HERE, "docs", "n8n_shots")
PIPER = os.path.join(HERE, "tools", "voices", "en_US-ryan-high.onnx")
PLAN = os.path.join(HERE, "n8n_video_plan_en.json")
SLOW = "1.3"  # length-scale: >1 = slower / clearer
SILENCE = "0.5"  # pause between sentences

try:
    from imageio_ffmpeg import get_ffmpeg_exe
    FFMPEG = get_ffmpeg_exe()
except Exception:  # noqa: BLE001
    FFMPEG = "ffmpeg"

PLANS = {
    "leadqual_demo": {
        "workflow_id": "R6TUfWY5jcGwZupm",
        "steps": [
            {"node": None, "text":
                "This workflow automates the qualification and scoring of incoming B2B leads. "
                "The goal is to instantly gauge how promising a lead is, and to hand it to a "
                "manager at the right moment. Let's walk through the pipeline step by step."},
            {"node": "Webhook", "text":
                "Step one — intake. Leads arrive from a website form through a webhook. The source "
                "can be a custom form, Typeform, or Google Forms — the pipeline is universal and "
                "not tied to any single service."},
            {"node": "Validate Lead", "text":
                "Step two — contact validation. The system checks that the email and phone number "
                "are well-formed. Invalid submissions are filtered out automatically, and the team "
                "gets a system notification. This keeps junk requests out of the funnel."},
            {"node": "Enrich Contact (Postgres)", "text":
                "Step three — enrichment. The workflow queries the corporate database and loads the "
                "company profile: industry, business size, and the contact person's role. If the "
                "contact is already in the system, their interaction history is pulled in as well. "
                "This provides the context needed for an accurate assessment."},
            {"node": "Qubax API A", "text":
                "Step four — intelligent scoring. A language model rates the lead on a "
                "hundred-point scale. This is an A/B setup: two independent prompts — conservative "
                "and expanded. The first sticks strictly to the facts, the second also weighs the "
                "account's growth potential. Together they produce a more objective score."},
            {"node": "Score > 70?", "text":
                "Step five — hot lead routing. If the score is above seventy, a manager instantly "
                "receives a card in Telegram: contacts, company, and the scoring rationale. "
                "A promising lead never waits in a manual review queue."},
            {"node": "Save Lead (Postgres)", "text":
                "Step six — CRM and analytics. All data is synced to the PostgreSQL database, "
                "keeping the sales funnel up to date. At the same time, model request costs and "
                "A/B statistics are recorded — so it's clear which prompt scores more accurately."},
            {"node": None, "text":
                "The outcome: instant response to promising deals, transparent analytics, and "
                "fully automated routine lead qualification."},
        ],
    },
    "news_demo": {
        "workflow_id": "YAyuG9GA2jUeICG2",
        "steps": [
            {"node": None, "text":
                "This workflow is an autonomous news desk. The pipeline collects stories from "
                "seven sources, filters out duplicates and irrelevant notes, translates them with "
                "a language model, and publishes ready-to-read posts to Telegram — with no human "
                "involved. Let's walk through the architecture step by step."},
            {"node": "RSS Forklog", "text":
                "Step one — collection. The workflow runs on a schedule and pulls fresh articles "
                "from seven topical feeds: crypto, artificial intelligence, and technology. Each "
                "source has its own schedule, so the stream of material stays even."},
            {"node": "Deduplication", "text":
                "Step two — the unified deduplicator. It compares links within a batch and against "
                "the publication history: titles are matched by similarity, and the registry of "
                "processed items updates automatically. Duplicates are filtered out before any "
                "language model call — which saves tokens."},
            {"node": "Interest Pre-Filter", "text":
                "Step three — topic detector and interest filter. The system determines what the "
                "piece is about — crypto or AI — and rates how interesting it is for the audience. "
                "Ads, giveaways, and junk notes are discarded; relevant material moves on."},
            {"node": "AI Translate", "text":
                "Step four — AI analysis. The language model translates the piece, condenses it to "
                "three or four sentences, adds an analytical takeaway, and rates relevance on a "
                "hundred-point scale. A post is dropped if the score is below the threshold, and "
                "the request cost is logged to the usage table."},
            {"node": "Telegram (Photo)", "text":
                "Step five — media and publishing. The cover image comes from the source; if it's "
                "missing or unavailable, an image search service is queried, and if that also "
                "fails the post goes out as text. The formatting: headline, summary, takeaway, "
                "tags, and a link to the original."},
            {"node": None, "text":
                "The outcome: a continuous stream of filtered, translated, and structured content "
                "in Telegram — with cost control and no manual work."},
        ],
    },
    "support_demo": {
        "workflow_id": "r7MQeVmaInZXmyYK",
        "steps": [
            {"node": None, "text":
                "This workflow is a smart support desk in Telegram. It answers routine questions "
                "from a knowledge base on its own, and escalates complex cases to a human "
                "operator. Let's walk through the pipeline step by step."},
            {"node": "Telegram Trigger", "text":
                "Step one — message intake. The Telegram trigger listens to the chat in real time "
                "and accepts both customer requests and operator replies. A single entry point — "
                "from there, the logic branches by role."},
            {"node": "Register User", "text":
                "Step two — request registration. The user is recorded in the user_states table of "
                "the PostgreSQL database: chat ID, name, and dialog state are stored. A "
                "parameterized upsert prevents duplicates and determines how the following "
                "messages are handled."},
            {"node": "Classify", "text":
                "Step three — classification. A neural classifier assigns the request to a "
                "category: a routine question that can be closed automatically, or a handoff to a "
                "human. Ambiguous cases also go to the operator — thanks to the fallback "
                "category."},
            {"node": "AI Response", "text":
                "Step four — automatic answer. The workflow calls a local RAG service: hybrid "
                "search over the knowledge base finds relevant fragments, and a language model "
                "drafts the answer. The service returns the finished text along with a flag for "
                "whether the answer was found in the base."},
            {"node": "RAG Answered?", "text":
                "Step five — quality check. If the answer was found in the knowledge base, it goes "
                "straight to the customer. If the information isn't there, the pipeline doesn't "
                "make things up: the request is honestly escalated to a human operator."},
            {"node": "Alert Operator", "text":
                "Step six — the operator's side. An alert with the customer's ID and the question "
                "text is sent to Telegram. To reply, the operator uses Telegram's Reply on the "
                "alert — the system extracts the ID and delivers the answer to the customer. The "
                "close command ends the dialog and resets the mode back to the bot."},
            {"node": None, "text":
                "The outcome: routine questions are closed instantly and without a human, while "
                "complex requests are never lost — they reach the operator together with the "
                "context. Every dialog's state is stored in PostgreSQL."},
        ],
    },
}


def duration(path: str) -> float:
    p = subprocess.run([FFMPEG, "-i", path], capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", p.stderr or "")
    if not m:
        return 5.0
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def tts(text: str, out_wav: str):
    txt = os.path.join(VO_DIR, "step.txt")
    with open(txt, "w", encoding="utf-8") as f:
        f.write(text)
    subprocess.run([sys.executable, "-m", "piper", "-m", PIPER, "-c", PIPER + ".json",
                    "-f", out_wav, "-i", txt, "--length-scale", SLOW,
                    "--sentence-silence", SILENCE], check=True)


def build():
    os.makedirs(VO_DIR, exist_ok=True)
    plan = {}
    for key, spec in PLANS.items():
        steps, audios = [], []
        for i, st in enumerate(spec["steps"]):
            a = os.path.join(VO_DIR, f"{key}_{i:02d}.wav")
            tts(st["text"], a)
            d = duration(a)
            steps.append({"node": st["node"], "text": st["text"], "audio": a,
                          "duration": round(d + 0.8, 2)})
            audios.append(a)
        lst = os.path.join(VO_DIR, f"concat_{key}.txt")
        with open(lst, "w", encoding="ascii") as f:
            for a in audios:
                f.write("file '%s'\n" % a.replace("\\", "/"))
        vo = os.path.join(VO_DIR, f"{key}_vo.wav")
        subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", lst, vo],
                       capture_output=True, text=True)
        total = sum(s["duration"] for s in steps)
        plan[key] = {"workflow_id": spec["workflow_id"], "steps": steps, "vo": vo}
        print(f"{key}: {len(steps)} steps, total ~{total:.0f}s ({total/60:.1f} min)")
    with open(PLAN, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print("plan ->", PLAN)


if __name__ == "__main__":
    build()
