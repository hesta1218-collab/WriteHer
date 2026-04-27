import sqlite3
import json
import os
from datetime import datetime, timezone

DB_PATH = os.environ.get("DB_PATH", "writehr.db")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS invite_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                used INTEGER DEFAULT 0,
                used_by INTEGER REFERENCES users(id),
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                title TEXT NOT NULL,
                folder TEXT,
                content TEXT NOT NULL,
                credibility TEXT,
                credibility_label TEXT,
                contributor TEXT DEFAULT 'Me',
                is_public INTEGER DEFAULT 0,
                allow_download INTEGER DEFAULT 0,
                origin_url TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                source_id INTEGER REFERENCES sources(id),
                content TEXT NOT NULL,
                tags TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS board_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                project_name TEXT NOT NULL,
                nodes TEXT NOT NULL DEFAULT '[]',
                edges TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT,
                UNIQUE(user_id, project_name)
            );
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                project_name TEXT NOT NULL,
                content TEXT,
                updated_at TEXT,
                UNIQUE(user_id, project_name)
            );
        """)
        # 迁移旧表字段
        for col, definition in [
            ("contributor", "TEXT DEFAULT 'Me'"),
            ("is_public", "INTEGER DEFAULT 0"),
            ("allow_download", "INTEGER DEFAULT 0"),
            ("origin_url", "TEXT"),
            ("user_id", "INTEGER"),
        ]:
            try:
                con.execute(f"ALTER TABLE sources ADD COLUMN {col} {definition}")
            except sqlite3.OperationalError:
                pass
        for col, definition in [("user_id", "INTEGER")]:
            try:
                con.execute(f"ALTER TABLE cards ADD COLUMN {col} {definition}")
            except sqlite3.OperationalError:
                pass
        for col, definition in [("user_id", "INTEGER")]:
            try:
                con.execute(f"ALTER TABLE board_state ADD COLUMN {col} {definition}")
            except sqlite3.OperationalError:
                pass
        for col, definition in [("user_id", "INTEGER")]:
            try:
                con.execute(f"ALTER TABLE drafts ADD COLUMN {col} {definition}")
            except sqlite3.OperationalError:
                pass
        # 迁移已有数据：给旧表添加新字段
        try:
            con.execute("ALTER TABLE sources ADD COLUMN contributor TEXT DEFAULT 'Me'")
        except sqlite3.OperationalError:
            pass
        try:
            con.execute("ALTER TABLE sources ADD COLUMN is_public INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            con.execute("ALTER TABLE sources ADD COLUMN allow_download INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            con.execute("ALTER TABLE sources ADD COLUMN origin_url TEXT")
        except sqlite3.OperationalError:
            pass
