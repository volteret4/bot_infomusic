import html

MAX_MSG = 4000


def esc(text) -> str:
    return html.escape(str(text)) if text else ""


def truncate(text: str, limit: int = 400) -> str:
    if not text:
        return ""
    return text[:limit] + "…" if len(text) > limit else text


def fmt_duration(seconds) -> str:
    if not seconds:
        return ""
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def split_message(text: str) -> list[str]:
    """Split a long HTML message into chunks under Telegram's 4096 char limit."""
    if len(text) <= MAX_MSG:
        return [text]
    chunks, current = [], []
    current_len = 0
    for line in text.split("\n"):
        if current_len + len(line) + 1 > MAX_MSG:
            chunks.append("\n".join(current))
            current, current_len = [], 0
        current.append(line)
        current_len += len(line) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks
