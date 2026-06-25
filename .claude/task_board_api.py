#!/usr/bin/env python3
"""
Artemis Task Board API — serves the task_board.html + REST API
================================================================
Tiny HTTP server that:
  - Serves task_board.html at /
  - Exposes /api/tasks/* for CRUD against the SQLite task queue
  - Port 19280 (configurable)

Run alongside the MCP server — both share the same SQLite DB.
"""
import sys
import os
import json
import sqlite3
import http.server
import urllib.parse
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(WORKSPACE, ".claude", "task_queue.db")
BOARD_HTML = os.path.join(WORKSPACE, ".claude", "task_board.html")
PORT = int(os.environ.get("ARTEMIS_TASK_PORT", "19280"))

# ── DB helpers ──
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def _read_current_character():
    soul = os.path.join(WORKSPACE, "SOUL.md")
    try:
        with open(soul, "r", encoding="utf-8") as f:
            first = f.readline().strip()
            if "Tool Mode" in first: return "tool"
            for name in ["Shiki Natsume","ATRI","Yono Sakura","Enola"]:
                if name in first:
                    return name.lower().replace(" ","_")
            return first.split(" — ")[-1].lower().split(" ")[0] if " — " in first else "unknown"
    except:
        return "natsume"


class TaskAPI(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silent

    def _send(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, path):
        try:
            with open(path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            return self._send_html(BOARD_HTML)

        elif path == "/api/tasks/list":
            db = get_db()
            try:
                rows = db.execute("SELECT * FROM tasks ORDER BY CASE status WHEN 'notstarted' THEN 0 WHEN 'ongoing' THEN 1 WHEN 'blocked' THEN 2 WHEN 'completed' THEN 3 END, sort_order ASC, created_at DESC").fetchall()
                tasks = [{k: row[k] for k in row.keys()} for row in rows]
                pending = sum(1 for t in tasks if t["status"] == "notstarted" and t["assignee"] == "agent")
                ongoing = sum(1 for t in tasks if t["status"] == "ongoing")
                completed = sum(1 for t in tasks if t["status"] == "completed")
                self._send({"ok": True, "tasks": tasks, "pending": pending, "ongoing": ongoing, "completed": completed, "character": _read_current_character()})
            finally:
                db.close()

        elif path.startswith("/api/tasks/get/"):
            tid = path.split("/")[-1]
            db = get_db()
            try:
                row = db.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
                if not row:
                    self._send({"ok": False, "error": "Not found"}, 404)
                    return
                task = {k: row[k] for k in row.keys()}
                msgs = db.execute("SELECT * FROM messages WHERE task_id=? ORDER BY created_at ASC", (tid,)).fetchall()
                messages = [{k: m[k] for k in m.keys()} for m in msgs]
                self._send({"ok": True, "task": task, "messages": messages})
            finally:
                db.close()

        else:
            self._send({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Read body
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(body)
        except:
            data = {}

        if path == "/api/tasks/create":
            title = data.get("title", "").strip()
            body_text = data.get("body", "")
            assignee = data.get("assignee", "agent")
            if not title:
                self._send({"ok": False, "error": "Title required"}, 400)
                return

            import uuid
            tid = uuid.uuid4().hex[:8]
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            db = get_db()
            try:
                max_order = db.execute("SELECT COALESCE(MAX(sort_order),-1) FROM tasks WHERE assignee='agent'").fetchone()
                sort_order = max_order[0] + 1 if assignee == "agent" else 0
                db.execute(
                    "INSERT INTO tasks(id,title,body,status,assignee,created_by,sort_order,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                    (tid, title, body_text, "notstarted", assignee, "human", sort_order, now, now)
                )
                db.commit()
                row = db.execute("SELECT * FROM tasks WHERE id=?",(tid,)).fetchone()
                self._send({"ok": True, "task": {k: row[k] for k in row.keys()}})
            finally:
                db.close()

        elif path == "/api/tasks/update-status":
            tid = data.get("taskId")
            status = data.get("status")
            if not tid or not status:
                self._send({"ok": False, "error": "taskId + status required"}, 400)
                return
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db = get_db()
            try:
                existing = db.execute("SELECT status FROM tasks WHERE id=?",(tid,)).fetchone()
                if not existing:
                    self._send({"ok": False, "error": "Not found"}, 404)
                    return
                db.execute("UPDATE tasks SET status=?, updated_at=? WHERE id=?",(status,now,tid))
                db.execute("INSERT INTO messages(id,task_id,sender,text,created_at) VALUES(?,?,?,?,?)",
                    (str(uuid.uuid4())[:8], tid, "system", f"📌 {existing['status']} → {status}", now))
                db.commit()
                self._send({"ok": True})
            finally:
                db.close()

        elif path == "/api/tasks/reply":
            tid = data.get("taskId")
            sender = data.get("sender", "human")
            text = data.get("text", "")
            if not tid or not text:
                self._send({"ok": False, "error": "taskId + text required"}, 400)
                return
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            import uuid
            db = get_db()
            try:
                db.execute("INSERT INTO messages(id,task_id,sender,text,created_at) VALUES(?,?,?,?,?)",
                    (uuid.uuid4().hex[:8], tid, sender, text, now))
                db.commit()
                self._send({"ok": True})
            finally:
                db.close()

        else:
            self._send({"error": "Not found"}, 404)


def main():
    server = http.server.HTTPServer(("127.0.0.1", PORT), TaskAPI)
    print(f"[Artemis Task Board] http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
