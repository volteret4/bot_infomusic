from telegram import Update
from telegram.ext import ContextTypes

from db import get_db
from utils import esc, split_message

_SQL_ARTISTS = """
    SELECT id, name, formed_year, tags
    FROM artists
    WHERE name LIKE ? OR tags LIKE ?
    ORDER BY name
    LIMIT 4
"""

_SQL_ALBUMS = """
    SELECT al.id, al.name, al.year, al.genre, a.name AS artist_name
    FROM albums al
    JOIN artists a ON al.artist_id = a.id
    WHERE al.name LIKE ?
    ORDER BY al.year DESC
    LIMIT 4
"""

_SQL_SONGS = """
    SELECT id, title, artist, album
    FROM songs
    WHERE title LIKE ? OR artist LIKE ?
    ORDER BY title
    LIMIT 6
"""


async def cmd_buscar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Uso: /buscar <texto>")
        return
    query = " ".join(context.args)
    pattern = f"%{query}%"

    with get_db() as conn:
        artists = conn.execute(_SQL_ARTISTS, (pattern, pattern)).fetchall()
        albums = conn.execute(_SQL_ALBUMS, (pattern,)).fetchall()
        songs = conn.execute(_SQL_SONGS, (pattern, pattern)).fetchall()

    if not any([artists, albums, songs]):
        await update.message.reply_text(f"Sin resultados para «{query}».")
        return

    lines = [f"<b>Resultados para «{esc(query)}»</b>"]

    if artists:
        lines.append("\n<b>Artistas</b>")
        for r in artists:
            year = f" ({r['formed_year']})" if r["formed_year"] else ""
            tags = f" — <i>{esc(r['tags'])}</i>" if r["tags"] else ""
            lines.append(f"• {esc(r['name'])}{year}{tags}")

    if albums:
        lines.append("\n<b>Álbumes</b>")
        for r in albums:
            year = f" ({str(r['year'])[:4]})" if r["year"] else ""
            lines.append(f"• {esc(r['name'])}{year} — {esc(r['artist_name'])}")

    if songs:
        lines.append("\n<b>Canciones</b>")
        for r in songs:
            album = f" [{esc(r['album'])}]" if r["album"] else ""
            lines.append(f"• {esc(r['title'])} — {esc(r['artist'] or '')}{album}")

    text = "\n".join(lines)
    for chunk in split_message(text):
        await update.message.reply_html(chunk)
