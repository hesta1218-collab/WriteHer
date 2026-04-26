import json
import os
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, jsonify
import db

app = Flask(__name__)

@app.template_filter("from_json")
def from_json_filter(s):
    try:
        return json.loads(s) if s else []
    except Exception:
        return []
db.init_db()


def now():
    return datetime.now(timezone.utc).isoformat()


# ── 资料库 ──────────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('library'))


@app.route('/library')
def library():
    folder = request.args.get('folder')
    search = request.args.get('q', '').strip()
    with db._conn() as con:
        folders = [r[0] for r in con.execute(
            "SELECT DISTINCT folder FROM sources WHERE folder IS NOT NULL ORDER BY folder"
        ).fetchall()]
        query = "SELECT id, title, folder, credibility, credibility_label, created_at FROM sources"
        params = []
        conditions = []
        if folder:
            conditions.append("folder = ?")
            params.append(folder)
        if search:
            conditions.append("title LIKE ?")
            params.append(f"%{search}%")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id DESC"
        sources = con.execute(query, params).fetchall()
    return render_template('library.html', sources=sources, folders=folders,
                           active_folder=folder, search=search)


@app.route('/library/import', methods=['POST'])
def import_source():
    f = request.files.get('file')
    folder = request.form.get('folder', '').strip() or None
    if not f:
        return jsonify({'error': 'no file'}), 400
    title = os.path.splitext(f.filename)[0]
    content = f.read().decode('utf-8')
    with db._conn() as con:
        con.execute(
            "INSERT INTO sources (title, folder, content, created_at) VALUES (?, ?, ?, ?)",
            (title, folder, content, now())
        )
    return redirect(url_for('library'))


@app.route('/library/credibility/<int:source_id>', methods=['POST'])
def update_credibility(source_id):
    data = request.get_json()
    with db._conn() as con:
        con.execute(
            "UPDATE sources SET credibility=?, credibility_label=? WHERE id=?",
            (data.get('credibility'), data.get('label'), source_id)
        )
    return jsonify({'ok': True})


@app.route('/library/delete/<int:source_id>', methods=['POST'])
def delete_source(source_id):
    with db._conn() as con:
        con.execute("DELETE FROM cards WHERE source_id=?", (source_id,))
        con.execute("DELETE FROM sources WHERE id=?", (source_id,))
    return redirect(url_for('library'))


@app.route('/library/share/<int:source_id>', methods=['POST'])
def update_share_settings(source_id):
    data = request.get_json()
    with db._conn() as con:
        con.execute(
            "UPDATE sources SET is_public=?, allow_download=? WHERE id=?",
            (data.get('is_public', 0), data.get('allow_download', 0), source_id)
        )
    return jsonify({'ok': True})


# ── 广场 ──────────────────────────────────────────────

@app.route('/plaza')
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
def import_from_plaza(source_id):
    with db._conn() as con:
        source = con.execute("SELECT * FROM sources WHERE id=? AND is_public=1", (source_id,)).fetchone()
        if not source:
            return jsonify({'error': 'not found'}), 404
        # 复制资料到自己的库
        con.execute(
            "INSERT INTO sources (title, folder, content, contributor, origin_url, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (source['title'], None, source['content'], source['contributor'],
             source.get('origin_url'), now())
        )
        new_source_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        # 复制卡片
        cards = con.execute("SELECT * FROM cards WHERE source_id=?", (source_id,)).fetchall()
        for card in cards:
            con.execute(
                "INSERT INTO cards (source_id, content, tags, created_at) VALUES (?, ?, ?, ?)",
                (new_source_id, card['content'], card['tags'], now())
            )
    return jsonify({'ok': True, 'new_id': new_source_id})


@app.route('/plaza/download/<int:source_id>')
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
def reader(source_id):
    with db._conn() as con:
        source = con.execute("SELECT * FROM sources WHERE id=?", (source_id,)).fetchone()
        cards = con.execute(
            "SELECT * FROM cards WHERE source_id=? ORDER BY id DESC", (source_id,)
        ).fetchall()
        all_sources = con.execute(
            "SELECT id, title FROM sources ORDER BY id DESC"
        ).fetchall()
    return render_template('reader.html', source=source, cards=cards, all_sources=all_sources)


@app.route('/reader/<int:source_id>/card', methods=['POST'])
def add_card(source_id):
    data = request.get_json()
    tags = json.dumps(data.get('tags', []), ensure_ascii=False)
    with db._conn() as con:
        con.execute(
            "INSERT INTO cards (source_id, content, tags, created_at) VALUES (?, ?, ?, ?)",
            (source_id, data['content'], tags, now())
        )
    return jsonify({'ok': True})


# ── 侦探板 ──────────────────────────────────────────────

@app.route('/board')
def board():
    project = request.args.get('project', '默认项目')
    embed = request.args.get('embed') == 'true'
    with db._conn() as con:
        state = con.execute(
            "SELECT nodes, edges FROM board_state WHERE project_name=?", (project,)
        ).fetchone()
        cards = con.execute("SELECT id, content, tags FROM cards ORDER BY id DESC").fetchall()
    nodes = state['nodes'] if state else '[]'
    edges = state['edges'] if state else '[]'
    template = 'board_embed.html' if embed else 'board.html'
    return render_template(template, project=project, nodes=nodes, edges=edges, cards=cards)


@app.route('/board/save', methods=['POST'])
def save_board():
    data = request.get_json()
    project = data.get('project', '默认项目')
    with db._conn() as con:
        con.execute("""
            INSERT INTO board_state (project_name, nodes, edges, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(project_name) DO UPDATE SET nodes=excluded.nodes, edges=excluded.edges, updated_at=excluded.updated_at
        """, (project, json.dumps(data['nodes'], ensure_ascii=False),
              json.dumps(data['edges'], ensure_ascii=False), now()))
    return jsonify({'ok': True})


# ── 编辑器 ──────────────────────────────────────────────

@app.route('/editor')
def editor():
    project = request.args.get('project', '默认项目')
    with db._conn() as con:
        draft = con.execute(
            "SELECT content FROM drafts WHERE project_name=?", (project,)
        ).fetchone()
        sources = con.execute("SELECT id, title FROM sources ORDER BY id DESC").fetchall()
        cards = con.execute("SELECT id, content, tags FROM cards ORDER BY id DESC").fetchall()
    content = draft['content'] if draft else ''
    return render_template('editor.html', project=project, draft_content=content,
                           sources=sources, cards=cards)


@app.route('/editor/save', methods=['POST'])
def save_draft():
    data = request.get_json()
    project = data.get('project', '默认项目')
    with db._conn() as con:
        con.execute("""
            INSERT INTO drafts (project_name, content, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(project_name) DO UPDATE SET content=excluded.content, updated_at=excluded.updated_at
        """, (project, data.get('content', ''), now()))
    return jsonify({'ok': True})


# ── API ──────────────────────────────────────────────

@app.route('/api/source/<int:source_id>')
def get_source(source_id):
    with db._conn() as con:
        source = con.execute("SELECT content FROM sources WHERE id=?", (source_id,)).fetchone()
    if not source:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'content': source['content']})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
