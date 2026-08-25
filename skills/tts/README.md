# GPT-SoVITS TTS Skill / 语音合成技能

## 中文

GPT-SoVITS 语音合成执行技能（主 session 专用，必须 spawn 子 session，不能直接 exec）。

TTS 推理会杀 llama-server 腾显存，直接 exec 会导致主 session 503。

### 文件结构

| 文件/目录 | 说明 |
|-----------|------|
| `SKILL.md` | 完整执行手册（spawn 流程、时序窗口保证、故障排查） |
| `tts_call.py` | 推理脚本（stop_llama → TTS → start_llama → 三阶段检测） |
| `tts_http_call.py` | HTTP 模式推理（自动探测并启动内置 sovits 引擎） |
| `run_tts.ps1` / `run_tts_http.ps1` | PowerShell 包装（文件锁、复制 wav、写 .task_flags） |
| `live2d_sync.py` | Live2D 口型同步辅助 |
| `ref_wavs_*/` | 各角色参考音频 |

### 依赖

- **`skills/sovits/`** — GPT-SoVITS 引擎（由 `tts_call.py` / `tts_http_call.py` 自动定位，勿删）

### 参数速查

| 参数 | 说明 |
|------|------|
| text | 要合成的文本 |
| lang | ja=日文, zh=中文, en=英文（默认 ja） |
| mood | casual=日常温柔, tsundere=傲娇, romantic=深情, long=长句（默认自动匹配） |

### 快速使用（主 session 走 SKILL.md 的 spawn 流程）

```javascript
// 参见 SKILL.md STEP 2 模板：
sessions_spawn({ task: "...run_tts.ps1 -text ... -lang ja -mood casual", mode: "run" })
```

## English

GPT-SoVITS text-to-speech skill (main-session only; must spawn a sub-session, never exec directly).

TTS inference kills llama-server to free VRAM; direct exec will 503 the main session.

### Files

| File/Dir | Description |
|----------|-------------|
| `SKILL.md` | Full execution manual (spawn flow, timing guarantees, troubleshooting) |
| `tts_call.py` | Inference script (stop_llama → TTS → start_llama → 3-stage checks) |
| `tts_http_call.py` | HTTP-mode inference (auto-detects and starts the built-in sovits engine) |
| `run_tts.ps1` / `run_tts_http.ps1` | PowerShell wrappers (file lock, wav copy, .task_flags) |
| `live2d_sync.py` | Live2D lip-sync helper |
| `ref_wavs_*/` | Per-character reference audio |

### Dependencies

- **`skills/sovits/`** — GPT-SoVITS engine (auto-located by `tts_call.py` / `tts_http_call.py`, do not delete)

### Parameter Reference

| Param | Description |
|-------|-------------|
| text | Text to synthesize |
| lang | ja=Japanese, zh=Chinese, en=English (default: ja) |
| mood | casual, tsundere, romantic, long (default: auto-match) |

### Quick Start (main session follows the spawn flow in SKILL.md)

```javascript
// See SKILL.md STEP 2 template:
sessions_spawn({ task: "...run_tts.ps1 -text ... -lang ja -mood casual", mode: "run" })
```
