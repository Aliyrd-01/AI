"""
Собирает демо-видео хаба с озвучкой (RU и EN) через офлайн Windows TTS (SAPI).

    python make_demo_video.py            # оба языка
    python make_demo_video.py --lang ru  # один

Требования:
  - скриншоты:  shots/<lang>_<name>.png   (node capture_shots.mjs <lang>)
  - ffmpeg:     imageio-ffmpeg (ставится вместе с moviepy)

Результат: docs/hub-demo-ru.mp4 и docs/hub-demo-en.mp4
"""

import argparse
import json
import os
import re
import subprocess
import sys

try:
    from imageio_ffmpeg import get_ffmpeg_exe
    FFMPEG_EXE = get_ffmpeg_exe()
except Exception:  # noqa: BLE001
    FFMPEG_EXE = "ffmpeg"

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "shots")
OUT = os.path.join(HERE, "docs")
VO = os.path.join(OUT, "vo")
TMP = os.path.join(VO, "tmp")

VOICES = {"ru": "Microsoft Irina Desktop", "en": "Microsoft Zira Desktop"}

# Piper (офлайн, человечные мужские голоса)
PIPER_DIR = os.path.join(HERE, "tools", "voices")
PIPER_MODELS = {
    "ru": os.path.join(PIPER_DIR, "ru_RU-dmitri-medium.onnx"),
    "en": os.path.join(PIPER_DIR, "en_US-ryan-high.onnx"),
}

SCRIPTS = {
    "ru": {
        "pages": [
            ("home", "Это моё AI-портфолио. Здесь собраны основные работы: RAG-система, "
                     "автоматизации на n8n и агентные решения. В сайдбаре — разделы: "
                     "RAG, n8n, агенты, метрики и проекты."),
            ("rag", "Интерактивное RAG демо: гибридный поиск по тремстам десяти тысячам документов, "
                    "реранкинг и ответы с цитатами. Задаем вопрос и получаем ответ со ссылками "
                    "на источники и метриками."),
            ("n8n", "Три n8n воркфлоу: автоматическая публикация новостей, квалификация лидов с "
                    "A B тестом промптов и интеллектуальная поддержка."),
            ("agents", "Многоагентная система: триаж агент маршрутизирует задачи под-агентам, "
                       "и у каждой фазы своя модель. Плюс MCP сервер к Postgres с десятью инструментами."),
            ("benchmarks", "Все измерено: метрики поиска, качество генерации по faithfulness и relevancy, "
                           "и сравнение моделей на TruthfulQA, GSM8K и BBH."),
            ("projects", "Остальные проекты: GraphRAG и LightRAG, MCP серверы, "
                         "бенчмарк галлюцинаций и телеграм бот. Код в репозитории."),
            ("unified_agent", "И главное: Unified Agent. Один агент сам решает: искать в базе знаний "
                              "или запросить CRM, и отвечает с пометками источников."),
        ],
    },
    "en": {
        "pages": [
            ("home", "This is my AI portfolio. It brings together the main work: a RAG system, "
                     "n8n automations and agent solutions. In the sidebar you will find "
                     "RAG, n8n, Agents, Benchmarks and Projects."),
            ("rag", "This is an interactive RAG demo: hybrid search over three hundred ten thousand documents, "
                    "reranking, and answers with citations. Ask a question and get an answer with "
                    "source links and metrics."),
            ("n8n", "Three n8n workflows: automated news publishing, lead qualification with "
                    "A B prompt testing, and AI-powered support."),
            ("agents", "A multi-agent system: a triage agent routes tasks to sub-agents, and every phase "
                       "has its own model. Plus an MCP server for Postgres with ten tools."),
            ("benchmarks", "Everything is measured: retrieval metrics, generation quality by faithfulness "
                           "and relevancy, and model comparison on TruthfulQA, GSM8K and BBH."),
            ("projects", "More projects: GraphRAG and LightRAG, MCP servers, a hallucination benchmark "
                         "and a Telegram bot. The code is in the repository."),
            ("unified_agent", "And the main tool: the Unified Agent. One agent decides on its own whether "
                              "to search the knowledge base or query the CRM, and answers with source tags."),
        ],
    },
}


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout or "", p.stderr or ""


