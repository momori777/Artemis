/**
 * Live2D WebSocket Bridge
 * ────────────────────────
 * 本地 HTTP + WebSocket 服务，OpenClaw 通过 HTTP 调用控制 Live2D 前端。
 *
 * 端口: 19200 (HTTP API) + 19201 (WebSocket)
 *
 * 用法: node live2d-bridge.mjs
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execFile, execSync } from 'node:child_process';
import { WebSocketServer } from 'ws';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ========== CONFIG ==========
const HTTP_PORT = 19200;
const WS_PORT = 19201;
const STATIC_DIR = __dirname;
const NODE_MODULES = path.join(__dirname, 'node_modules');
const AUDIO_CACHE_DIR = path.join(__dirname, 'audio_cache');
const AUDIO_CACHE_MAX_FILES = 50;
const AUDIO_CACHE_MAX_AGE_MS = 30 * 60 * 1000; // 30 min

// Serve node_modules files at /node_modules/... path
const NODE_MODULES_ALIASES = {
  '/pixi.min.js': 'pixi.js/dist/pixi.min.js',
};

// ========== CLIENTS ==========
/** @type {Set<import('ws').WebSocket>} */
const clients = new Set();

// ========== GPT-SoVITS 常驻管理 ==========
let sovitsProcess = null;
let sovitsRunning = false;
const SOVITS_PORT = 9880;

async function probeSovits(timeout = 2) {
  try {
    const { stdout } = await execFile('powershell', [
      '-NoProfile', '-Command',
      `(New-Object Net.WebClient).DownloadString('http://127.0.0.1:${SOVITS_PORT}/')` ,
    ], { timeout: timeout * 1000 });
    return true;
  } catch { return false; }
}

