# ComfyUI 文生图 Skill / ComfyUI Image Generation Skill

## 中文

ComfyUI 文生图执行技能（主 session 专用，必须 spawn 子 session，不能直接 exec）。

ComfyUI 推理会杀 llama-server 腾显存，直接 exec 会导致主 session 503。

### 文件结构

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 完整执行手册（spawn 流程、时序窗口保证、故障排查） |
| `comfyui_call.py` | 推理脚本（stop_llama → GPU 推理 → start_llama → 三阶段检测） |
| `run_comfyui.ps1` | PowerShell 包装（文件锁、TimeoutGuard、复制媒体、写 .task_flags） |
| `prompt_template.md` | 角色 prompt 模板 |
| `apron_prompt.txt` / `apron_negative.txt` / `custom_prompt.txt` | 预设 prompt |

### 依赖

- **`skills/comfyui_core/`** — ComfyUI 引擎代码（由 `comfyui_call.py` 自动定位，勿删）

### 快速使用（主 session 走 SKILL.md 的 spawn 流程）

```javascript
// 参见 SKILL.md STEP 2 模板：
sessions_spawn({ task: "...run_comfyui.ps1 -positive ... -negative ...", mode: "run" })
```

## English

ComfyUI image generation skill (main-session only; must spawn a sub-session, never exec directly).

ComfyUI inference kills llama-server to free VRAM; direct exec will 503 the main session.

### Files

| File | Description |
|------|-------------|
| `SKILL.md` | Full execution manual (spawn flow, timing guarantees, troubleshooting) |
| `comfyui_call.py` | Inference script (stop_llama → GPU inference → start_llama → 3-stage checks) |
| `run_comfyui.ps1` | PowerShell wrapper (file lock, TimeoutGuard, media copy, .task_flags) |
| `prompt_template.md` | Character prompt templates |
| `apron_prompt.txt` / `apron_negative.txt` / `custom_prompt.txt` | Preset prompts |

### Dependencies

- **`skills/comfyui_core/`** — ComfyUI engine code (auto-located by `comfyui_call.py`, do not delete)

### Quick Start (main session follows the spawn flow in SKILL.md)

```javascript
// See SKILL.md STEP 2 template:
sessions_spawn({ task: "...run_comfyui.ps1 -positive ... -negative ...", mode: "run" })
```
