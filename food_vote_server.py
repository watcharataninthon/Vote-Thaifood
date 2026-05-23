#!/usr/bin/env python3
"""
Food Vote API  —  Python 3 + SQLite (ไม่ต้องติดตั้งอะไรเพิ่ม)
"""
import json, sqlite3, re, os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'food_votes.db')
PORT    = 3001

# ── Database ─────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS menu_votes (
        menu_id    INTEGER PRIMARY KEY,
        vote_count INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT    NOT NULL DEFAULT (datetime('now'))
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_votes (
        session_id TEXT    NOT NULL,
        menu_id    INTEGER NOT NULL,
        voted_at   TEXT    NOT NULL DEFAULT (datetime('now')),
        PRIMARY KEY (session_id, menu_id)
    )''')
    for i in range(1, 21):
        c.execute('INSERT OR IGNORE INTO menu_votes (menu_id) VALUES (?)', (i,))
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ── HTTP Handler ──────────────────────────────────────────────────────────────
class FoodVoteHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f'  [{args[1]}] {self.command} {self.path}')

    def cors_headers(self):
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Headers', 'x-session-id, Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')

    def send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def session_id(self):
        return (self.headers.get('x-session-id') or '').strip() or None

    def do_OPTIONS(self):
        self.send_response(204)
        self.cors_headers()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == '/health':
            return self.send_json(200, {'status': 'ok'})

        if path == '/rankings':
            with get_db() as conn:
                rows = conn.execute(
                    'SELECT menu_id, vote_count FROM menu_votes '
                    'ORDER BY vote_count DESC, menu_id ASC'
                ).fetchall()
            return self.send_json(200, [dict(r) for r in rows])

        if path == '/votes/mine':
            sid = self.session_id()
            if not sid:
                return self.send_json(400, {'error': 'x-session-id header required'})
            with get_db() as conn:
                rows = conn.execute(
                    'SELECT menu_id FROM user_votes WHERE session_id=?', (sid,)
                ).fetchall()
            return self.send_json(200, [r['menu_id'] for r in rows])

        self.send_json(404, {'error': 'not found'})

    def do_POST(self):
        m = re.fullmatch(r'/vote/(\d+)', urlparse(self.path).path)
        if not m:
            return self.send_json(404, {'error': 'not found'})

        menu_id = int(m.group(1))
        sid     = self.session_id()

        if not sid:
            return self.send_json(400, {'error': 'x-session-id header required'})
        if not 1 <= menu_id <= 20:
            return self.send_json(400, {'error': 'invalid menu_id'})

        try:
            with get_db() as conn:
                dup = conn.execute(
                    'SELECT 1 FROM user_votes WHERE session_id=? AND menu_id=?',
                    (sid, menu_id)
                ).fetchone()
                if dup:
                    return self.send_json(409, {'error': 'already_voted'})
                conn.execute(
                    'INSERT INTO user_votes (session_id, menu_id) VALUES (?,?)',
                    (sid, menu_id)
                )
                conn.execute(
                    "UPDATE menu_votes SET vote_count=vote_count+1, updated_at=datetime('now') "
                    "WHERE menu_id=?", (menu_id,)
                )
                row = conn.execute(
                    'SELECT vote_count FROM menu_votes WHERE menu_id=?', (menu_id,)
                ).fetchone()
            self.send_json(200, {'menu_id': menu_id, 'vote_count': row['vote_count']})
        except Exception as e:
            self.send_json(500, {'error': str(e)})

    def do_DELETE(self):
        m = re.fullmatch(r'/vote/(\d+)', urlparse(self.path).path)
        if not m:
            return self.send_json(404, {'error': 'not found'})

        menu_id = int(m.group(1))
        sid     = self.session_id()

        if not sid:
            return self.send_json(400, {'error': 'x-session-id header required'})

        try:
            with get_db() as conn:
                result = conn.execute(
                    'DELETE FROM user_votes WHERE session_id=? AND menu_id=?',
                    (sid, menu_id)
                )
                if result.rowcount == 0:
                    return self.send_json(404, {'error': 'not_voted'})
                conn.execute(
                    "UPDATE menu_votes SET vote_count=MAX(vote_count-1,0), updated_at=datetime('now') "
                    "WHERE menu_id=?", (menu_id,)
                )
                row = conn.execute(
                    'SELECT vote_count FROM menu_votes WHERE menu_id=?', (menu_id,)
                ).fetchone()
            self.send_json(200, {'menu_id': menu_id, 'vote_count': row['vote_count']})
        except Exception as e:
            self.send_json(500, {'error': str(e)})

# ── Start ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    server = HTTPServer(('0.0.0.0', PORT), FoodVoteHandler)
    print(f'\n  🍜 Food Vote API  →  http://localhost:{PORT}')
    print(f'  GET  /health         — health check')
    print(f'  GET  /rankings       — leaderboard')
    print(f'  GET  /votes/mine     — คะแนนของฉัน (ต้องส่ง x-session-id header)')
    print(f'  POST /vote/:id       — โหวต')
    print(f'  DEL  /vote/:id       — ถอนโหวต')
    print(f'\n  กด Ctrl+C เพื่อหยุด\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n  หยุดแล้ว')