async function startSovits() {
  if (sovitsRunning) return { ok: true, message: 'GPT-SoVITS 已在运行' };

  // 读取 config.yaml 获取路径
  const configPath = path.join(__dirname, '..', 'config.yaml');
  if (!fs.existsSync(configPath)) {
    return { ok: false, message: '找不到 config.yaml' };
  }

  const configContent = fs.readFileSync(configPath, 'utf-8');
  const sovitsPythonMatch = configContent.match(/sovits_python:\s*["']?([^"'\r\n]+)/);
  const sovitsRootMatch = configContent.match(/sovits_root:\s*["']?([^"'\r\n]+)/);

  if (!sovitsPythonMatch || !sovitsRootMatch) {
    return { ok: false, message: 'config.yaml 中缺少 sovits_python 或 sovits_root' };
  }

  const sovitsPy = sovitsPythonMatch[1].trim().replace(/"/g, '');
  const sovitsRoot = sovitsRootMatch[1].trim().replace(/"/g, '');

  // 查找 inference_webui.py
  let webuiPath = null;
  const dirsToCheck = [sovitsRoot, path.join(sovitsRoot, 'runtime')];
  for (const base of dirsToCheck) {
    const candidate = path.join(base, 'inference_webui.py');
    if (fs.existsSync(candidate)) { webuiPath = candidate; break; }
    // 递归查找
    const findWebui = (dir) => {
      if (!fs.existsSync(dir)) return null;
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const e of entries) {
        const full = path.join(dir, e.name);
        if (e.isFile() && e.name === 'inference_webui.py') return full;
        if (e.isDirectory()) { const r = findWebui(full); if (r) return r; }
      }
      return null;
    };
    if (!webuiPath) webuiPath = findWebui(base);
    if (webuiPath) break;
  }

  if (!webuiPath) {
    return { ok: false, message: '找不到 inference_webui.py' };
  }

  const cmd = [sovitsPy, webuiPath, '--port', String(SOVITS_PORT)];
  console.log(`[SOVITS] 启动: ${cmd.join(' ')}`);

  sovitsProcess = execFile(sovitsPy, [webuiPath, '--port', String(SOVITS_PORT)], {
    cwd: sovitsRoot,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
    windowsHide: true,
  });

  // 等待服务就绪
  let attempts = 0;
  while (attempts < 30) {
    await new Promise(r => setTimeout(r, 2000));
    if (await probeSovits(1)) {
      sovitsRunning = true;
      console.log('[SOVITS] HTTP 服务启动成功 (端口 9880)');
      broadcast({ type: 'sovits_state', running: true });
      return { ok: true, message: 'GPT-SoVITS 已启动，端口 9880' };
    }
    attempts++;
  }

  sovitsRunning = false;
  return { ok: false, message: 'GPT-SoVITS 启动超时' };
}

async function stopSovits() {
  if (!sovitsRunning && !await probeSovits(1)) {
    return { ok: true, message: 'GPT-SoVITS 未在运行' };
  }

  if (sovitsProcess) {
    try { sovitsProcess.kill('SIGTERM'); } catch {}
    sovitsProcess = null;
  }

  // Windows: 杀 9880 端口进程
  try {
    await execFile('powershell', ['-NoProfile', '-Command',
      `$procs = Get-NetTCPConnection -LocalPort ${SOVITS_PORT} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; ` +
      `foreach ($pid in $procs) { if ($pid) { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } }`,
    ], { timeout: 5000 });
  } catch {}

  sovitsRunning = false;
  console.log('[SOVITS] 已停止');
  broadcast({ type: 'sovits_state', running: false });
  return { ok: true, message: 'GPT-SoVITS 已停止' };
}

// ========== Audio Cache (serves TTS output for streaming lip-sync) ==========
function ensureAudioCacheDir() {
  if (!fs.existsSync(AUDIO_CACHE_DIR)) {
    fs.mkdirSync(AUDIO_CACHE_DIR, { recursive: true });
  }
}

function cleanupAudioCache() {
  ensureAudioCacheDir();
  const now = Date.now();
  const files = fs.readdirSync(AUDIO_CACHE_DIR)
    .map(name => {
      const full = path.join(AUDIO_CACHE_DIR, name);
      try {
        const stat = fs.statSync(full);
        return { path: full, name, mtime: stat.mtimeMs };
      } catch { return null; }
    })
    .filter(Boolean);

  // Remove expired
  for (const f of files) {
    if (now - f.mtime > AUDIO_CACHE_MAX_AGE_MS) {
      try { fs.unlinkSync(f.path); } catch {}
    }
  }

  // Trim to max files (oldest first)
  const remaining = files
    .filter(f => fs.existsSync(f.path))
    .sort((a, b) => a.mtime - b.mtime);
  for (const f of remaining.slice(0, -AUDIO_CACHE_MAX_FILES)) {
    try { fs.unlinkSync(f.path); } catch {}
  }
}

/** Cache an audio file (e.g., TTS output wav) and return its URL */
function cacheAudioFile(sourcePath) {
  ensureAudioCacheDir();
  cleanupAudioCache();

  if (!fs.existsSync(sourcePath)) {
    throw new Error(`Audio file not found: ${sourcePath}`);
  }

  const ext = path.extname(sourcePath) || '.wav';
  const cachedName = `${randomUUID()}${ext}`;
  const cachedPath = path.join(AUDIO_CACHE_DIR, cachedName);
  fs.copyFileSync(sourcePath, cachedPath);

  return `/cache/audio/${cachedName}`;
}

// ========== MIME types ==========
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.moc3': 'application/octet-stream',
  '.cdi3.json': 'application/json',
  '.exp3.json': 'application/json',
  '.motion3.json': 'application/json',
  '.physics3.json': 'application/json',
  '.model3.json': 'application/json',
  '.css': 'text/css; charset=utf-8',
  '.wav': 'audio/wav',
  '.mp3': 'audio/mpeg',
  '.ogg': 'audio/ogg',
  '.mjs': 'application/javascript; charset=utf-8',
};

// ========== Broadcast to all WebSocket clients ==========
function broadcast(data) {
  const msg = JSON.stringify(data);
  for (const client of clients) {
    if (client.readyState === 1) { // WebSocket.OPEN
      client.send(msg);
    }
  }
}

// ========== HTTP Server (static + API) ==========
const httpServer = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${HTTP_PORT}`);
  const pathname = decodeURIComponent(url.pathname);

  // CORS for cross-origin calls from the web-chat frontend (127.0.0.1:19270)
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // ---- API Routes ----
  if (pathname === '/api/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      ok: true,
      clients: clients.size,
      uptime: process.uptime(),
    }));
    return;
  }

  // ---- Model list & switching (Live2D settings panel) ----
  if (pathname === '/api/models') {
    try {
      const modelRoot = path.join(STATIC_DIR, 'model');
      const models = [];
      if (fs.existsSync(modelRoot)) {
        for (const dir of fs.readdirSync(modelRoot)) {
          const dirPath = path.join(modelRoot, dir);
          if (!fs.statSync(dirPath).isDirectory()) continue;
          // Find all .model3.json recursively (some models nest deeper)
          const found = [];
          (function walk(d) {
            for (const ent of fs.readdirSync(d)) {
              const p = path.join(d, ent);
              const st = fs.statSync(p);
              if (st.isDirectory()) walk(p);
              else if (ent.endsWith('.model3.json')) found.push(path.relative(modelRoot, p).split(path.sep).join('/'));
            }
          })(dirPath);
          if (found.length) {
            models.push({
              id: dir,
              name: dir,
              models: found,
            });
          }
        }
      }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, models }));
    } catch (e) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: false, error: e.message }));
    }
    return;
  }

  if (pathname === '/api/switch-model') {
    const model = url.searchParams.get('model') || '';
    if (!model) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: false, error: 'model param required (relative path under /model/)' }));
      return;
    }
    // Security: model must resolve under STATIC_DIR/model
    const modelRootDir = path.join(STATIC_DIR, 'model');
    const resolvedModel = path.resolve(modelRootDir, model);
    const resolvedRoot = path.resolve(modelRootDir);
    if (!resolvedModel.startsWith(resolvedRoot + path.sep)) {
      res.writeHead(403, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: false, error: 'model path must be under /model/' }));
      return;
    }
    const modelUrl = '/' + model.split(path.sep).join('/').replace(/^\/+/, '');
    if (!fs.existsSync(resolvedModel)) {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: false, error: `model file not found: ${modelUrl}` }));
      return;
    }
    // Rewrite var MODEL= in index.html (same mechanism as switch_model.ps1)
    const indexPath = path.join(STATIC_DIR, 'index.html');
    try {
      let content = fs.readFileSync(indexPath, 'utf-8');
      if (!/var MODEL\s*=/.test(content)) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: 'index.html has no var MODEL= line' }));
        return;
      }
      const titleMatch = content.match(/<title>([^<]*)<\/title>/);
      const oldTitle = titleMatch ? titleMatch[1] : 'Live2D';
      const modelName = path.basename(path.dirname(modelUrl)) + ' / ' + path.basename(modelUrl);
      content = content.replace(/var MODEL\s*=\s*'[^']*'/, `var MODEL='${modelUrl}'`);
      content = content.replace(/<title>[^<]*<\/title>/, `<title>${modelName}</title>`);
      fs.writeFileSync(indexPath, content, 'utf-8');
      // Tell all connected Live2D pages to reload so they pick up the new model
      broadcast({ type: 'model_changed', model: modelUrl, title: modelName });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, model: modelUrl, title: modelName, oldTitle }));
    } catch (e) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: false, error: e.message }));
    }
    return;
  }

  if (pathname === '/api/expression') {
    const name = url.searchParams.get('name') || 'neutral';
    broadcast({ type: 'expression', name });
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true, type: 'expression', name }));
    return;
  }

  if (pathname === '/api/motion') {
    const name = url.searchParams.get('name') || 'idle';
    broadcast({ type: 'motion', name });
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true, type: 'motion', name }));
    return;
  }

  if (pathname === '/api/message') {
    const text = url.searchParams.get('text') || '';
    const duration = parseInt(url.searchParams.get('duration') || '5000');
    broadcast({ type: 'message', text, duration });
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true, type: 'message', text, duration }));
    return;
  }

  if (pathname === '/api/speak') {
    const action = url.searchParams.get('action') || 'start';
    const text = url.searchParams.get('text') || '';
    if (action === 'start') {
      broadcast({ type: 'speak_start', text });
    } else {
      broadcast({ type: 'speak_end' });
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true, type: 'speak', action }));
    return;
  }

  if (pathname === '/api/emotion') {
    // Combined: expression + motion + text
    const expression = url.searchParams.get('expression') || '';
    const motion = url.searchParams.get('motion') || '';
    const text = url.searchParams.get('text') || '';

    if (expression) broadcast({ type: 'expression', name: expression });
    if (motion) broadcast({ type: 'motion', name: motion });
    if (text) broadcast({ type: 'message', text });

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true, expression, motion, text }));
    return;
  }

  if (pathname === '/api/reset') {
    broadcast({ type: 'reset' });
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true, type: 'reset' }));
    return;
  }

  if (pathname === '/api/sovits') {
    const action = url.searchParams.get('action') || 'status';
    if (action === 'start') {
      const result = await startSovits();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result));
    } else if (action === 'stop') {
      const result = await stopSovits();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result));
    } else {
      // status
      const isRunning = sovitsRunning || await probeSovits(1);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, running: isRunning, port: SOVITS_PORT }));
    }
    return;
  }

  // /api/speak_audio — stream audio to Live2D with real lip-sync
  // action=start&audio_path=<local file path>&text=<optional>
  // action=end
  if (pathname === '/api/speak_audio') {
    const action = url.searchParams.get('action') || 'start';
    const audioPath = url.searchParams.get('audio_path') || '';
    const text = url.searchParams.get('text') || '';

    if (action === 'start') {
      let audioUrl = '';
      if (audioPath) {
        try {
          audioUrl = cacheAudioFile(audioPath);
        } catch (e) {
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ ok: false, error: e.message }));
          return;
        }
      }
      broadcast({
        type: 'speak_audio',
        action: 'start',
        audio_url: audioUrl ? `http://localhost:${HTTP_PORT}${audioUrl}` : '',
        text: text
      });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, audio_url: audioUrl }));
    } else {
      broadcast({ type: 'speak_audio', action: 'end' });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true }));
    }
    return;
  }

  // ---- Audio Cache static serving ----
  if (pathname.startsWith('/cache/audio/')) {
    const fileName = pathname.replace('/cache/audio/', '');
    // Sanitize: only allow hex UUID + safe extensions
    if (!/^[a-f0-9-]+\.(wav|mp3|ogg|webm)$/i.test(fileName)) {
      res.writeHead(403);
      res.end('Forbidden');
      return;
    }
    const filePath = path.join(AUDIO_CACHE_DIR, fileName);
    if (!fs.existsSync(filePath)) {
      res.writeHead(404);
      res.end('Not found');
      return;
    }
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, {
      'Content-Type': MIME[ext] || 'audio/wav',
      'Cache-Control': 'public, max-age=3600',
      'Accept-Ranges': 'bytes'
    });
    fs.createReadStream(filePath).pipe(res);
    return;
  }

  // ---- Static file serving ----
  let filePath;

  // Debug: log pathname for all requests
  console.log(`📄 ${req.method} ${pathname}`);

    // Silently ignore favicon requests
  if (pathname === "/favicon.ico") {
    res.writeHead(204);
    res.end();
    return;
  }

  // Check node_modules aliases first
  if (NODE_MODULES_ALIASES[pathname]) {
    filePath = path.join(NODE_MODULES, NODE_MODULES_ALIASES[pathname]);
    if (fs.existsSync(filePath)) {
      const ext = path.extname(filePath);
      const contentType = MIME[ext] || 'application/octet-stream';
      res.writeHead(200, { 'Content-Type': contentType, 'Cache-Control': 'public, max-age=3600' });
      fs.createReadStream(filePath).pipe(res);
      return;
    }
  }

  filePath = pathname === '/' ? '/index.html' : pathname;
  filePath = path.join(STATIC_DIR, filePath);

  // Security: prevent traversal (use resolved path to avoid encoding issues)
  const resolvedPath = path.resolve(filePath);
  const resolvedRoot = path.resolve(STATIC_DIR);
  if (!resolvedPath.startsWith(resolvedRoot + path.sep) && resolvedPath !== resolvedRoot) {
    console.log(`🚫 Blocked traversal: ${filePath}`);
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  if (!fs.existsSync(filePath)) {
    res.writeHead(404);
    res.end('Not found');
    return;
  }

  const ext = path.extname(filePath);
  const contentType = MIME[ext] || 'application/octet-stream';
  res.writeHead(200, { 'Content-Type': contentType, 'Cache-Control': 'no-store' });
  fs.createReadStream(filePath).pipe(res);
});

