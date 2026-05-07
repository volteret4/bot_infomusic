from telegram import Update
from telegram.ext import ContextTypes

from db import get_db
from utils import esc, fmt_duration

_SQL_CANCION = """
    SELECT id, title, artist, album, date, genre,
           duration, bitrate, bit_depth, sample_rate
    FROM songs
    WHERE title LIKE ?
    ORDER BY title
    LIMIT 8
"""

_SQL_LYRICS_BY_SONG = """
    SELECT l.lyrics
    FROM songs s
    JOIN lyrics l ON l.track_id = s.id
    WHERE s.title LIKE ?
    LIMIT 1
"""

_SQL_LYRICS_FTS = """
    SELECT l.lyrics
    FROM lyrics_fts
    JOIN lyrics l ON lyrics_fts.rowid = l.id
    WHERE lyrics_fts MATCH ?
    LIMIT 1
"""


def _format_song(row) -> str:
    lines = [f"<b>{esc(row['title'])}</b>"]
    if row["artist"]:
        lines.append(f"<i>{esc(row['artist'])}</i>")
    if row["album"]:
        year = f" ({str(row['date'])[:4]})" if row["date"] else ""
        lines.append(f"Álbum: {esc(row['album'])}{year}")
    meta = []
    if row["duration"]:
        meta.append(fmt_duration(row["duration"]))
    if row["genre"]:
        meta.append(esc(row["genre"]))
    if row["bitrate"]:
        depth = f"/{row['bit_depth']}bit" if row["bit_depth"] else ""
        rate = f"/{row['sample_rate']}Hz" if row["sample_rate"] else ""
        meta.append(f"{row['bitrate']}kbps{depth}{rate}")
    if meta:
        lines.append(" · ".join(meta))
    return "\n".join(lines)


async def cmd_cancion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Uso: /cancion <título>")
        return
    query = " ".join(context.args)
    with get_db() as conn:
        rows = conn.execute(_SQL_CANCION, (f"%{query}%",)).fetchall()
    if not rows:
        await update.message.reply_text(f"No se encontró ninguna canción para «{query}».")
        return
    if len(rows) == 1:
        await update.message.reply_html(_format_song(rows[0]))
        return
    lines = [f"<b>{len(rows)} canciones para «{esc(query)}»:</b>"]
    for r in rows:
        dur = f" [{fmt_duration(r['duration'])}]" if r["duration"] else ""
        lines.append(f"• {esc(r['title'])}{dur} — {esc(r['artist'] or '')}")
    await update.message.reply_html("\n".join(lines))


async def cmd_letra(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Uso: /letra <título o palabras de la letra>")
        return
    query = " ".join(context.args)

    with get_db() as conn:
        # Try 1: song title → lyrics via FK
        row = conn.execute(_SQL_LYRICS_BY_SONG, (f"%{query}%",)).fetchone()
        if row:
            header = f"<b>{esc(query)}</b>\n\n"
            await _send_lyrics(update, header, row["lyrics"])
            return

        # Try 2: full-text search in lyrics content
        fts_query = " ".join(f'"{w}"' for w in query.split())
        row = conn.execute(_SQL_LYRICS_FTS, (fts_query,)).fetchone()
        if row:
            await _send_lyrics(update, "", row["lyrics"])
            return

    await update.message.reply_text(f"No se encontró letra para «{query}».")


async def _send_lyrics(update, header: str, lyrics: str) -> None:
    lyrics = lyrics or ""
    chunk_size = 3900 - len(header)
    first, rest = lyrics[:chunk_size], lyrics[chunk_size:]
    await update.message.reply_html(header + esc(first) + ("…" if rest else ""))
    while rest:
        part, rest = rest[:3900], rest[3900:]
        await update.message.reply_html(esc(part) + ("…" if rest else ""))
