import json
import os
import sys
import time
import requests
from dotenv import load_dotenv

# Load .env from current directory or project root
_HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_HERE, ".env"))
load_dotenv(os.path.join(_HERE, "..", "..", ".env"))

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
if not TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN is not set. Set TELEGRAM_BOT_TOKEN in .env before running the bot.")
    sys.exit(1)

LIGHTRAG_URL = os.getenv("LIGHTRAG_URL", "http://localhost:9621/query")
OFFSET_FILE = os.path.expanduser("~/.tg_bot_offset")


def get_offset():
    try:
        with open(OFFSET_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except Exception:
        return 0


def save_offset(offset):
    try:
        with open(OFFSET_FILE, "w", encoding="utf-8") as f:
            f.write(str(offset))
    except Exception as e:
        print(f"Warning: could not save offset: {e}")


def lightrag_query(text):
    try:
        r = requests.post(LIGHTRAG_URL, json={"query": text, "mode": "mix"}, timeout=120)
        if r.status_code == 200:
            return r.json().get("response", "Нет ответа")
        return f"Ошибка LightRAG: {r.status_code}"
    except Exception as e:
        return f"Ошибка: {e}"


def send_tg_message(chat_id, text):
    """Send text in chunks of up to 4000 chars, with markdown fallback."""
    chunk_size = 4000
    for i in range(0, max(1, len(text)), chunk_size):
        chunk = text[i:i + chunk_size]
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        # Try Markdown first
        r = requests.post(
            url,
            json={"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"},
            timeout=30,
        )
        if r.status_code != 200:
            # Fallback to plain text if Markdown parsing fails
            requests.post(
                url,
                json={"chat_id": chat_id, "text": chunk},
                timeout=30,
            )


def main():
    offset = get_offset()
    print(f"Бот запущен. Offset: {offset}")

    while True:
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35,
            )
            data = r.json()
            if not data.get("ok"):
                time.sleep(3)
                continue

            for update in data.get("result", []):
                update_id = update["update_id"]
                msg = update.get("message", {})
                text = msg.get("text", "")
                chat_id = msg.get("chat", {}).get("id")

                if text and chat_id:
                    print(f"[{chat_id}] {text}")
                    answer = lightrag_query(text)
                    send_tg_message(chat_id, answer)
                    print(f"  -> {answer[:50]}...")

                offset = update_id + 1
                save_offset(offset)

        except KeyboardInterrupt:
            print("\nСтоп")
            break
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