// ========== WebSocket Server ==========
const wss = new WebSocketServer({ port: WS_PORT });

wss.on('connection', (ws, req) => {
  const ip = req.socket.remoteAddress;
  console.log(`🔗 WS client connected: ${ip}`);
  clients.add(ws);

  ws.on('message', (raw) => {
    try {
      const msg = JSON.parse(raw.toString());
      console.log('📩 WS message from client:', msg.type);
    } catch (e) {
      // ignore non-JSON
    }
  });

  ws.on('close', () => {
    console.log(`🔌 WS client disconnected: ${ip}`);
    clients.delete(ws);
  });

  ws.on('error', (err) => {
    console.error('WS error:', err.message);
    clients.delete(ws);
  });
});

// ========== Start ==========
httpServer.listen(HTTP_PORT, () => {
  console.log('');
  console.log('🎭 Live2D Bridge 已启动');
  console.log(`   HTTP:    http://localhost:${HTTP_PORT}`);
  console.log(`   WebSocket: ws://localhost:${WS_PORT}`);
  console.log('');
  console.log('   API 接口:');
  console.log(`   GET /api/expression?name=<exp_01~05|neutral|happy|sad|angry|surprised>`);
  console.log(`   GET /api/motion?name=<idle|mtn_01|mtn_02|mtn_03>`);
  console.log(`   GET /api/message?text=<文本>&duration=<毫秒>`);
  console.log(`   GET /api/speak_audio?action=start&audio_path=<本地wav路径>&text=<文本>`);
  console.log(`   GET /api/speak_audio?action=end`);
  console.log(`   GET /api/speak?action=start|end&text=<文本>           (legacy)`);
  console.log(`   GET /api/emotion?expression=<>&motion=<>&text=<>&duration=<>`);
  console.log(`   GET /api/reset`);
  console.log(`   GET /api/status`);
  console.log(`   GET /api/sovits?action=start|stop|status`);
  console.log(`   GET /cache/audio/<uuid>.wav                          (audio serving)`);
  console.log('');
});
