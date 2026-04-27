# WriteHer MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Flask web app with three modules — resource library, detective board, and editor — for a single user to manage research materials and write.

**Architecture:** Flask serves HTML templates; SQLite stores all data; vanilla JS handles interactivity. Four pages: `/library`, `/reader/<id>`, `/board`, `/editor`. Existing `db.py` is extended with four new tables.

**Tech Stack:** Python 3, Flask, SQLite3, vanilla JS, marked.js (CDN, for Markdown rendering)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `app.py` | Create | Flask app, all routes |
| `db.py` | Modify | Add 4 new tables + CRUD functions |
| `requirements.txt` | Modify | Add `flask` |
| `static/style.css` | Create | Global dark theme, CSS variables |
| `static/js/library.js` | Create | File import, credibility tag UI |
| `static/js/reader.js` | Create | Text selection, tag popup, card creation |
| `static/js/board.js` | Create | Drag canvas, SVG lines, outline generation |
| `static/js/editor.js` | Create | Panel minimize/maximize/close, resize, autosave |
| `templates/base.html` | Create | Nav bar, font, CSS vars |
| `templates/library.html` | Create | Folder sidebar + source list |
| `templates/reader.html` | Create | Two-column: article + tag stream |
| `templates/board.html` | Create | Card sidebar + SVG canvas |
| `templates/editor.html` | Create | Four-panel grid layout |

---

## Task 1: Flask scaffold + DB schema

**Files:**
- Modify: `requirements.txt`
- Modify: `db.py`
- Create: `app.py`

- [ ] **Step 1: Add Flask to requirements**

Edit `requirements.txt` to:
```
requests
openai
flask
```

- [ ] **Step 2: Install**

```bash
pip install flask
```

- [ ] **Step 3: Extend db.py with new tables**

Add this function to the bottom of `db.py`:

```python
def init_web_db():
    with _conn() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                folder TEXT,
                content TEXT NOT NULL,
                credibility TEXT,
                credibility_label TEXT,
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
                content TEXT DEFAULT '',
                updated_at TEXT
            );
        """)
```

- [ ] **Step 4: Create app.py**

```python
from flask import Flask, redirect, url_for
import db

app = Flask(__name__)

db.init_db()
db.init_web_db()

from routes.library import library_bp
from routes.reader import reader_bp
from routes.board import board_bp
from routes.editor import editor_bp

app.register_blueprint(library_bp)
app.register_blueprint(reader_bp)
app.register_blueprint(board_bp)
app.register_blueprint(editor_bp)

@app.route('/')
def index():
    return redirect(url_for('library.index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

- [ ] **Step 5: Create routes directory**

```bash
mkdir -p /Users/jean/writehr/routes
touch /Users/jean/writehr/routes/__init__.py
```

- [ ] **Step 6: Verify app starts**

```bash
cd /Users/jean/writehr
python app.py
```

Expected: `Running on http://127.0.0.1:5000` (will 404 on routes until templates exist — that's fine)

- [ ] **Step 7: Commit**

```bash
cd /Users/jean/writehr
git init
git add app.py db.py requirements.txt routes/
git commit -m "feat: flask scaffold + db schema for web app"
```

---

## Task 2: Base template + global styles

**Files:**
- Create: `templates/base.html`
- Create: `static/style.css`

- [ ] **Step 1: Create static/style.css**

```css
:root {
    --bg-deep: #0a0a0a;
    --panel-bg: #141414;
    --text-warm: #ece5d8;
    --border-muted: #2a2a2a;
    --accent-gold: #8b7355;
    --accent-gold-dim: #4d4438;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body, html {
    height: 100%;
    background-color: var(--bg-deep);
    color: var(--text-warm);
    font-family: 'Noto Serif SC', serif;
    overflow: hidden;
}

a { color: var(--text-warm); text-decoration: none; }
a:hover { color: var(--accent-gold); }

.top-nav {
    height: 40px;
    border-bottom: 1px solid var(--border-muted);
    display: flex;
    align-items: center;
    padding: 0 20px;
    gap: 30px;
    font-size: 12px;
    letter-spacing: 2px;
}

.top-nav .brand { color: var(--accent-gold); opacity: 0.8; margin-right: auto; }
.top-nav a { opacity: 0.6; transition: opacity 0.2s; }
.top-nav a:hover, .top-nav a.active { opacity: 1; color: var(--accent-gold); }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: var(--border-muted); }
```

- [ ] **Step 2: Create templates/base.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}WriteHer · 述她{% endblock %}</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    {% block head %}{% endblock %}
</head>
<body>
<nav class="top-nav">
    <span class="brand">WRITEHR · 述她</span>
    <a href="/library" {% if active == 'library' %}class="active"{% endif %}>资料库</a>
    <a href="/board" {% if active == 'board' %}class="active"{% endif %}>侦探板</a>
    <a href="/editor" {% if active == 'editor' %}class="active"{% endif %}>编辑器</a>
