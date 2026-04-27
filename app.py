import json
import os
import secrets
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

@app.template_filter("from_json")
def from_json_filter(s):
    try:
        return json.loads(s) if s else []
    except Exception:
        return []
db.init_db()


def now():
    return datetime.now(timezone.utc).isoformat()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    if 'user_id' not in session:
        return None
    with db._conn() as con:
        return con.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()


# ── 认证 ──────────────────────────────────────────────

@app.route('/init-admin', methods=['GET', 'POST'])
def init_admin():
    """首次部署时创建管理员账号"""
    with db._conn() as con:
        existing = con.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
        if existing['cnt'] > 0:
            return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        with db._conn() as con:
            con.execute(
                "INSERT INTO users (username, password_hash, is_admin, created_at) VALUES (?, ?, 1, ?)",
                (username, generate_password_hash(password), now())
            )
        return redirect(url_for('login'))

    return '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>初始化管理员 - WriteHer</title>
        <link rel="stylesheet" href="/static/style.css">
        <style>
        .init-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            background: var(--panel-bg);
            border: 1px solid var(--border-muted);
        }
        .init-title {
            font-size: 20px;
            margin-bottom: 16px;
            text-align: center;
            letter-spacing: 2px;
            color: var(--accent-gold);
        }
        .init-desc {
            font-size: 13px;
            opacity: 0.7;
            margin-bottom: 24px;
            text-align: center;
        }
        .init-form label {
            display: block;
            font-size: 13px;
            margin-bottom: 8px;
            color: var(--accent-gold);
        }
        .init-form input {
            width: 100%;
            background: var(--bg-deep);
            border: 1px solid var(--border-muted);
            color: var(--text-warm);
            padding: 12px;
            font-family: 'Noto Serif SC', serif;
            font-size: 14px;
            margin-bottom: 16px;
        }
        .init-form button {
            width: 100%;
            background: var(--accent-gold);
            border: none;
            color: #0a0a0a;
            padding: 12px;
            cursor: pointer;
            font-family: 'Noto Serif SC', serif;
            font-size: 14px;
        }
        </style>
    </head>
    <body>
        <div class="init-container">
            <div class="init-title">首次初始化</div>
            <div class="init-desc">创建第一个管理员账号</div>
            <form class="init-form" method="post">
                <label>用户名</label>
                <input type="text" name="username" required autofocus>
                <label>密码</label>
                <input type="password" name="password" required>
                <button type="submit">创建管理员</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        with db._conn() as con:
            user = con.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            return redirect(url_for('library'))
        return render_template('login.html', error='用户名或密码错误')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        invite_code = request.form.get('invite_code')

        with db._conn() as con:
            # 验证邀请码
            code = con.execute(
                "SELECT * FROM invite_codes WHERE code=? AND used=0", (invite_code,)
            ).fetchone()
            if not code:
                return render_template('register.html', error='邀请码无效或已使用')

            # 检查用户名是否已存在
            existing = con.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
            if existing:
                return render_template('register.html', error='用户名已存在')

            # 创建用户
            password_hash = generate_password_hash(password)
            con.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, password_hash, now())
            )
            user_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]

            # 标记邀请码已使用
            con.execute(
                "UPDATE invite_codes SET used=1, used_by=? WHERE id=?",
                (user_id, code['id'])
            )

            session['user_id'] = user_id
            session['username'] = username
            session['is_admin'] = 0
            return redirect(url_for('library'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ── 资料库 ──────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('library'))


@app.route('/library')
@login_required
def library():
    user_id = session['user_id']
    folder = request.args.get('folder')
    search = request.args.get('q', '').strip()
    with db._conn() as con:
        folders = [r[0] for r in con.execute(
            "SELECT DISTINCT folder FROM sources WHERE folder IS NOT NULL AND user_id=? ORDER BY folder",
            (user_id,)
        ).fetchall()]
        query = "SELECT id, title, folder, credibility, credibility_label, is_public, allow_download, created_at FROM sources WHERE user_id=?"
        params = [user_id]
        conditions = []
        if folder:
            conditions.append("folder = ?")
            params.append(folder)
        if search:
            conditions.append("title LIKE ?")
            params.append(f"%{search}%")
        if conditions:
            query += " AND " + " AND ".join(conditions)
        query += " ORDER BY id DESC"
        sources = con.execute(query, params).fetchall()
    return render_template('library.html', sources=sources, folders=folders,
                           active_folder=folder, search=search)


@app.route('/library/import', methods=['POST'])
@login_required
def import_source():
    user_id = session['user_id']
    f = request.files.get('file')
    folder = request.form.get('folder', '').strip() or None
    if not f:
        return jsonify({'error': 'no file'}), 400
    title = os.path.splitext(f.filename)[0]
    content = f.read().decode('utf-8')
    with db._conn() as con:
        con.execute(
            "INSERT INTO sources (user_id, title, folder, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, folder, content, now())
        )
    return redirect(url_for('library'))


@app.route('/library/credibility/<int:source_id>', methods=['POST'])
@login_required
def update_credibility(source_id):
    user_id = session['user_id']
    data = request.get_json()
    with db._conn() as con:
        con.execute(
            "UPDATE sources SET credibility=?, credibility_label=? WHERE id=? AND user_id=?",
            (data.get('credibility'), data.get('label'), source_id, user_id)
        )
    return jsonify({'ok': True})


@app.route('/library/delete/<int:source_id>', methods=['POST'])
@login_required
def delete_source(source_id):
    user_id = session['user_id']
    with db._conn() as con:
        con.execute("DELETE FROM cards WHERE source_id=? AND user_id=?", (source_id, user_id))
        con.execute("DELETE FROM sources WHERE id=? AND user_id=?", (source_id, user_id))
    return redirect(url_for('library'))


@app.route('/library/share/<int:source_id>', methods=['POST'])
@login_required
def update_share_settings(source_id):
    user_id = session['user_id']
    data = request.get_json()
    with db._conn() as con:
        con.execute(
            "UPDATE sources SET is_public=?, allow_download=? WHERE id=? AND user_id=?",
            (data.get('is_public', 0), data.get('allow_download', 0), source_id, user_id)
        )
    return jsonify({'ok': True})


# ── 广场 ──────────────────────────────────────────────

@app.route('/plaza')
@login_required
def plaza():
    search = request.args.get('q', '').strip()
    with db._conn() as con:
        query = """
            SELECT s.id, s.title, s.contributor, s.allow_download,
                   (SELECT COUNT(*) FROM cards WHERE source_id = s.id) as card_count
            FROM sources s
            WHERE s.is_public = 1
        """
        params = []
        if search:
            query += " AND s.title LIKE ?"
            params.append(f"%{search}%")
        query += " ORDER BY s.id DESC"
        sources = con.execute(query, params).fetchall()
    return render_template('plaza.html', sources=sources, search=search)


@app.route('/plaza/view/<int:source_id>')
@login_required
def plaza_view(source_id):
    with db._conn() as con:
        source = con.execute("SELECT * FROM sources WHERE id=? AND is_public=1", (source_id,)).fetchone()
        if not source:
            return "资料不存在或未公开", 404
        cards = con.execute(
            "SELECT * FROM cards WHERE source_id=? ORDER BY id DESC", (source_id,)
        ).fetchall()
    return render_template('plaza_view.html', source=source, cards=cards)


@app.route('/plaza/import/<int:source_id>', methods=['POST'])
@login_required
def import_from_plaza(source_id):
    user_id = session['user_id']
    with db._conn() as con:
        source = con.execute("SELECT * FROM sources WHERE id=? AND is_public=1", (source_id,)).fetchone()
        if not source:
            return jsonify({'error': 'not found'}), 404
        con.execute(
            "INSERT INTO sources (user_id, title, folder, content, contributor, origin_url, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, source['title'], None, source['content'], source['contributor'],
             source.get('origin_url'), now())
        )
        new_source_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        cards = con.execute("SELECT * FROM cards WHERE source_id=?", (source_id,)).fetchall()
        for card in cards:
            con.execute(
                "INSERT INTO cards (user_id, source_id, content, tags, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, new_source_id, card['content'], card['tags'], now())
            )
    return jsonify({'ok': True, 'new_id': new_source_id})


