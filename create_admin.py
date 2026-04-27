#!/usr/bin/env python3
"""运行一次，创建第一个管理员账号"""
import getpass
import db
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone

db.init_db()

username = input("管理员用户名: ").strip()
password = getpass.getpass("管理员密码: ")

with db._conn() as con:
    existing = con.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
    if existing:
        print(f"错误：用户名 '{username}' 已存在")
        exit(1)
    con.execute(
        "INSERT INTO users (username, password_hash, is_admin, created_at) VALUES (?, ?, 1, ?)",
        (username, generate_password_hash(password), datetime.now(timezone.utc).isoformat())
    )
    print(f"管理员账号 '{username}' 创建成功，现在可以登录了")
