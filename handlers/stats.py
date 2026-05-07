from telegram import Update
from telegram.ext import ContextTypes

from db import get_db
from utils import esc

_SQL_TOP_SCROBBLES = """
    SELECT name, artist_name, COUNT(*) AS plays
    FROM scrobbles_paqueradejere
    GROUP BY name, artist_name
    ORDER BY plays DESC
    LIMIT ?
"""

_SQL_NUEVOS_ALBUMS = """
    SELECT al.name, a.name AS artist_name, al.year, al.added_timestamp
    FROM albums al
    JOIN artists a ON al.artist_id = a.id
    WHERE al.added_timestamp IS NOT NULL
    ORDER BY al.added_timestamp DESC
    LIMIT ?
"""

_SQL_STATS = """
    SELECT
        (SELECT COUNT(*) FROM artists) AS artistas,
        (SELECT COUNT(*) FROM albums)  AS albumes,
        (SELECT COUNT(*) FROM songs)   AS canciones,
        (SELECT COUNT(*) FROM lyrics)  AS letras,
        (SELECT COUNT(*) FROM scrobbles_paqueradejere) AS scrobbles
"""


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    with get_db() as conn:
        row = conn.execute(_SQL_STATS).fetchone()
    lines = [
        "<b>Estadísticas de la base de datos</b>",
        f"Artistas:   {row['artistas']:,}",
        f"Álbumes:    {row['albumes']:,}",
        f"Canciones:  {row['canciones']:,}",
        f"Letras:     {row['letras']:,}",
        f"Scrobbles:  {row['scrobbles']:,}",
    ]
    await update.message.reply_html("\n".join(lines))


async def cmd_top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    n = 10
    if context.args:
        try:
            n = max(1, min(int(context.args[0]), 30))
        except ValueError:
            pass
    with get_db() as conn:
        rows = conn.execute(_SQL_TOP_SCROBBLES, (n,)).fetchall()
    if not rows:
        await update.message.reply_text("No hay datos de scrobbles.")
        return
    lines = [f"<b>Top {n} canciones más escuchadas</b>"]
    for i, r in enumerate(rows, 1):
        lines.append(f"{i}. {esc(r['name'])} — {esc(r['artist_name'])} ({r['plays']})")
    await update.message.reply_html("\n".join(lines))


async def cmd_nuevos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    n = 10
    if context.args:
        try:
            n = max(1, min(int(context.args[0]), 30))
        except ValueError:
            pass
    with get_db() as conn:
        rows = conn.execute(_SQL_NUEVOS_ALBUMS, (n,)).fetchall()
    if not rows:
        await update.message.reply_text("No hay álbumes recientes.")
        return
    lines = [f"<b>Últimos {n} álbumes añadidos</b>"]
    for r in rows:
        year = f" ({str(r['year'])[:4]})" if r["year"] else ""
        date = str(r["added_timestamp"])[:10] if r["added_timestamp"] else ""
        lines.append(f"• {esc(r['name'])}{year} — {esc(r['artist_name'])}  <code>{date}</code>")
    await update.message.reply_html("\n".join(lines))
