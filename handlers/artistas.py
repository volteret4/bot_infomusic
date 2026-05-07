from telegram import Update
from telegram.ext import ContextTypes

from db import get_db
from utils import esc, truncate

_LINKS = [
    ("spotify_url", "Spotify"),
    ("youtube_url", "YouTube"),
    ("wikipedia_url", "Wikipedia"),
    ("musicbrainz_url", "MusicBrainz"),
    ("discogs_url", "Discogs"),
    ("rateyourmusic_url", "RYM"),
    ("lastfm_url", "Last.fm"),
    ("bandcamp_url", "Bandcamp"),
]


def _format_artist(row) -> str:
    lines = [f"<b>{esc(row['name'])}</b>"]
    meta = []
    if row["origin"] or row["origen"]:
        meta.append(f"Origen: {esc(row['origin'] or row['origen'])}")
    if row["formed_year"]:
        meta.append(f"Año: {row['formed_year']}")
    if row["total_albums"]:
        meta.append(f"Álbumes: {row['total_albums']}")
    if meta:
        lines.append(" · ".join(meta))
    if row["tags"]:
        lines.append(f"<i>{esc(row['tags'])}</i>")
    if row["bio"]:
        lines.append("")
        lines.append(esc(truncate(row["bio"], 500)))
    links = [
        f'<a href="{esc(row[f])}">{lbl}</a>'
        for f, lbl in _LINKS
        if row[f]
    ]
    if links:
        lines.append("")
        lines.append(" · ".join(links))
    return "\n".join(lines)


async def cmd_artista(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Uso: /artista <nombre>")
        return
    query = " ".join(context.args)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM artists WHERE name LIKE ? ORDER BY name LIMIT 6",
            (f"%{query}%",),
        ).fetchall()
    if not rows:
        await update.message.reply_text(f"No se encontró ningún artista para «{query}».")
        return
    if len(rows) == 1:
        await update.message.reply_html(_format_artist(rows[0]))
        return
    # Multiple results: list them
    lines = [f"<b>{len(rows)} artistas encontrados para «{esc(query)}»:</b>"]
    for r in rows:
        extra = f" ({r['formed_year']})" if r["formed_year"] else ""
        lines.append(f"• {esc(r['name'])}{extra}")
    lines.append("\nUsa un nombre más específico para ver detalles.")
    await update.message.reply_html("\n".join(lines))
