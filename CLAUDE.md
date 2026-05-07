# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project goal

A Telegram bot deployed in Docker that exposes a music database (defined in `schema_musica_local.sql`) for user queries.

## Development environment

Activate the shared virtual environment before running anything:

```bash
source ~/Scripts/python_venv/bin/activate
```

Key packages already installed in that venv:
- `python-telegram-bot` 22.6 — async Telegram bot framework
- `SQLAlchemy` 2.0 — ORM / query layer for the music DB
- `sopsdotenv` 0.1.0 (editable, at `~/Scripts/tools/sopsdotenv/`) — secrets loader

## Secrets management

Credentials live in `.encrypted.env`, encrypted with SOPS + age. Load them at startup:

```python
from sopsdotenv import load_sops_env
load_sops_env()  # walks up from CWD until it finds .encrypted.env
```

`load_sops_env` calls `sops --decrypt` under the hood and injects variables into `os.environ`. Accepts an explicit path and an `override=True` flag.

`.encrypted.env` must never be committed — `.gitignore` already blocks all `.env*` patterns.

## Pre-commit hooks

`gitleaks` runs on every staged commit to catch hardcoded secrets. It must be available on `PATH` as a system binary (the hook uses `language: system`). Install pre-commit hooks once after cloning:

```bash
pre-commit install
```

## Database schema

`schema_musica_local.sql` defines the music database. When building the ORM models or writing raw SQL, derive table/column names from that file.

## Bot structure

```
bot.py              — entry point: loads secrets, registers handlers, runs polling
db.py               — get_db() context manager (read-only sqlite3 connection)
utils.py            — esc(), fmt_duration(), truncate(), split_message()
sopsdotenv.py       — copy of ~/Scripts/tools/sopsdotenv/sopsdotenv.py
handlers/
  artistas.py       — /artista <nombre>
  albumes.py        — /album <nombre>
  canciones.py      — /cancion <título>, /letra <título o letra>
  stats.py          — /stats, /top [n], /nuevos [n]
  buscar.py         — /buscar <texto>  (LIKE search, FTS tables are unpopulated)
```

**Known DB quirk**: `lyrics.track_id` references old song IDs; only ~5 lyrics link to valid
`songs` rows. `/letra` first tries the FK path, then falls back to FTS5 (`lyrics_fts`) which
returns the lyric text without song metadata.

## Running locally

```bash
source ~/Scripts/python_venv/bin/activate
DB_PATH=/home/huan/gits/pollo/music-fuzzy/musica_local.sqlite python bot.py
```

Requires `.encrypted.env` in or above the working directory containing `TELEGRAM_BOT_TOKEN`.

## Docker

The container needs sops v3.9.4 (downloaded in Dockerfile) and three volume mounts:

| Host path (default) | Container path | Purpose |
|---|---|---|
| `musica_local.sqlite` | `/data/musica_local.sqlite` | SQLite DB (read-only) |
| `.encrypted.env` | `/app/.encrypted.env` | SOPS-encrypted credentials |
| `~/.config/sops/age/keys.txt` | `/root/.config/sops/age/keys.txt` | age decryption key |

Override defaults via env vars `DB_PATH`, `ENCRYPTED_ENV`, `AGE_KEY_FILE` before running
`docker compose up`.
