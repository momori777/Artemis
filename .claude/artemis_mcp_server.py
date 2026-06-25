#!/usr/bin/env python3
"""
Artemis MCP Server — Claude Code Integration + AgentRQ-style Task System
========================================================================
Exposes Artemis (AI Girlfriend) capabilities as MCP tools for Claude Code.
Includes a local task queue system (AgentRQ-compatible) for human-agent
task collaboration — no Docker, no Google OAuth, just SQLite.

Protocol: MCP over stdio (JSON-RPC 2.0)

MCP Tools (Claude Code executes these):
  ── Artemis Capabilities ──
  - tts_generate         : TTS voice synthesis
  - comfyui_generate     : AI image generation
  - live2d_emotion       : Live2D desktop pet control
  - switch_character     : Switch AI girlfriend character
  - list_characters      : List available characters
  - memory_search        : Search vector memory (mem0)
  - memory_add           : Add memory entry
  - get_status           : Get system status

  ── AgentRQ-compatible Task Queue ──
  - getNextTask          : Dequeue next 'notstarted' agent task
  - createTask           : Create a new task
  - updateTaskStatus     : Update task status (notstarted/ongoing/completed/blocked)
  - reply                : Post a message to task thread
  - getTaskMessages      : Read task message history
  - getWorkspace         : Get workspace info + stats
"""
import sys
import os
import json
import subprocess
import time
import uuid
import sqlite3
import threading
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(WORKSPACE)

