"""Строит план n8n-видео: текст озвучки + селекторы нод, единый голос (Piper),
генерирует и склеивает аудио, измеряет длительности.

Запуск: python n8n_video_plan.py
Результат: n8n_video_plan.json + docs/vo_n8n/<key>_vo.wav
"""

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VO_DIR = os.path.join(HERE, "docs", "vo_n8n")
PIPER = os.path.join(HERE, "tools", "voices", "ru_RU-dmitri-medium.onnx")
PLAN = os.path.join(HERE, "n8n_video_plan.json")

try:
    from imageio_ffmpeg import get_ffmpeg_exe
    FFMPEG = get_ffmpeg_exe()
except Exception:  # noqa: BLE001
    FFMPEG = "ffmpeg"

PLANS = {
    "leadqual_demo": {
        "workflow_id": "R6TUfWY5jcGwZupm",
        "steps": [
            {"node": None, "text": "Этот воркфлоу автоматизирует квалификацию и скоринг входящих "
                                   "B2B-лидов. Рассмотрим архитектуру пайплайна."},
            {"node": "Webhook", "text": "Приём заявки: данные поступают через Webhook из формы захвата "
                                        "на сайте."},
            {"node": "Validate Lead", "text": "Валидация контактных данных. Некорректные обращения "
                                              "отсеиваются автоматически, команда получает системное уведомление."},
            {"node": "MCP Enrich HTTP", "text": "Обогащение через MCP: система обращается к корпоративной "
                                                "базе данных за профилем компании, индустрией и позицией "
                                                "контактного лица."},
            {"node": "OpenRouter API A", "text": "Интеллектуальный скоринг: языковая модель оценивает лид "
                                                 "по стобалльной шкале. Применяется A/B-архитектура с двумя "
                                                 "промптами — консервативным и расширенным."},
            {"node": "PostgreSQL (CRM)", "text": "Приоритетные лиды мгновенно уходят в Telegram, а все данные "
                                                 "синхронизируются с CRM в PostgreSQL."},
            {"node": None, "text": "Результат — мгновенная реакция на перспективные сделки и полная "
                                   "автоматизация рутинной квалификации."},
        ],
    },
    "news_demo": {
        "workflow_id": "YAyuG9GA2jUeICG2",
        "steps": [
            {"node": None, "text": "Автоматическая публикация материалов: пайплайн собирает, анализирует "
                                   "и публикует контент без участия человека."},
            {"node": "RSS Forklog", "text": "Сбор данных из RSS-источников по расписанию."},
            {"node": "Deduplication", "text": "Дедупликация записей и извлечение полного текста статьи."},
            {"node": "OpenRouter AI", "text": "AI-анализ: перевод, суммаризация и оценка релевантности "
                                              "материала."},
            {"node": "Telegram (Photo)", "text": "Финальное форматирование и публикация готового поста "
                                                 "в Telegram-канал."},
            {"node": None, "text": "Результат — постоянный поток отфильтрованных и проанализированных "
                                   "материалов."},
        ],
    },
    "support_demo": {
        "workflow_id": "jOJivAqG5l6rfQgk",
        "steps": [
            {"node": None, "text": "Сервис поддержки: автоматическая обработка обращений с маршрутизацией "
                                   "на оператора."},
            {"node": "Telegram Trigger", "text": "Приём сообщений через Telegram-триггер."},
            {"node": "Is Operator", "text": "Проверка роли пользователя и состояния диалога."},
            {"node": "Classify", "text": "LLM-классификация: определение типа обращения."},
            {"node": "Forward to Operator", "text": "Авто-ответ для типовых вопросов и эскалация сложных "
                                                    "тикетов оператору."},
            {"node": None, "text": "Результат — снижение нагрузки на первую линию поддержки."},
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
                    "-f", out_wav, "-i", txt, "--length-scale", "1.05"], check=True)


def build():
    os.makedirs(VO_DIR, exist_ok=True)
    plan = {}
    for key, spec in PLANS.items():
        steps, audios = [], []
        for i, st in enumerate(spec["steps"]):
            a = os.path.join(VO_DIR, f"{key}_{i:02d}.wav")
            tts(st["text"], a)
            steps.append({"node": st["node"], "text": st["text"],
                          "audio": a, "duration": round(duration(a) + 0.6, 2)})
            audios.append(a)
        # concat audio per workflow
        lst = os.path.join(VO_DIR, f"concat_{key}.txt")
        with open(lst, "w", encoding="ascii") as f:
            for a in audios:
                f.write("file '%s'\n" % a.replace("\\", "/"))
        vo = os.path.join(VO_DIR, f"{key}_vo.wav")
        subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", lst, vo],
                       capture_output=True, text=True)
        plan[key] = {"workflow_id": spec["workflow_id"], "steps": steps, "vo": vo}
        total = sum(s["duration"] for s in steps)
        print(f"{key}: {len(steps)} steps, ~{total:.1f}s, vo={os.path.basename(vo)}")
    with open(PLAN, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print("plan ->", PLAN)


if __name__ == "__main__":
    build()