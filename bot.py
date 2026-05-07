import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from sopsdotenv import load_sops_env
from handlers import artistas, albumes, canciones, stats, buscar

load_sops_env()

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)


_HELP = """<b>Bot InfoMusic</b> 🎵

/artista &lt;nombre&gt; — info del artista
/album &lt;nombre&gt; — info del álbum
/cancion &lt;título&gt; — busca canciones
/letra &lt;título o letra&gt; — muestra la letra
/top [n] — canciones más escuchadas
/nuevos [n] — últimas adiciones
/stats — estadísticas generales
/buscar &lt;texto&gt; — búsqueda global"""


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(_HELP)


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("artista", artistas.cmd_artista))
    app.add_handler(CommandHandler("album", albumes.cmd_album))
    app.add_handler(CommandHandler("cancion", canciones.cmd_cancion))
    app.add_handler(CommandHandler("letra", canciones.cmd_letra))
    app.add_handler(CommandHandler("top", stats.cmd_top))
    app.add_handler(CommandHandler("nuevos", stats.cmd_nuevos))
    app.add_handler(CommandHandler("stats", stats.cmd_stats))
    app.add_handler(CommandHandler("buscar", buscar.cmd_buscar))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