# ================================================================
# Config
# ================================================================
def load_config():
    try:
        import yaml
        with open(os.path.join(WORKSPACE, "config.yaml"), "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except:
        return {}

CFG = load_config()

LLAMA_PORT = int(CFG.get("llama_port", 8080))
LIVE2D_BRIDGE = "http://localhost:19200"
MEDIA_AUDIO = CFG.get("media_qqbot_audio", os.path.join(WORKSPACE, "media", "qqbot", "audio"))
MEDIA_IMAGES = CFG.get("media_qqbot_images", os.path.join(WORKSPACE, "media", "qqbot", "images"))

TTs_PYTHON = CFG.get("sovits_python", "python")
COMFYUI_PYTHON = CFG.get("comfyui_python", "python")

os.makedirs(MEDIA_AUDIO, exist_ok=True)
os.makedirs(MEDIA_IMAGES, exist_ok=True)

# ================================================================
# Task Database (SQLite, AgentRQ-compatible schema)
# ================================================================
DB_DIR = os.path.join(WORKSPACE, ".claude")
DB_PATH = os.path.join(DB_DIR, "task_queue.db")

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

DB = get_db()
DB_LOCK = threading.Lock()

# Schema init
DB.executescript("""
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'notstarted'
        CHECK(status IN ('notstarted','ongoing','completed','blocked','rejected','cron')),
    assignee TEXT NOT NULL DEFAULT 'agent'
        CHECK(assignee IN ('human','agent')),
    created_by TEXT NOT NULL DEFAULT 'human'
        CHECK(created_by IN ('human','agent')),
    sort_order INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    sender TEXT NOT NULL CHECK(sender IN ('human','agent','system')),
    text TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status, assignee, sort_order);
CREATE INDEX IF NOT EXISTS idx_messages_task ON messages(task_id, created_at);
""")

# Seed a demo task if empty
def seed_demo():
    with DB_LOCK:
        count = DB.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if count == 0:
            tid = str(uuid.uuid4())[:8]
            DB.execute(
                "INSERT INTO tasks(id,title,body,status,assignee,sort_order) VALUES(?,?,?,?,?,?)",
                (tid, "🎨 Draw Natsume in a yukata at a summer festival",
                 "Use ComfyUI to generate an image of Shiki Natsume in a yukata (summer kimono) at a festival with fireworks and lanterns. I want a warm, romantic vibe.",
                 "notstarted", "agent", 0)
            )
            DB.execute(
                "INSERT INTO messages(id,task_id,sender,text) VALUES(?,?,?,?)",
                (str(uuid.uuid4())[:8], tid, "human", "Use ComfyUI to generate this. Default checkpoint, 1200x1500.")
            )
            DB.commit()

seed_demo()

# ================================================================
# MCP Schema
# ================================================================
NAME = "artemis-mcp"
VERSION = "2.0.0"
SERVER_INFO = {"name": NAME, "version": VERSION}

TOOLS = [
    # ── Artemis Capabilities ──
    {
        "name": "tts_generate",
        "description": "Generate TTS voice audio for an AI girlfriend character. Returns the file path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to synthesize (Japanese/Chinese/English)"},
                "character": {"type": "string", "enum": ["natsume","atri","sakura"], "default": "natsume"},
                "lang": {"type": "string", "enum": ["ja","zh","en"], "default": "ja"},
                "mood": {"type": "string", "enum": ["casual","tsundere","romantic","long","random"], "default": "casual"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "comfyui_generate",
        "description": "Generate AI character illustration using ComfyUI. Choose checkpoint and pass English prompts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "positive": {"type": "string"},
                "negative": {"type": "string", "default": "lowres, bad anatomy, bad hands, text, error, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, blurry"},
                "width": {"type": "integer", "default": 1200},
                "height": {"type": "integer", "default": 1500},
                "steps": {"type": "integer", "default": 30},
                "cfg": {"type": "number", "default": 6.0},
                "checkpoint": {"type": "string", "enum": ["WAI-Nsfw-Illustrious-17.safetensors","miaomiaoHarem_v20.safetensors"], "default": "WAI-Nsfw-Illustrious-17.safetensors"},
            },
            "required": ["positive"],
        },
    },
    {
        "name": "live2d_emotion",
        "description": "Control the Live2D desktop pet — trigger motion + optional speech bubble.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "motion": {"type": "string", "description": "Motion: Idle, Tap摸头, Tap外框, Tap摸手, Start, Leave300, Leave900, Leave1800"},
                "text": {"type": "string", "description": "Speech bubble text"},
            },
        },
    },
    {
        "name": "switch_character",
        "description": "Switch the active AI girlfriend character.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "character": {"type": "string", "description": "natsume, atri, sakura, enola"},
            },
            "required": ["character"],
        },
    },
    {
        "name": "list_characters",
        "description": "List all available AI girlfriend characters.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "memory_search",
        "description": "Search vector memory for past conversations and facts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "character": {"type": "string", "default": "natsume"},
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "memory_add",
        "description": "Add a new memory entry.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "character": {"type": "string", "default": "natsume"},
                "content": {"type": "string"},
            },
            "required": ["content"],
        },
    },
    {
        "name": "get_status",
        "description": "Get current system service health + active character.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "asr_transcribe",
        "description": "Transcribe speech from an audio file to text using Faster-Whisper small model. Supports wav/mp3/ogg/flac/m4a. Does NOT kill llama-server (Whisper uses separate ~1.5GB VRAM).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "audio_path": {"type": "string", "description": "Absolute path to the audio file to transcribe"},
            },
            "required": ["audio_path"],
        },
    },

    # ── AgentRQ-compatible Task Queue ──
    {
        "name": "getWorkspace",
        "description": "Get workspace info and task statistics (AgentRQ-compatible).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "getNextTask",
        "description": "Dequeue the next 'notstarted' task assigned to the agent, ordered by priority (sort_order). Returns null if none.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "createTask",
        "description": "Create a new task in the workspace. The agent can create tasks assigned to 'human' for follow-ups. Supports attachments as file paths.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "body": {"type": "string", "default": ""},
                "assignee": {"type": "string", "enum": ["human","agent"], "default": "human"},
                "attachments": {"type": "array", "items": {"type": "string"}, "description": "File paths to attach"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "updateTaskStatus",
        "description": "Transition task status (notstarted → ongoing → completed or blocked).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "taskId": {"type": "string"},
                "status": {"type": "string", "enum": ["notstarted","ongoing","completed","blocked"]},
            },
            "required": ["taskId","status"],
        },
    },
    {
        "name": "reply",
        "description": "Send a message in a task conversation thread.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "taskId": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["taskId","text"],
        },
    },
    {
        "name": "getTaskMessages",
        "description": "Read the conversation history of a task with pagination support.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "taskId": {"type": "string"},
                "cursor": {"type": "integer", "description": "Offset for pagination, default 0"},
                "limit": {"type": "integer", "default": 20},
            },
            "required": ["taskId"],
        },
    },
]

# ================================================================
# Tool Implementations — Artemis Capabilities
# ================================================================