@app.route('/plaza/download/<int:source_id>')
@login_required
def download_from_plaza(source_id):
    with db._conn() as con:
        source = con.execute(
            "SELECT * FROM sources WHERE id=? AND is_public=1 AND allow_download=1",
            (source_id,)
        ).fetchone()
        if not source:
            return "资料不存在、未公开或不允许下载", 404
    from flask import make_response
    response = make_response(source['content'])
    response.headers['Content-Type'] = 'text/markdown; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="{source["title"]}.md"'
    return response


# ── 阅读器 ──────────────────────────────────────────────

@app.route('/reader/<int:source_id>')
@login_required
def reader(source_id):
    user_id = session['user_id']
    with db._conn() as con:
        source = con.execute("SELECT * FROM sources WHERE id=? AND user_id=?", (source_id, user_id)).fetchone()
        if not source:
            return "资料不存在", 404
        cards = con.execute(
            "SELECT * FROM cards WHERE source_id=? ORDER BY id DESC", (source_id,)
        ).fetchall()
        all_sources = con.execute(
            "SELECT id, title FROM sources WHERE user_id=? ORDER BY id DESC", (user_id,)
        ).fetchall()
    return render_template('reader.html', source=source, cards=cards, all_sources=all_sources)


@app.route('/reader/<int:source_id>/card', methods=['POST'])
@login_required
def add_card(source_id):
    user_id = session['user_id']
    data = request.get_json()
    tags = json.dumps(data.get('tags', []), ensure_ascii=False)
    with db._conn() as con:
        con.execute(
            "INSERT INTO cards (user_id, source_id, content, tags, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, source_id, data['content'], tags, now())
        )
    return jsonify({'ok': True})