def ffprobe_duration(path: str) -> float:
    rc, _out, err = run([FFMPEG_EXE, "-i", path])
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", err)
    if not m:
        return 5.0
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def sapi_tts(text: str, lang: str, out_wav: str):
    """(запасной вариант) Офлайн озвучка через Windows SAPI."""
    txt_file = os.path.join(TMP, "text.txt")
    with open(txt_file, "w", encoding="utf-8-sig") as f:
        f.write(text)
    ps_file = os.path.join(TMP, "tts.ps1")
    ps = (
        "Add-Type -AssemblyName System.Speech\n"
        "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
        f"$synth.SelectVoice('{VOICES[lang]}')\n"
        f"$synth.SetOutputToWaveFile('{out_wav}')\n"
        "$text = Get-Content -Raw -Encoding UTF8 '" + txt_file + "'\n"
        "$synth.Speak($text)\n"
        "$synth.Dispose()\n"
    )
    with open(ps_file, "w", encoding="ascii") as f:
        f.write(ps)
    rc, _o, err = run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_file])
    if rc != 0 or not os.path.exists(out_wav):
        raise RuntimeError(f"SAPI TTS failed: {err[:200]}")


def piper_tts(text: str, lang: str, out_wav: str):
    """Офлайн озвучка через Piper — спокойный мужской голос, с паузами для внятности."""
    txt_file = os.path.join(TMP, "text.txt")
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(text)
    model = PIPER_MODELS[lang]
    # length-scale 1.3 = заметно медленнее и разборчивее; sentence-silence — паузы между фразами
    rc, _o, err = run([sys.executable, "-m", "piper",
                       "-m", model, "-c", model + ".json",
                       "-f", out_wav, "-i", txt_file,
                       "--length-scale", "1.3", "--sentence-silence", "0.5"])
    if rc != 0 or not os.path.exists(out_wav):
        raise RuntimeError(f"Piper TTS failed: {err[:200]}")


def gen_audio(lang: str):
    os.makedirs(TMP, exist_ok=True)
    for name, text in SCRIPTS[lang]["pages"]:
        out_wav = os.path.join(VO, f"{lang}_{name}.wav")
        piper_tts(text, lang, out_wav)
        print(f"  vo {lang}/{name} (piper: {os.path.basename(PIPER_MODELS[lang])})")


def build(lang: str) -> str | None:
    segs = []
    for i, (name, _text) in enumerate(SCRIPTS[lang]["pages"], 1):
        img = os.path.join(SHOTS, f"{lang}_{name}.png")
        audio = os.path.join(VO, f"{lang}_{name}.wav")
        seg = os.path.join(VO, f"seg_{lang}_{i:02d}.mp4")
        dur = ffprobe_duration(audio) + 0.7
        rc, _o, err = run([FFMPEG_EXE, "-y",
                           "-loop", "1", "-framerate", "2", "-i", img,
                           "-i", audio,
                           "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "128k",
                           "-t", f"{dur:.2f}", "-shortest", seg])
        if rc != 0:
            print("  segment FAILED:", err[-300:])
            return None
        segs.append(seg)
        print(f"  seg {lang}/{name}: {dur:.1f}s")

    lst = os.path.join(VO, f"concat_{lang}.txt")
    with open(lst, "w", encoding="ascii") as f:
        for s in segs:
            f.write(f"file '{s}'\n")

    final = os.path.join(OUT, f"hub-demo-{lang}.mp4")
    rc, _o, err = run([FFMPEG_EXE, "-y", "-f", "concat", "-safe", "0", "-i", lst,
                       "-c", "copy", final])
    if rc != 0:
        print("concat FAILED:", err[-300:])
        return None
    print(f"  -> {final}")
    return final


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=["ru", "en", "both"], default="both")
    args = ap.parse_args()
    langs = ["ru", "en"] if args.lang == "both" else [args.lang]

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(VO, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)

    for lang in langs:
        print(f"=== {lang} ===")
        gen_audio(lang)
        build(lang)


if __name__ == "__main__":
    main()
