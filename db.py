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
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                source_id INTEGER REFERENCES sources(id),
                content TEXT NOT NULL,
                tags TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS board_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL UNIQUE,
                nodes TEXT NOT NULL DEFAULT '[]',
                edges TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL UNIQUE,
                content TEXT,
                updated_at TEXT
            );
        """)
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