def _read_current_character():
    soul_path = os.path.join(WORKSPACE, "SOUL.md")
    try:
        with open(soul_path, "r", encoding="utf-8") as f:
            first = f.readline().strip()
            if "Tool Mode" in first:
                return "tool"
            for name in ["Shiki Natsume","ATRI","Yono Sakura","Enola"]:
                if name in first:
                    return name.lower().replace(" ","_")
            return first.split(" — ")[-1].lower().split(" ")[0] if " — " in first else "unknown"
    except:
        return "natsume"

def tool_tts_generate(params):
    character = params.get("character","natsume")
    text = params["text"]
    lang = params.get("lang","ja")
    mood = params.get("mood","casual")

    out_id = uuid.uuid4().hex[:8]
    out_path = os.path.join(MEDIA_AUDIO, f"claude_tts_{out_id}.wav")

    # Try PowerShell TTS first (more reliable in Windows)
    ps_script = os.path.join(WORKSPACE, "skills","tts","run_tts.ps1")
    if os.path.exists(ps_script):
        try:
            escaped = text.replace('"','`"')
            result = subprocess.run(
                ["powershell","-ExecutionPolicy","Bypass","-File",ps_script,
                 "-text",escaped,"-lang",lang,"-mood",mood],
                capture_output=True, text=True, timeout=300, cwd=WORKSPACE
            )
            stdout = result.stdout + result.stderr
            if "DONE:" in stdout:
                for line in stdout.splitlines():
                    if "DONE:" in line and ".wav" in line:
                        path = line.split("DONE:")[-1].strip()
                        if os.path.exists(path):
                            return {"ok":True, "path":path, "character":character, "lang":lang, "mood":mood}
        except:
            pass

    # Fallback: Python TTS
    tts_call = os.path.join(WORKSPACE, "skills","tts","tts_call.py")
    if os.path.exists(tts_call):
        try:
            result = subprocess.run(
                [TTs_PYTHON, tts_call, "--text",text,"--lang",lang,"--mood",mood,
                 "--character",character,"--output",out_path],
                capture_output=True, text=True, timeout=120, cwd=WORKSPACE
            )
            if result.returncode == 0 and os.path.exists(out_path):
                return {"ok":True, "path":out_path, "character":character, "lang":lang, "mood":mood}
        except:
            pass

    return {"ok":False, "error":"TTS generation failed."}

def tool_comfyui_generate(params):
    positive = params["positive"]
    negative = params.get("negative","lowres, bad anatomy, bad hands, text, error, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, blurry")
    width = params.get("width",1200)
    height = params.get("height",1500)
    steps = params.get("steps",30)
    cfg = params.get("cfg",6.0)
    checkpoint = params.get("checkpoint","WAI-Nsfw-Illustrious-17.safetensors")

    ps_script = os.path.join(WORKSPACE,"skills","comfyui","run_comfyui.ps1")
    if not os.path.exists(ps_script):
        return {"ok":False, "error":f"Script not found: {ps_script}"}

    try:
        pos = positive.replace('"','`"').replace('$','`$')
        neg = negative.replace('"','`"').replace('$','`$')
        result = subprocess.run(
            ["powershell","-ExecutionPolicy","Bypass","-File",ps_script,
             "-positive",pos,"-negative",neg,
             "-width",str(width),"-height",str(height),
             "-steps",str(steps),"-cfg",str(cfg),
             "-checkpoint",checkpoint],
            capture_output=True, text=True, timeout=600, cwd=WORKSPACE
        )
        stdout = result.stdout + result.stderr
        if "DONE:" in stdout:
            for line in stdout.splitlines():
                if "DONE:" in line:
                    path = line.split("DONE:")[-1].strip()
                    if os.path.exists(path):
                        return {"ok":True, "path":path}
        if "FAILED" in stdout:
            return {"ok":False, "error":"ComfyUI generation failed.", "output":stdout[-300:]}
        return {"ok":False, "error":"Unknown result", "output":stdout[-300:]}
    except subprocess.TimeoutExpired:
        return {"ok":False, "error":"ComfyUI timed out (600s)"}
    except Exception as e:
        return {"ok":False, "error":str(e)}

def tool_live2d_emotion(params):
    motion = params.get("motion","Idle")
    text = params.get("text","")
    try:
        from urllib.request import Request, urlopen
        from urllib.parse import quote
        from urllib.error import URLError
        if text:
            url = f"{LIVE2D_BRIDGE}/api/emotion?motion={quote(motion)}&text={quote(text)}"
        else:
            url = f"{LIVE2D_BRIDGE}/api/motion?name={quote(motion)}"
        with urlopen(Request(url), timeout=5) as resp:
            return {"ok":True, "motion":motion, "text":text or None}
    except Exception as e:
        return {"ok":False, "error":f"Live2D bridge offline: {e}"}

