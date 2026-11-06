"""Human-readable error messages for the UI: no tracebacks, no local paths, no raw API dumps."""

import re

_RU = "ru"

_MSG_RU = {
    "ratelimit": ("Лимит запросов или закончилась квота API — модель сейчас не может отвечать. "
                  "Подождите минуту или пополните баланс провайдера."),
    "auth": ("Ключ API не принят — проверьте настройки доступа (ключ задаётся через .env/Secrets, "
             "в интерфейсе он не показывается)."),
    "db": ("Векторная база (Qdrant) недоступна: сервис не отвечает. Обычная причина на бесплатном "
           "тарифе — кластер уходит в паузу после простоя, его нужно разбудить в консоли Qdrant."),
    "llm": ("Сервис ответов временно недоступен. Попробуйте ещё раз через минуту."),
    "conn": ("Нет связи с сервисом. Попробуйте ещё раз через минуту."),
    "timeout": ("Сервис не успел ответить вовремя. Попробуйте ещё раз."),
    "generic": ("Сервис временно недоступен — попробуйте ещё раз. Технические детали скрыты из "
                "интерфейса и видны только в логах."),
}
_MSG_EN = {
    "ratelimit": ("API rate limit hit or the quota is exhausted — the model cannot answer right now. "
                  "Wait a minute or top up the provider balance."),
    "auth": ("The API key was rejected — check the access settings (the key comes from .env/Secrets "
             "and is never shown in the UI)."),
    "db": ("The vector database (Qdrant) is unreachable: the service is not responding. On the free "
           "tier a paused cluster is the usual cause — wake it up in the Qdrant console."),
    "llm": ("The answer service is temporarily unavailable. Please try again in a minute."),
    "conn": ("Cannot reach the service. Please try again in a minute."),
    "timeout": ("The service did not respond in time. Please try again."),
    "generic": ("The service is temporarily unavailable — please retry. Technical details are hidden "
                "from the UI and only visible in the server logs."),
}

_PATH_RE = re.compile(r"[A-Za-z]:\\\\?[^\s'\"]+|/(?:home|app|Users|usr|var|tmp|opt)/[^\s'\"]+")


def friendly_error(exc: Exception | None, lang: str = "ru") -> str:
    msg = _MSG_RU if lang == _RU else _MSG_EN
    cls = type(exc).__name__ if exc is not None else ""
    low = f"{cls} {'' if exc is None else str(exc)}".lower()
    if "ratelimit" in low or "rate limit" in low or "429" in low:
        return msg["ratelimit"]
    if any(w in low for w in ("authentication", "invalid api key", "unauthorized", "401")):
        return msg["auth"]
    if "timeout" in low or "timed out" in low or "handshake" in low or "_ssl" in low:
        if any(w in low for w in ("qdrant", "35.246", "qdrant.io", "handshake", "_ssl")):
            return msg["db"]
        return msg["timeout"]
    if any(w in low for w in ("connectionerror", "connection refused", "connect")):
        return msg["conn"]
    if "qdrant" in low or "status code: 5" in low or "unavailable" in low:
        return msg["db"]
    return msg["generic"]


def scrub_paths(text: str) -> str:
    return _PATH_RE.sub("[path hidden]", str(text))