# ── 侦探板 ──────────────────────────────────────────────

@app.route('/board')
@login_required
def board():
    user_id = session['user_id']
    project = request.args.get('project', '默认项目')
    embed = request.args.get('embed') == 'true'
    with db._conn() as con:
        state = con.execute(
            "SELECT nodes, edges FROM board_state WHERE project_name=? AND user_id=?", (project, user_id)
        ).fetchone()
        cards = con.execute("SELECT id, content, tags FROM cards WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()
    nodes = state['nodes'] if state else '[]'
    edges = state['edges'] if state else '[]'
    template = 'board_embed.html' if embed else 'board.html'
    return render_template(template, project=project, nodes=nodes, edges=edges, cards=cards)


@app.route('/board/save', methods=['POST'])
@login_required
def save_board():
    user_id = session['user_id']
    data = request.get_json()
    project = data.get('project', '默认项目')
    with db._conn() as con:
        con.execute("""
            INSERT INTO board_state (user_id, project_name, nodes, edges, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, project_name) DO UPDATE SET nodes=excluded.nodes, edges=excluded.edges, updated_at=excluded.updated_at
        """, (user_id, project, json.dumps(data['nodes'], ensure_ascii=False),
              json.dumps(data['edges'], ensure_ascii=False), now()))
    return jsonify({'ok': True})


# ── 编辑器 ──────────────────────────────────────────────

@app.route('/editor')
@login_required
def editor():
    user_id = session['user_id']
    project = request.args.get('project', '默认项目')
    with db._conn() as con:
        draft = con.execute(
            "SELECT content FROM drafts WHERE project_name=? AND user_id=?", (project, user_id)
        ).fetchone()
        sources = con.execute("SELECT id, title FROM sources WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()
        cards = con.execute("SELECT id, content, tags FROM cards WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()
    content = draft['content'] if draft else ''
    return render_template('editor.html', project=project, draft_content=content,
                           sources=sources, cards=cards)


@app.route('/editor/save', methods=['POST'])
@login_required
def save_draft():
    user_id = session['user_id']
    data = request.get_json()
    project = data.get('project', '默认项目')
    with db._conn() as con:
        con.execute("""
            INSERT INTO drafts (user_id, project_name, content, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, project_name) DO UPDATE SET content=excluded.content, updated_at=excluded.updated_at
        """, (user_id, project, data.get('content', ''), now()))
    return jsonify({'ok': True})


# ── API ──────────────────────────────────────────────

@app.route('/api/source/<int:source_id>')
@login_required
def get_source(source_id):
    user_id = session['user_id']
    with db._conn() as con:
        source = con.execute("SELECT content FROM sources WHERE id=? AND user_id=?", (source_id, user_id)).fetchone()
    if not source:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'content': source['content']})


# ── 管理员 ──────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return "无权限", 403
        return f(*args, **kwargs)
    return decorated_function


@app.route('/admin')
@login_required
@admin_required
def admin():
    with db._conn() as con:
        users = con.execute("SELECT id, username, is_admin, created_at FROM users ORDER BY id").fetchall()
        codes = con.execute("SELECT * FROM invite_codes ORDER BY id DESC").fetchall()
    return render_template('admin.html', users=users, codes=codes)


@app.route('/admin/invite', methods=['POST'])
@login_required
@admin_required
def create_invite():
    code = secrets.token_urlsafe(8)
    with db._conn() as con:
        con.execute("INSERT INTO invite_codes (code, created_at) VALUES (?, ?)", (code, now()))
    return jsonify({'ok': True, 'code': code})


@app.route('/admin/reset_password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    new_password = secrets.token_urlsafe(8)
    with db._conn() as con:
        con.execute(
            "UPDATE users SET password_hash=? WHERE id=?",
            (generate_password_hash(new_password), user_id)
        )
    return jsonify({'ok': True, 'new_password': new_password})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