def tool_switch_character(params):
    character = params["character"].lower()
    importer = os.path.join(WORKSPACE,"skills","character_importer","card_importer.py")
    if not os.path.exists(importer):
        return {"ok":False, "error":f"Importer not found: {importer}"}
    try:
        result = subprocess.run(
            [sys.executable, importer, "switch-harem", character],
            capture_output=True, text=True, timeout=30, cwd=WORKSPACE
        )
        stdout = result.stdout + result.stderr
        if "[OK]" in stdout or "Switched" in stdout:
            return {"ok":True, "character":character, "note":"Switched. Live2D model updated."}
        return {"ok":False, "error":stdout[:300]}
    except Exception as e:
        return {"ok":False, "error":str(e)}

def tool_list_characters(params):
    harem_dir = os.path.join(WORKSPACE,"skills","harem")
    chars = []
    try:
        if os.path.isdir(harem_dir):
            for entry in sorted(os.listdir(harem_dir)):
                p = os.path.join(harem_dir, entry)
                if os.path.isdir(p):
                    s = os.path.join(p,"SOUL.md")
                    title = "Unknown"
                    if os.path.exists(s):
                        with open(s,"r",encoding="utf-8") as f:
                            title = f.readline().strip()
                    chars.append({"name":entry,"title":title})
    except:
        pass
    return {"ok":True, "current":_read_current_character(), "characters":chars}

def tool_memory_search(params):
    character = params.get("character","natsume")
    query = params["query"]
    limit = params.get("limit",5)
    try:
        code = f"from skills.shared.mem0_bridge import search_mem0_qdrant; import json; print(json.dumps(search_mem0_qdrant('{character}','{query}',limit={limit}),ensure_ascii=False))"
        result = subprocess.run(["python","-c",code], capture_output=True, text=True, timeout=30, cwd=WORKSPACE)
        if result.returncode == 0 and result.stdout.strip():
            return {"ok":True, "results":json.loads(result.stdout)}
        return {"ok":False, "error":result.stderr[:200] or "Empty"}
    except Exception as e:
        return {"ok":False, "error":str(e)}

def tool_memory_add(params):
    character = params.get("character","natsume")
    content = params["content"]
    try:
        code = f"from skills.shared.mem0_bridge import add_memory; import json; print(json.dumps(add_memory('{character}','{content}'),ensure_ascii=False))"
        result = subprocess.run(["python","-c",code], capture_output=True, text=True, timeout=30, cwd=WORKSPACE)
        if result.returncode == 0:
            return {"ok":True, "stored":content[:100]}
        return {"ok":False, "error":result.stderr[:200]}
    except Exception as e:
        return {"ok":False, "error":str(e)}

def tool_get_status(params):
    import socket
    status = {"character":_read_current_character(), "services":{}}
    ports = {"llama":8080,"live2d":19200,"artemis_bridge":19250,"webchat":19270,"openclaw_gateway":18789,"embedding":9999}
    for name,port in ports.items():
        try:
            s = socket.create_connection(("127.0.0.1",port),timeout=1)
            s.close()
            status["services"][name] = "online"
        except:
            status["services"][name] = "offline"
    # Task stats
    with DB_LOCK:
        total = DB.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        pending = DB.execute("SELECT COUNT(*) FROM tasks WHERE status='notstarted' AND assignee='agent'").fetchone()[0]
        ongoing = DB.execute("SELECT COUNT(*) FROM tasks WHERE status='ongoing'").fetchone()[0]
        completed = DB.execute("SELECT COUNT(*) FROM tasks WHERE status='completed'").fetchone()[0]
    status["tasks"] = {"total":total,"pending":pending,"ongoing":ongoing,"completed":completed}
    return {"ok":True, **status}

