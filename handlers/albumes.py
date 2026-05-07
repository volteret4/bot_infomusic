from telegram import Update
from telegram.ext import ContextTypes

from db import get_db
from utils import esc

_LINKS = [
    ("spotify_url", "Spotify"),
    ("youtube_url", "YouTube"),
    ("wikipedia_url", "Wikipedia"),
    ("musicbrainz_url", "MusicBrainz"),
    ("discogs_url", "Discogs"),
    ("rateyourmusic_url", "RYM"),
    ("bandcamp_url", "Bandcamp"),
]

_SQL = """
    SELECT al.*, a.name AS artist_name
    FROM albums al
    JOIN artists a ON al.artist_id = a.id
    WHERE al.name LIKE ?
    ORDER BY al.year DESC
    LIMIT 6
"""


def _format_album(row) -> str:
    lines = [
        f"<b>{esc(row['name'])}</b>",
        f"<i>{esc(row['artist_name'])}</i>",
    ]
    meta = []
    if row["year"]:
        meta.append(str(row["year"])[:4])
    if row["genre"]:
        meta.append(esc(row["genre"]))
    if row["label"]:
        meta.append(esc(row["label"]))
    if row["total_tracks"]:
        meta.append(f"{row['total_tracks']} pistas")
    if meta:
        lines.append(" · ".join(meta))
    if row["producers"]:
        lines.append(f"Producido por: {esc(row['producers'])}")
    links = [
        f'<a href="{esc(row[f])}">{lbl}</a>'
        for f, lbl in _LINKS
        if row[f]
    ]
    if links:
        lines.append(" · ".join(links))
    return "\n".join(lines)


async def cmd_album(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Uso: /album <nombre>")
        return
    query = " ".join(context.args)
    with get_db() as conn:
        rows = conn.execute(_SQL, (f"%{query}%",)).fetchall()
    if not rows:
        await update.message.reply_text(f"No se encontró ningún álbum para «{query}».")
        return
    if len(rows) == 1:
        await update.message.reply_html(_format_album(rows[0]))
        return
    lines = [f"<b>{len(rows)} álbumes encontrados para «{esc(query)}»:</b>"]
    for r in rows:
        year = f" ({str(r['year'])[:4]})" if r["year"] else ""
        lines.append(f"• {esc(r['name'])}{year} — {esc(r['artist_name'])}")
    lines.append("\nUsa un nombre más específico para ver detalles.")
    await update.message.reply_html("\n".join(lines))
