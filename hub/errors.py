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
                "интерфейса и видны только в серверных логах."),
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


def friendly_error(exc: Exception | str | None, lang: str = "ru") -> str:
    """Map any exception or error string to a polite, user-facing message with zero technical leakage."""
    msg = _MSG_RU if lang == _RU else _MSG_EN
    if exc is None:
        return msg["generic"]

    cls = type(exc).__name__ if isinstance(exc, Exception) else ""
    low = f"{cls} {str(exc)}".lower()

    # 1. Rate limit, quota exhaustion, insufficient funds, 429, code 1300
    if any(k in low for k in (
        "ratelimit", "rate limit", "rate_limited", "429", "1300",
        "quota", "insufficient_quota", "credit", "balance", "billing",
        "all models failed", "all models failed for stream", "overloaded", "capacity"
    )):
        return msg["ratelimit"]

    # 2. Authentication, unauthorized, 401
    if any(k in low for k in ("authentication", "invalid api key", "unauthorized", "401", "permission_denied")):
        return msg["auth"]

    # 3. Vector DB / Qdrant cluster pause / database unreachable
    if any(k in low for k in ("qdrant", "cluster", "35.246", "qdrant.io", "handshake", "_ssl", "responsehandlingexception")):
        return msg["db"]

    # 4. Timeout
    if "timeout" in low or "timed out" in low:
        return msg["timeout"]

    # 5. Connection refused / network failure
    if any(k in low for k in ("connectionerror", "connection refused", "connect", "unreachable", "name resolution", "econnrefused")):
        return msg["conn"]

    # 6. Fallback generic
    return msg["generic"]


def scrub_paths(text: str) -> str:
    """Completely wipe local filesystem paths, machine usernames, and stack traces from any string."""
    s = str(text or "")
    # Windows absolute paths (D:\..., C:\..., D:/...)
    s = re.sub(r"[A-Za-z]:[/\\][^\s'\"<>\)]+", "[path]", s)
    # Unix absolute paths (/home/<user>, /Users/<user>, /app/...)
    s = re.sub(r"/(?:home|app|Users|usr|var|tmp|opt|root|workspace)/[^\s'\"<>\)]+", "[path]", s)
    # Python traceback lines (File "...", line 123)
    s = re.sub(r'File\s+["\'][^"\']+["\'],\s+line\s+\d+', 'File "[source]", line 0', s)
    # Machine usernames
    s = re.sub(r"\b(?:user|alex|user)\b", "[user]", s, flags=re.IGNORECASE)
    # IP addresses
    s = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?\b", "[host]", s)
    return s