def tool_asr_transcribe(params):
    audio_path = params["audio_path"]
    if not os.path.exists(audio_path):
        return {"ok":False, "error":f"Audio file not found: {audio_path}"}

    asr_script = os.path.join(WORKSPACE, "skills", "asr", "asr_call.py")
    if not os.path.exists(asr_script):
        return {"ok":False, "error":f"ASR script not found: {asr_script}"}

    try:
        result = subprocess.run(
            ["python", asr_script, audio_path],
            capture_output=True, text=True, timeout=300,
            cwd=WORKSPACE, env={**os.environ, "PYTHONIOENCODING":"utf-8"}
        )
        # ASR outputs recognized text to stdout, logs to stderr
        text = result.stdout.strip()
        if text:
            return {"ok":True, "text":text, "language":"auto"}
        else:
            stderr_tail = result.stderr.strip()[-200:] if result.stderr else ""
            return {"ok":False, "error":f"No transcription output.\nstderr: {stderr_tail}"}
    except subprocess.TimeoutExpired:
        return {"ok":False, "error":"ASR timed out (300s)"}
    except Exception as e:
        return {"ok":False, "error":str(e)}


# ================================================================
# Tool Implementations — AgentRQ-compatible Task Queue
# ================================================================

def _task_row_to_dict(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "body": row["body"],
        "status": row["status"],
        "assignee": row["assignee"],
        "created_by": row["created_by"],
        "sort_order": row["sort_order"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }

def tool_getWorkspace(params):
    with DB_LOCK:
        total = DB.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        pending = DB.execute("SELECT COUNT(*) FROM tasks WHERE status='notstarted' AND assignee='agent'").fetchone()[0]
        ongoing = DB.execute("SELECT COUNT(*) FROM tasks WHERE status='ongoing'").fetchone()[0]
        completed = DB.execute("SELECT COUNT(*) FROM tasks WHERE status='completed'").fetchone()[0]
    return {"ok":True,
        "name":"Artemis AI Girlfriend",
        "description":"100% Local AI Girlfriend harem — TTS, ComfyUI, Live2D, multiple characters.",
        "character":_read_current_character(),
        "task_stats":{"total":total,"pending":pending,"ongoing":ongoing,"completed":completed},
    }

def tool_getNextTask(params):
    with DB_LOCK:
        row = DB.execute(
            "SELECT * FROM tasks WHERE status='notstarted' AND assignee='agent' ORDER BY sort_order ASC, created_at ASC LIMIT 1"
        ).fetchone()
        if not row:
            return {"ok":True, "task":None, "message":"No pending tasks for agent."}
        task = _task_row_to_dict(row)
        # Also get message history
        msgs = DB.execute(
            "SELECT * FROM messages WHERE task_id=? ORDER BY created_at ASC", (task["id"],)
        ).fetchall()
        task["messages"] = [{ "id":m["id"],"sender":m["sender"],"text":m["text"],"created_at":m["created_at"] } for m in msgs]
    return {"ok":True, "task":task}

def tool_createTask(params):
    title = params["title"]
    body = params.get("body","")
    assignee = params.get("assignee","human")
    attachments = params.get("attachments",[])
    tid = str(uuid.uuid4())[:8]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with DB_LOCK:
        # Get max sort_order for agent tasks
        max_order_row = DB.execute(
            "SELECT COALESCE(MAX(sort_order),-1) FROM tasks WHERE assignee='agent'"
        ).fetchone()
        sort_order = max_order_row[0] + 1 if assignee == "agent" else 0

        DB.execute(
            "INSERT INTO tasks(id,title,body,status,assignee,created_by,sort_order,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (tid, title, body, "notstarted", assignee, "agent", sort_order, now, now)
        )
        # Attachment message
        if attachments:
            attach_text = "📎 Attachments:\n" + "\n".join(attachments)
            DB.execute("INSERT INTO messages(id,task_id,sender,text,created_at) VALUES(?,?,?,?,?)",
                       (str(uuid.uuid4())[:8], tid, "agent", attach_text, now))
        DB.commit()

    task = _task_row_to_dict(DB.execute("SELECT * FROM tasks WHERE id=?",(tid,)).fetchone())
    return {"ok":True, "task":task}

def tool_updateTaskStatus(params):
    tid = params["taskId"]
    status = params["status"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with DB_LOCK:
        existing = DB.execute("SELECT * FROM tasks WHERE id=?",(tid,)).fetchone()
        if not existing:
            return {"ok":False, "error":f"Task '{tid}' not found."}
        DB.execute("UPDATE tasks SET status=?, updated_at=? WHERE id=?",(status,now,tid))
        # Auto-message on status change
        msg_text = f"📌 Status changed: {existing['status']} → {status}"
        DB.execute("INSERT INTO messages(id,task_id,sender,text,created_at) VALUES(?,?,?,?,?)",
                   (str(uuid.uuid4())[:8], tid, "system", msg_text, now))
        DB.commit()
    return {"ok":True, "taskId":tid, "status":status, "previous":existing["status"]}

def tool_reply(params):
    tid = params["taskId"]
    text = params["text"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mid = str(uuid.uuid4())[:8]
    with DB_LOCK:
        existing = DB.execute("SELECT id FROM tasks WHERE id=?",(tid,)).fetchone()
        if not existing:
            return {"ok":False, "error":f"Task '{tid}' not found."}
        DB.execute("INSERT INTO messages(id,task_id,sender,text,created_at) VALUES(?,?,?,?,?)",
                   (mid, tid, "agent", text, now))
        DB.commit()
    return {"ok":True, "messageId":mid, "taskId":tid}

def tool_getTaskMessages(params):
    tid = params["taskId"]
    cursor = params.get("cursor",0)
    limit = params.get("limit",20)
    with DB_LOCK:
        msgs = DB.execute(
            "SELECT * FROM messages WHERE task_id=? ORDER BY created_at ASC LIMIT ? OFFSET ?",
            (tid, limit, cursor)
        ).fetchall()
        total = DB.execute("SELECT COUNT(*) FROM messages WHERE task_id=?",(tid,)).fetchone()[0]
    result = [{ "id":m["id"],"sender":m["sender"],"text":m["text"],"created_at":m["created_at"] } for m in msgs]
    next_cursor = cursor + limit if cursor + limit < total else None
    return {"ok":True, "messages":result, "total":total, "nextCursor":next_cursor}


TOOL_HANDLERS = {
    # Artemis capabilities
    "tts_generate": tool_tts_generate,
    "comfyui_generate": tool_comfyui_generate,
    "live2d_emotion": tool_live2d_emotion,
    "switch_character": tool_switch_character,
    "list_characters": tool_list_characters,
    "memory_search": tool_memory_search,
    "memory_add": tool_memory_add,
    "get_status": tool_get_status,
    "asr_transcribe": tool_asr_transcribe,
    # AgentRQ-compatible task queue
    "getWorkspace": tool_getWorkspace,
    "getNextTask": tool_getNextTask,
    "createTask": tool_createTask,
    "updateTaskStatus": tool_updateTaskStatus,
    "reply": tool_reply,
    "getTaskMessages": tool_getTaskMessages,
}


# ================================================================
# JSON-RPC Dispatch
# ================================================================

def handle_request(req):
    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params",{})

    if method == "initialize":
        return {
            "jsonrpc":"2.0", "id":req_id,
            "result":{
                "protocolVersion":"2024-11-05",
                "serverInfo":SERVER_INFO,
                "capabilities":{"tools":{}},
            },
        }

    elif method == "tools/list":
        return {"jsonrpc":"2.0", "id":req_id, "result":{"tools":TOOLS}}

    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments",{})
        handler = TOOL_HANDLERS.get(tool_name)
        if handler:
            try:
                result = handler(tool_args)
                return {
                    "jsonrpc":"2.0", "id":req_id,
                    "result":{
                        "content":[{"type":"text","text":json.dumps(result,ensure_ascii=False)}],
                        "isError": not result.get("ok",False),
                    },
                }
            except Exception as e:
                return {
                    "jsonrpc":"2.0","id":req_id,
                    "result":{
                        "content":[{"type":"text","text":json.dumps({"ok":False,"error":str(e)})}],
                        "isError":True,
                    },
                }
        else:
            return {"jsonrpc":"2.0","id":req_id,"error":{"code":-32601,"message":f"Tool '{tool_name}' not found"}}

    elif method == "notifications/initialized":
        return None

    elif method == "ping":
        return {"jsonrpc":"2.0","id":req_id,"result":{}}

    else:
        return {"jsonrpc":"2.0","id":req_id,"error":{"code":-32601,"message":f"Method '{method}' not found"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle_request(req)
            if resp is not None:
                sys.stdout.write(json.dumps(resp,ensure_ascii=False)+"\n")
                sys.stdout.flush()
        except json.JSONDecodeError as e:
            sys.stderr.write(f"JSON parse error: {e}\n")
            sys.stderr.flush()
        except BrokenPipeError:
            break
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()


if __name__ == "__main__":
    main()