</nav>
{% block content %}{% endblock %}
{% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 3: Commit**

```bash
git add templates/base.html static/style.css
git commit -m "feat: base template and global dark theme styles"
```

---

## Task 3: Resource library page

**Files:**
- Create: `routes/library.py`
- Create: `templates/library.html`
- Create: `static/js/library.js`

- [ ] **Step 1: Add CRUD functions to db.py**

Append to `db.py`:

```python
def get_all_sources(folder=None):
    with _conn() as con:
        if folder:
            rows = con.execute(
                "SELECT id, title, folder, credibility, credibility_label, created_at FROM sources WHERE folder = ? ORDER BY created_at DESC",
                (folder,)
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT id, title, folder, credibility, credibility_label, created_at FROM sources ORDER BY created_at DESC"
            ).fetchall()
    return [{"id": r[0], "title": r[1], "folder": r[2], "credibility": r[3], "credibility_label": r[4], "created_at": r[5]} for r in rows]

def get_folders():
    with _conn() as con:
        rows = con.execute("SELECT DISTINCT folder FROM sources WHERE folder IS NOT NULL AND folder != '' ORDER BY folder").fetchall()
    return [r[0] for r in rows]

def create_source(title, content, folder=None, credibility=None, credibility_label=None):
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO sources (title, folder, content, credibility, credibility_label, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (title, folder, content, credibility, credibility_label, now)
        )
        return cur.lastrowid

def update_source_credibility(source_id, credibility, credibility_label):
    with _conn() as con:
        con.execute(
            "UPDATE sources SET credibility = ?, credibility_label = ? WHERE id = ?",
            (credibility, credibility_label, source_id)
        )

def search_sources(query):
    with _conn() as con:
        rows = con.execute(
            "SELECT id, title, folder, credibility, credibility_label, created_at FROM sources WHERE title LIKE ? ORDER BY created_at DESC",
            (f"%{query}%",)
        ).fetchall()
    return [{"id": r[0], "title": r[1], "folder": r[2], "credibility": r[3], "credibility_label": r[4], "created_at": r[5]} for r in rows]
```

- [ ] **Step 2: Create routes/library.py**

```python
from flask import Blueprint, render_template, request, jsonify
import db

library_bp = Blueprint('library', __name__)

@library_bp.route('/library')
def index():
    folder = request.args.get('folder')
    query = request.args.get('q', '')
    if query:
        sources = db.search_sources(query)
    else:
        sources = db.get_all_sources(folder=folder)
    folders = db.get_folders()
    return render_template('library.html', sources=sources, folders=folders,
                           active_folder=folder, query=query, active='library')

@library_bp.route('/api/sources', methods=['POST'])
def upload_source():
    data = request.get_json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    folder = data.get('folder', '').strip() or None
    if not title or not content:
        return jsonify({'error': 'title and content required'}), 400
    source_id = db.create_source(title, content, folder=folder)
    return jsonify({'id': source_id, 'title': title})

@library_bp.route('/api/sources/<int:source_id>/credibility', methods=['PATCH'])
def update_credibility(source_id):
    data = request.get_json()
    credibility = data.get('credibility', '')
    credibility_label = data.get('credibility_label', '')
    db.update_source_credibility(source_id, credibility, credibility_label)
    return jsonify({'ok': True})
```

- [ ] **Step 3: Create templates/library.html**

```html
{% extends "base.html" %}
{% block title %}资料库 · WriteHer{% endblock %}
{% block head %}
<style>
.lib-container { display: flex; height: calc(100vh - 40px); }
.folder-sidebar { width: 220px; border-right: 1px solid var(--border-muted); padding: 20px 10px; background: #0d0d0d; overflow-y: auto; }
.sidebar-title { font-size: 11px; letter-spacing: 2px; color: var(--accent-gold); margin-bottom: 20px; padding-left: 10px; opacity: 0.8; }
.folder-item { padding: 9px 10px; font-size: 13px; cursor: pointer; border-radius: 3px; margin-bottom: 3px; display: flex; align-items: center; gap: 8px; opacity: 0.7; }
.folder-item:hover { background: var(--panel-bg); opacity: 1; }
.folder-item.active { color: var(--accent-gold); border-left: 2px solid var(--accent-gold); opacity: 1; }
.main-list { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.list-header { padding: 16px 32px; border-bottom: 1px solid var(--border-muted); display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.search-bar { background: transparent; border: 1px solid var(--border-muted); color: var(--text-warm); padding: 7px 14px; border-radius: 20px; width: 220px; font-family: 'Noto Serif SC'; font-size: 12px; }
.search-bar:focus { outline: none; border-color: var(--accent-gold-dim); }
.upload-btn { border: 1px dashed var(--accent-gold-dim); padding: 8px 20px; font-size: 12px; color: var(--accent-gold); cursor: pointer; background: transparent; font-family: 'Noto Serif SC'; }
.upload-btn:hover { border-color: var(--accent-gold); }
.source-table { padding: 10px 32px; overflow-y: auto; flex: 1; }
.source-row { display: grid; grid-template-columns: 32px 1fr 200px 110px; padding: 13px 0; border-bottom: 1px solid var(--border-muted); align-items: center; gap: 12px; }
.source-row:hover { background: rgba(139,115,85,0.04); }
.cred-symbol { font-size: 17px; cursor: pointer; }
.doc-name { font-size: 14px; cursor: pointer; }
.doc-name:hover { color: var(--accent-gold); }
.tag-pill { font-size: 11px; padding: 2px 8px; border-radius: 2px; background: transparent; border: 1px solid var(--border-muted); display: inline-flex; align-items: center; gap: 4px; cursor: pointer; }
.tag-pill.cred-full { border-color: var(--text-warm); color: var(--text-warm); }
.tag-pill.cred-half { border-color: var(--accent-gold); color: var(--accent-gold); }
.tag-pill.cred-none { border-color: var(--accent-gold-dim); color: var(--accent-gold-dim); }
.tag-pill.cred-personal { border-color: var(--accent-gold-dim); color: var(--accent-gold-dim); border-style: dashed; }
.date { font-size: 11px; color: var(--accent-gold-dim); }
.cred-popup { position: fixed; background: #1a1a1a; border: 1px solid var(--accent-gold); padding: 12px; z-index: 100; display: none; min-width: 220px; }
.cred-popup.visible { display: block; }
.cred-option { padding: 7px 10px; cursor: pointer; font-size: 13px; display: flex; align-items: center; gap: 8px; }
.cred-option:hover { background: rgba(139,115,85,0.1); }
.cred-label-input { width: 100%; background: transparent; border: none; border-bottom: 1px solid var(--border-muted); color: var(--text-warm); font-family: 'Noto Serif SC'; font-size: 12px; padding: 6px 0; margin-top: 8px; outline: none; }
</style>
{% endblock %}
{% block content %}
<div class="lib-container">
  <aside class="folder-sidebar">
    <div class="sidebar-title">ARCHIVE / 案卷夹</div>
    <div class="folder-item {% if not active_folder %}active{% endif %}" onclick="location.href='/library'">📂 全部资料</div>
    {% for f in folders %}
    <div class="folder-item {% if active_folder == f %}active{% endif %}" onclick="location.href='/library?folder={{ f }}'">📂 {{ f }}</div>
    {% endfor %}
  </aside>
  <main class="main-list">
    <div class="list-header">
      <form method="get" action="/library" style="display:flex;gap:8px;align-items:center;">
        {% if active_folder %}<input type="hidden" name="folder" value="{{ active_folder }}">{% endif %}
        <input type="text" class="search-bar" name="q" value="{{ query }}" placeholder="检索资料标题...">
      </form>
      <button class="upload-btn" onclick="document.getElementById('file-input').click()">+ 掷入新的碎片资料</button>
      <input type="file" id="file-input" accept=".md" style="display:none" multiple>
    </div>
    <div class="source-table">
      {% for s in sources %}
      <div class="source-row" data-id="{{ s.id }}">
        <div class="cred-symbol" title="点击修改可信度" onclick="openCredPopup(event, {{ s.id }}, '{{ s.credibility or '' }}', '{{ s.credibility_label or '' }}')">
          {{ s.credibility or '◻' }}
        </div>
        <div class="doc-name" onclick="location.href='/reader/{{ s.id }}'">{{ s.title }}</div>
        <div>
          {% set sym = s.credibility or '◻' %}
          {% set lbl = s.credibility_label or '未标注' %}
          {% if sym == '●' %}<span class="tag-pill cred-full">● {{ lbl }}</span>
          {% elif sym == '◐' %}<span class="tag-pill cred-half">◐ {{ lbl }}</span>
          {% elif sym == '○' %}<span class="tag-pill cred-none">○ {{ lbl }}</span>
          {% else %}<span class="tag-pill cred-personal">◻ {{ lbl }}</span>{% endif %}
        </div>
        <div class="date">{{ (s.created_at or '')[:10] }}</div>
      </div>
      {% else %}
      <div style="padding:40px;text-align:center;opacity:0.4;font-size:13px;">还没有资料，点击右上角导入 Markdown 文件</div>
      {% endfor %}
    </div>
  </main>
</div>

<div class="cred-popup" id="cred-popup">
  <div class="cred-option" onclick="selectCred('●')">● 一手 / 原始档案</div>
  <div class="cred-option" onclick="selectCred('◐')">◐ 二级 / 综合资料</div>
  <div class="cred-option" onclick="selectCred('○')">○ 民间 / 网络来源</div>
  <div class="cred-option" onclick="selectCred('◻')">◻ 个人 / 主观假设</div>
  <input type="text" class="cred-label-input" id="cred-label-input" placeholder="子标签描述（如：案卷档案）">
</div>
{% endblock %}
{% block scripts %}
<script src="{{ url_for('static', filename='js/library.js') }}"></script>
{% endblock %}
