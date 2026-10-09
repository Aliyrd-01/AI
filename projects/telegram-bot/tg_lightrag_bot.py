import requests, time, json, os

TOKEN = "REDACTED"
LIGHTRAG_URL = "http://localhost:9621/query"
OFFSET_FILE = os.path.expanduser("~/.tg_bot_offset")

def get_offset():
    try:
        with open(OFFSET_FILE) as f:
            return int(f.read().strip())
    except:
        return 0

def save_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        f.write(str(offset))

def lightrag_query(text):
    try:
        r = requests.post(LIGHTRAG_URL, json={"query": text, "mode": "mix"}, timeout=120)
        if r.status_code == 200:
            return r.json().get("response", "Нет ответа")
        return f"Ошибка LightRAG: {r.status_code}"
    except Exception as e:
        return f"Ошибка: {e}"

offset = get_offset()
print(f"Бот запущен. Offset: {offset}")

while True:
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates",
            params={"offset": offset, "timeout": 30},
            timeout=35
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
                requests.post(
                    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                    json={"chat_id": chat_id, "text": answer, "parse_mode": "Markdown"}
                )
                print(f"  -> {answer[:50]}...")

            offset = update_id + 1
            save_offset(offset)

    except KeyboardInterrupt:
        print("\nСтоп")
        break
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)
