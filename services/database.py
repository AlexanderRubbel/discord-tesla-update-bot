import json
import os

import aiosqlite

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "bot.db")


async def _get_db() -> aiosqlite.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db() -> None:
    db = await _get_db()
    try:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS versions (
                version_id   TEXT PRIMARY KEY,
                release_date TEXT,
                release_notes TEXT,
                fleet_pct    REAL,
                source_url   TEXT,
                embed_msg_id INTEGER,
                poll_msg_id  INTEGER,
                channel_id   INTEGER,
                created_at   TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        await db.commit()
    finally:
        await db.close()


async def is_version_known(version_id: str) -> bool:
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT 1 FROM versions WHERE version_id = ?", (version_id,)
        )
        return await cursor.fetchone() is not None
    finally:
        await db.close()


async def add_version(
    version_id: str,
    release_date: str,
    features: list[dict],
    fleet_pct: float | None,
    source_url: str,
    embed_msg_id: int,
    poll_msg_id: int,
    channel_id: int,
) -> None:
    db = await _get_db()
    try:
        await db.execute(
            """INSERT OR IGNORE INTO versions
               (version_id, release_date, release_notes, fleet_pct,
                source_url, embed_msg_id, poll_msg_id, channel_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                version_id,
                release_date,
                json.dumps(features),
                fleet_pct,
                source_url,
                embed_msg_id,
                poll_msg_id,
                channel_id,
            ),
        )
        await db.commit()
    finally:
        await db.close()


async def get_version(version_id: str) -> dict | None:
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM versions WHERE version_id = ?", (version_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        result = dict(row)
        result["release_notes"] = json.loads(result["release_notes"] or "[]")
        return result
    finally:
        await db.close()


async def get_latest_version() -> dict | None:
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM versions ORDER BY created_at DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        result = dict(row)
        result["release_notes"] = json.loads(result["release_notes"] or "[]")
        return result
    finally:
        await db.close()


async def get_config(key: str) -> str | None:
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT value FROM config WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        return row["value"] if row else None
    finally:
        await db.close()


async def set_config(key: str, value: str) -> None:
    db = await _get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, value),
        )
        await db.commit()
    finally:
        await db.close()
