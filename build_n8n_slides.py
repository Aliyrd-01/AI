"""Собирает s8n-видео из кадров (docs/n8n_shots) и озвучки (docs/vo_n8n) по плану.

Каждый шаг: кадр показывается ровно столько, сколько длится его озвучка, с лёгким
наездом камеры (Ken Burns) для эффекта движения. Кадры снимались после полной отрисовки,
поэтому «загрузки страницы» в видео нет.

Запуск: python build_n8n_slides.py
Результат: hub/assets/n8n/<key>_demo.mp4
"""

import json
import os
import subprocess

try:
    from imageio_ffmpeg import get_ffmpeg_exe
    FFMPEG = get_ffmpeg_exe()
except Exception:
    FFMPEG = "ffmpeg"

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(HERE, "n8n_video_plan.json"), encoding="utf-8"))
SHOT = os.path.join(HERE, "docs", "n8n_shots")
SEG = os.path.join(HERE, "docs", "n8n_seg")
OUT = os.path.join(HERE, "hub", "assets", "n8n")
W, H, FPS = 1600, 900, 30
os.makedirs(SEG, exist_ok=True)


def build(key):
    spec = PLAN[key]
    segs = []
    for i, st in enumerate(spec["steps"]):
        img = os.path.join(SHOT, f"{key}_{i:02d}.png")
        audio = st["audio"]
        if not os.path.isabs(audio):
            audio = os.path.join(HERE, audio)
        dur = st["duration"]
        seg = os.path.join(SEG, f"{key}_{i:02d}.mp4")
        frames = int(dur * FPS)
        if not (os.path.exists(img) and os.path.exists(audio)):
            print("  skip", i, "missing", img)
            continue
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H},"
              f"zoompan=z='min(zoom+0.0006,1.12)':d={frames}:x='iw/2-(iw/zoom/2)':"
              f"y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS}")
        cmd = [FFMPEG, "-y", "-loop", "1", "-i", img, "-i", audio,
               "-vf", vf, "-t", f"{dur}", "-r", str(FPS),
               "-c:v", "libx264", "-crf", "23", "-preset", "fast", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "1",
               "-shortest", seg]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print("  SEG FAIL", i, r.stderr[-300:])
            continue
        segs.append(seg)
    lst = os.path.join(SEG, f"list_{key}.txt")
    with open(lst, "w", encoding="ascii") as f:
        for s in segs:
            f.write("file '%s'\n" % s.replace("\\", "/"))
    final = os.path.join(OUT, f"{key}.mp4")
    r = subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", lst,
                        "-c", "copy", final], capture_output=True, text=True)
    if r.returncode != 0:  # re-encode fallback
        subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", lst,
                        "-c:v", "libx264", "-crf", "23", "-preset", "fast", "-c:a", "aac",
                        "-b:a", "128k", final], capture_output=True, text=True)
    if os.path.exists(final):
        print(f"{key} -> {os.path.basename(final)}  {round(os.path.getsize(final)/1024)} KB")
    else:
        print(f"{key} FAILED", r.stderr[-300:])


if __name__ == "__main__":
    for k in ["leadqual_demo", "news_demo", "support_demo"]:
        print("==", k)
        build(k)