import os
import subprocess

try:
    from imageio_ffmpeg import get_ffmpeg_exe
    FFMPEG = get_ffmpeg_exe()
except Exception:
    FFMPEG = "ffmpeg"

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "hub", "assets", "n8n")

for key in ["leadqual_demo", "news_demo", "support_demo"]:
    raw = os.path.join(A, f"{key}_raw.webm")
    vo = os.path.join(HERE, "docs", "vo_n8n", f"{key}_vo.wav")
    out = os.path.join(A, f"{key}.mp4")
    if not (os.path.exists(raw) and os.path.exists(vo)):
        print("SKIP", key, "raw:", os.path.exists(raw), "vo:", os.path.exists(vo))
        continue
    cmd = [FFMPEG, "-y", "-i", raw, "-i", vo,
           "-c:v", "libx264", "-crf", "24", "-preset", "fast", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k", "-shortest", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(key, "->", os.path.basename(out), "rc:", r.returncode,
          "size:", round(os.path.getsize(out) / 1024) if os.path.exists(out) else 0, "KB")