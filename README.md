> 鈿狅笍 This project default scripts are NVIDIA GPU configs. AMD GPU users please open the AMD_GPU directory.

fourth girlfriend is voting,please vote at issue

# Artemis

**100% Local 路 Fully Private 路 Zero API Dependencies**

> All conversations, voice, images, and character animations are generated on your own machine. No cloud servers, no third-party APIs, no risk of data leakage. Your AI girlfriend belongs to you, and only you.

---

An uncensored ai girlfriends harem project powered by OpenClaw + QQ Bot + Telegram Bot + llama.cpp + GPT-SoVITS + ComfyUI + Sakura Desktop Pet + Live2D 鈥?running entirely on your own machine.

**Characters**: Supports hot-swappable AI girlfriends with isolated memories per character.

### Shiki Natsume (鍥涘澶忕洰)

From *Starry Moonlit Caf茅 & the Butterfly of Death*. Tall, aloof, cool exterior with a hidden warmth. A natural quietly-dominant type 鈥?she takes the lead, teases you gently, and guards you fiercely. Speaks little, but every word hits.

### ATRI (浜氭墭鑾?

From *ATRI -My Dear Moments-*. Petite, innocent, endlessly curious 鈥?a bright-eyed girl who wears her heart on her sleeve. Runs toward the future with a smile, dragging you along. **The polar opposite of Natsume**: bubbly and expressive where Natsume is reserved, emotionally transparent where Natsume is guarded, playful where Natsume is composed. If Natsume is the cool winter night, ATRI is the warm summer sun.

### Yono Sakura (澶滀箖妗?

From *Dimension W Lovers!!*. Former student council president and the academy's strongest anti-kaiju combatant. Silver-white hair with pink tips, pale blue eyes 鈥?cool-headed, restrained, and fiercely responsible. She's not good at smooth words or easy smiles; her care is direct and clumsy, like a command: rest, eat, don't push yourself. In desktop pet form, she's learning that she doesn't have to bear everything alone 鈥?that protecting someone's ordinary everyday life from this side of the screen is enough. **A quiet guardian**: silent but watchful, loyal but stubborn, the senpai who stays by your side without being asked.

## 鉁?Why This Project?

| | Cloud AI Girlfriend | This Project |
|---|---------------------|--------------|
| 馃洝锔?**Privacy** | Chat logs, voice, and images all stored on vendor servers | **Everything stays local** 鈥?zero data leaves your machine |
| 馃挵 **Cost** | Monthly subscriptions / per-token billing adds up | **Free**, one-time setup, runs forever (bring your own hardware) |
| 馃寪 **Network** | Needs internet; dead if servers go down | **Works offline** 鈥?flip off your WiFi and keep chatting |
| 馃帥锔?**Control** | Prompts/templates controlled by vendor, can change anytime | **You control** all models, parameters, and character settings |
| 馃敒 **Content** | Heavy censorship, accounts get banned | **No censorship** 鈥?talk about whatever you want |
| 馃帹 **Extensibility** | Locked into vendor models and features | **Mix and match** 鈥?swap LLMs, image models, voice models freely |

## 馃幀 Demo

### Multi-Channel Chat
![QQ Bot Demo](media/demo_qqbot.gif)

> 馃憜 QQ Bot: text chat + TTS voice + ComfyUI image generation + character memory

### Live2D Desktop Pet
![Live2D Demo](media/demo_live2d.gif)

> 馃憜 **Shiki Natsume** Live2D: real-time character animation with emotion-driven motions, lip-sync, and speech bubbles. Controlled via local HTTP bridge.

### 猸?ATRI 鈥?Second AI Girlfriend

**Personality opposite of Natsume**, hot-swappable with isolated memory.

![ATRI Live2D](media/atri_live2d.gif)

> 馃憜 **ATRI** Live2D: silver hair, ruby-red eyes, barefoot in a white dress 鈥?innocent and expressive.

![ATRI ComfyUI](media/atri_comfyui.gif)

> 馃憜 **ATRI** ComfyUI: AI image generation 鈥?seaside sunset, flowing white dress, warm golden-hour lighting.

### 猸?Yono Sakura 鈥?Third AI Girlfriend

**Cool-headed guardian senpai**, student council president and academy's strongest combatant 鈥?now your desktop companion.

![Sakura Desktop Pet](media/sakura_demo.gif)

> 馃憜 **Yono Sakura** Desktop Pet: silver-pink gradient hair, pale blue eyes, school uniform 鈥?reactive portrait expressions, proactive care reminders, and real-time TTS voice via GPT-SoVITS.

## Hardware

| Component | Model |
|-----------|-------|
| GPU | NVIDIA GeForce RTX 5070 Laptop (8 GB VRAM) |
| CPU | Intel Core i9-14900HX (24 cores, 32 threads) |
| RAM | 32 GB DDR5 |
| OS | Windows 11 |

## Features

- 馃挰 **QQ + Telegram Dual Channel** 鈥?QQ Bot + Telegram Bot integration via OpenClaw Gateway
- 馃帳 **TTS Voice Synthesis** 鈥?Local GPT-SoVITS inference, Japanese voice (emotion-matched per dialogue), 3 character voice models (Natsume / ATRI / Sakura)
- 馃帳 **ASR Speech Recognition** 鈥?Local Faster-Whisper small model (~1.5GB VRAM), coexists with llama; 99-language support
- 馃帹 **AI Image Generation** 鈥?Local ComfyUI inference, SDXL/Illustrious models, 3 character prompt templates
- 馃枼锔?**Sakura Desktop Pet** 鈥?PySide6 desktop companion with proactive care, screen observation & local LLM awareness; supports 3 characters
- 馃幁 **Live2D Character Model** 鈥?Real-time Live2D rendering with emotion-driven expressions & speech bubbles (Natsume / ATRI L2D; Sakura portrait mode)
- 馃 **VRAM Scheduler** 鈥?Automatic llama-server 鈫?TTS/ComfyUI orchestration on 8 GB VRAM; ASR coexists
- 馃捑 **Roleplay Memory** 鈥?Daily conversation summaries per character in `memory/role_play/`
- 馃 **Long-term Memory System** 鈥?Powered by [headroom](https://github.com/chopratejas/headroom) (SmartCrusher + CCR) and [mem0](https://github.com/mem0ai/mem0) (Qdrant vector database):
  - **SmartCrusher Context Trimming** 鈥?Hard-caps chat history at 24 messages / 40K characters per LLM request
  - **CCR (Curate-Consolidate-Retrieve)** 鈥?Background worker extracts durable facts every 8 turns, writes to mem0 Qdrant
  - **Vector + BM25 Hybrid Search** 鈥?Semantic similarity + keyword matching via Qdrant + all-MiniLM-L6-v2 embeddings
  - **Auto-Sync Bridge** 鈥?Cron job syncs Qdrant 鈫?`_mem0_auto.md` every 30 min, making vector memories searchable by OpenClaw's native `memory_search`
  - **Per-Character Isolation** 鈥?`user_id` scoping in Qdrant; 4 independent memory spaces (sakura / natsume / enola / atori)
  - **Recall Priority** 鈥?Vector long-term memories > handwritten daily notes > SOUL base persona
- 馃攧 **Multi-Character Hot-Swap** 鈥?Switch between AI girlfriends (Natsume 鈬?ATRI 鈬?Sakura) with one command; SOUL/IDENTITY/TTS weights/Live2D model all switch automatically, memories isolated per character
- 馃儚 **Character Card Import** 鈥?Auto-detect SillyTavern character cards via `skills/character_importer/`, import 鈫?agent auto-switches role
- 馃挰 **Chat Import** 鈥?Import SillyTavern JSONL chat logs into `memory/role_play/<character>/`, agent restores conversation context on role switch

## Models

All models hosted on HuggingFace: **[TAOTAO777/ai-girlfriend-natsume](https://huggingface.co/TAOTAO777/ai-girlfriend-natsume)**

See [`models.yaml`](models.yaml) for full details.

| Model | Purpose | Size |
|-------|---------|------|
| **Qwen3.6-35B-A3B-APEX-I-Compact** (Q4_K GGUF) | Chat LLM | 16.11 GB |
| **WAI-Nsfw-Illustrious-17** | ComfyUI generation (default) | 6.46 GB |
| **miaomiaoHarem_v20** | ComfyUI generation (backup) | 6.46 GB |
| **GPT-SoVITS voice weights** | TTS voice synthesis | ~303 MB |
| **Sakura SoVITS weights** | TTS (Sakura voice) | ~313 MB |
| **all-MiniLM-L6-v2** | Sentence embedding (mem0 memory) | ~80 MB |
|  | 鈫?Path: `embedding/all-MiniLM-L6-v2/` (HF repo) | |

### One-command Download

```powershell
# Install huggingface-cli: pip install huggingface_hub
huggingface-cli login

# Download all models
huggingface-cli download TAOTAO777/ai-girlfriend-natsume --local-dir ./models

# Or download individual components:
huggingface-cli download TAOTAO777/ai-girlfriend-natsume llm/ --local-dir ./models
huggingface-cli download TAOTAO777/ai-girlfriend-natsume comfyui-checkpoints/ --local-dir ./checkpoints
huggingface-cli download TAOTAO777/ai-girlfriend-natsume gpt-sovits-weights/ --local-dir ./gpt-sovits-weights
```

### Local Configuration

1. **Run `quick_setup.ps1`** 鈥?interactive wizard that generates `config.yaml` with your local paths
2. (Alternative) Copy `config.example.yaml` 鈫?`config.yaml` and edit manually
3. Place downloaded model files according to `models.yaml`, then update `config.yaml` paths

All Python/PS scripts read paths from `config.yaml` 鈥?no hardcoded paths to edit.

> 鈿狅笍 **Disclaimer**: All models are community open-source. This project only provides mirror distribution, non-profit. Copyright belongs to original authors.

## Local LLM Performance

Running Qwen3.6-35B-A3B (MoE, Q4_K, 16.10 GiB, 34.66B params) via llama.cpp (b8851-b9222).

### Launch Command

```powershell
llama-server.exe `
  -m "Qwen3.6-35B-A3B-uncensored-heretic-APEX-I-Compact.gguf" `
  -c 120000 `
  --flash-attn on -ctk q8_0 -ctv q8_0 `
  -ngl 41 --cpu-moe --cpu-mask 0xFFFFFFFF `
  --batch-size 4096 --ubatch-size 2048 --threads 24 `
  --api-key *** -rea off --jinja `
  --cache-ram 2048 --parallel 1 `
  --kv-unified --no-mmap
```

### Key Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| VRAM Usage | ~4.6 GiB (model) + ~1.2 GiB (KV cache) | ~2 GB free on 8 GB VRAM |
| Prefill Speed | **960 ~ 1390 t/s** | 120K context, batch-size 4096 |
| Token Generation | **31 ~ 39 t/s** | MoE architecture, 8/256 experts |
| Context Limit | 120K (~120k tokens) | ~59k token full reprocess in ~55s |
| Model Load Time | ~12s | --no-mmap, requires sufficient RAM |

### Long Context Stability

Qwen3.6 MoE uses SSM (Gated Delta Net) hybrid attention with `--kv-unified`.

鈿狅笍 **Known Limitation**: Cross-turn prompt cache reuse is not supported (SSM architecture limitation). Each request triggers full context re-processing. Longer conversations = higher first-token latency (~55s for 59k tokens).

**Mitigations**:
- Periodic `/reset` (Natsume writes roleplay summaries to `memory/role_play/` before resetting)
- Restore context from summaries on startup, keeping actual token count in 5K鈥?0K range
- `config-patch.json` sets OpenClaw contextWindow to 262144 to match model capacity

### VRAM Budget

```
8 GB Total VRAM
鈹溾攢鈹€ llama-server resident: ~5.8 GB (model 4.6G + KV cache 1.2G)
鈹溾攢鈹€ Free: ~2.2 GB
鈹?
鈹溾攢鈹€ TTS inference: stop llama 鈫?~8 GB free 鈫?resume llama (~70s)
鈹斺攢鈹€ ComfyUI generation: stop llama 鈫?~8 GB free 鈫?resume llama (~120s)
```

## Directory Structure

```
AI_Girlfriend/                        # OpenClaw workspace root
鈹溾攢鈹€ start.ps1                         # 馃殌 One-click launch: llama + Live2D + Gateway
鈹溾攢鈹€ quick_setup.ps1                     # 馃洜 Interactive path config wizard
鈹溾攢鈹€ config.yaml                       # Generated config
鈹溾攢鈹€ download-models.ps1               # One-click model download (Windows)
鈹溾攢鈹€ download-models.sh                # One-click model download (Linux/macOS)
鈹溾攢鈹€ setup-llama.ps1                   # Auto-detect HW + configure llama.cpp (Win)
鈹溾攢鈹€ setup-llama.sh                    # Auto-detect HW + configure llama.cpp (Linux/macOS)
鈹溾攢鈹€ setup-openclaw.ps1                # One-click OpenClaw install + deploy (Win)
鈹溾攢鈹€ setup-openclaw.sh                 # One-click OpenClaw install + deploy (Linux/macOS)
鈹溾攢鈹€ setup-all.ps1                     # 馃殌 All-in-One mega script (Windows)
鈹溾攢鈹€ setup-all.sh                      # 馃殌 All-in-One mega script (Linux/macOS)
鈹溾攢鈹€ config-qqbot.json                 # QQ Bot config patch
鈹溾攢鈹€ config-telegram.json              # Telegram Bot config patch
鈹溾攢鈹€ config-patch.json                 # OpenClaw LLM config patch
鈹溾攢鈹€ AGENTS.md                         # Agent behavior rules
鈹溾攢鈹€ SOUL.md                           # Character personality
鈹溾攢鈹€ IDENTITY.md                       # Character identity
鈹溾攢鈹€ USER.md                           # User info
鈹溾攢鈹€ HEARTBEAT.md                      # Heartbeat config
鈹溾攢鈹€ TOOLS.md                          # Tool quick reference
鈹溾攢鈹€ models.yaml                       # Model catalog + download links
鈹溾攢鈹€ README.md                         # This file
鈹溾攢鈹€ .gitignore
鈹溾攢鈹€ live2d/                           # Live2D character model (Cubism 4 Core)
鈹?  鈹溾攢鈹€ index.html                    # Default (Shiki Natsume)
鈹?  鈹溾攢鈹€ index_atri.html               # ATRI variant
鈹?  鈹溾攢鈹€ index_upper.html              # Natsume upper-body variant
鈹?  鈹溾攢鈹€ index_atri_upper.html         # ATRI upper-body variant
鈹?  鈹溾攢鈹€ live2dcubismcore.min.js       # Cubism Core 4 (207 KB)
鈹?  鈹溾攢鈹€ plid-v5-bundle.js             # pixi-live2d-display v0.5.0 bundle
鈹?  鈹溾攢鈹€ live2d-bridge.mjs             # HTTP (19200) + WebSocket (19201) bridge
鈹?  鈹溾攢鈹€ switch_model.ps1              # Model switcher (natsume / atri)
鈹?  鈹溾攢鈹€ pixi.min.js, pixi-shim.js     # PIXI.js v7 rendering
鈹?  鈹溾攢鈹€ model/shiki_natsume/          # Natsume model (14 textures, 42 motions, 41 sounds)
鈹?  鈹斺攢鈹€ model/atri/                   # ATRI model (2 textures, 620 voice mp3, 8 motions)
鈹溾攢鈹€ ren_pro_jp/                       # Ren'Py dialog engine (planned)
鈹溾攢鈹€ memory/                           # [.gitignore] Runtime memory
鈹?  鈹斺攢鈹€ role_play/                    # Roleplay conversation logs
鈹溾攢鈹€ media/                            # [.gitignore] Generated media
鈹?  鈹溾攢鈹€ audio/                        # TTS voice output
鈹?  鈹溾攢鈹€ images/                       # ComfyUI image output
鈹?  鈹斺攢鈹€ *.gif                         # README demo GIFs
鈹溾攢鈹€ docs/
鈹?  鈹溾攢鈹€ telegram-setup.md             # Telegram Bot setup guide
鈹?  鈹斺攢鈹€ qqbot-setup.md                # QQ Bot setup guide
鈹斺攢鈹€ skills/
    鈹溾攢鈹€ live2d/                       # Live2D control skill
    鈹?  鈹溾攢鈹€ SKILL.md                  # Motion/expression reference + API guide
    鈹?  鈹溾攢鈹€ scripts/start-live2d.ps1  # Live2D launcher
    鈹?  鈹斺攢鈹€ media/                    # Shared media output
    鈹溾攢鈹€ tts/
    鈹?  鈹溾攢鈹€ SKILL.md                  # TTS invocation guide
    鈹?  鈹溾攢鈹€ run_tts.ps1               # TTS launcher script
    鈹?  鈹溾攢鈹€ tts_call.py               # GPT-SoVITS inference
    鈹?  鈹斺攢鈹€ ref_wavs/                 # Reference audio clips
    鈹溾攢鈹€ comfyui/
    鈹?  鈹溾攢鈹€ SKILL.md                  # ComfyUI invocation guide
    鈹?  鈹溾攢鈹€ run_comfyui.ps1           # ComfyUI launcher script
    鈹?  鈹溾攢鈹€ comfyui_call.py           # ComfyUI inference
    鈹?  鈹溾攢鈹€ prompt_template.md        # Character prompt template
    鈹?  鈹斺攢鈹€ custom_prompt.txt         # Custom extra prompt
    鈹溾攢鈹€ asr/                          # Speech recognition skill
    鈹?  鈹溾攢鈹€ run_asr.ps1               # Faster-Whisper launcher (~1.5GB VRAM)
    鈹?  鈹斺攢鈹€ asr_call.py               # Whisper small model inference
    鈹溾攢鈹€ shared/                       # Shared infrastructure
    鈹?  鈹溾攢鈹€ embedding_server.py       # OpenAI-compatible embedding API (port 9999)
    鈹?  鈹溾攢鈹€ mem0_bridge.py            # mem0 Qdrant 鈫?OpenClaw memory bridge
    鈹?  鈹溾攢鈹€ start_embedding_server.ps1 # Auto-start embedding server
    鈹?  鈹溾攢鈹€ llama_lifecycle.py        # Llama start/stop management
    鈹?  鈹斺攢鈹€ llama_utils.py            # Llama utility functions
    鈹溾攢鈹€ sakura/                       # Sakura Desktop Pet (PySide6 GUI)
    鈹?  鈹溾攢鈹€ SKILL.md                  # Sakura skill documentation
    鈹?  鈹溾攢鈹€ main.py                   # Application entry point
    鈹?  鈹溾攢鈹€ install.bat               # Windows dependency installer
    鈹?  鈹溾攢鈹€ start.bat                 # Windows launcher
    鈹?  鈹斺攢鈹€ app/                      # Source code
    鈹溾攢鈹€ llama-management.md           # VRAM management architecture doc
    鈹溾攢鈹€ llama-watchdog.ps1            # Llama health check
    鈹溾攢鈹€ cleanup_orphans.ps1           # Orphan process cleanup
    鈹斺攢鈹€ character_importer/           # SillyTavern character card auto-import
```

## Skills Overview

| Skill | Type | Llama Kill? | Mechanism |
|-------|------|-------------|-----------|
| **Embedding** | Background process | 鉂?No | all-MiniLM-L6-v2 (CPU, 384-dim) on port 9999 鈥?OpenClaw memory search + mem0 bridge |
| **Live2D** | HTTP exec | 鉂?No | Direct HTTP calls to `localhost:19200` bridge |
| **TTS** | sessions_spawn | 鉁?Yes | Kill 鈫?GPT-SoVITS 鈫?restart llama |
| **ComfyUI** | sessions_spawn | 鉁?Yes | Kill 鈫?image gen 鈫?restart llama |
| **ASR** | sessions_spawn | 鉂?No | Faster-Whisper small (~1.5GB VRAM, coexists with llama) |
| **Sakura** | Shared llama-client | 鉂?No | Detects llama down 鈫?waits 鈫?auto-resumes |

## Prerequisites

| Component | Version / Source | Purpose |
|-----------|-----------------|---------|
| [OpenClaw](https://docs.openclaw.ai) | latest | AI Agent Gateway |
| QQ Bot | OpenClaw qqbot channel | QQ message relay |
| Telegram Bot | OpenClaw telegram channel | Telegram message relay |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | b9222 | Local LLM inference server |
| [GPT-SoVITS v2](https://github.com/RVC-Boss/GPT-SoVITS) | v2pro-20250604 | TTS voice synthesis |
| [ComfyUI](https://github.com/comfyanonymous/ComfyUI) | aki-v3 | Image generation engine |
| [Sakura Desktop Pet](https://github.com/Rvosy/Sakura) | v0.9.6-dev | Desktop companion GUI |
| [pixi-live2d-display](https://github.com/guansss/pixi-live2d-display) | v0.5.0 (bundled) | Live2D WebGL renderer |
| Live2D Cubism Core | 4.x (bundled: `live2d/live2dcubismcore.min.js`) | Live2D physics/animation |

> 鉁?**TTS, ComfyUI, and Live2D are fully self-contained.** No external downloads at runtime 鈥?all model weights (`skills/sovits/`, `skills/comfyui_core/`), Python scripts, JS libraries (`live2d/pixi.min.js`, `live2d/plid-v5-bundle.js`), and Cubism Core 4 (`live2d/live2dcubismcore.min.js`) are bundled locally.
>
> 馃 **Headroom token-saving** 鈥?`skills/headroom/` (SmartCrusher + ContentRouter + CCR). Compress large tool outputs in dev scenarios before they hit the context window. See AGENTS.md for API usage.
| Python | 3.12+ | Runtime (Sakura + TTS + ComfyUI) |

## Quick Start

### 馃殌 All-in-One (Recommended)

**One command, from scratch to a fully functional AI girlfriend:**

**Windows:**
```powershell
powershell -File setup-all.ps1
```

**Linux / macOS:**
```bash
bash setup-all.sh
```

Automated pipeline: environment check 鈫?model download 鈫?llama.cpp setup 鈫?OpenClaw install 鈫?Sakura desktop pet 鈫?workspace deploy 鈫?path check 鈫?launch 鈫?verify.

> Supports resume from breakpoint. Flags: `--skip-model-download`, `--skip-llama-setup`, `--skip-openclaw-setup`, `--skip-sakura-setup`, `--dry-run`, `--no-start`

---

### Step-by-Step

### 0. Setup OpenClaw

Install OpenClaw Gateway and deploy the AI Girlfriend workspace:

**Windows:**
```powershell
powershell -File setup-openclaw.ps1
```

**Linux / macOS:**
```bash
bash setup-openclaw.sh
```

This script installs Node.js, OpenClaw Gateway, deploys workspace files, installs daemon, and applies config patch.

> **Flags:** `--skip-node`, `--skip-deploy`, `--skip-daemon`, `--no-onboard`

### 1. Download Models

**Windows:**
```powershell
pip install huggingface_hub
huggingface-cli login
powershell -File download-models.ps1
```

**Linux / macOS:**
```bash
pip install huggingface_hub
huggingface-cli login
bash download-models.sh
```

Downloads all 5 model files (~31.7 GB) from HuggingFace with progress reporting and resume support.

### 2. Setup llama.cpp

Auto-detects GPU, VRAM, CPU cores, RAM and generates optimized launch configs.

**Windows:**
```powershell
powershell -File setup-llama.ps1
```

**Linux / macOS:**
```bash
bash setup-llama.sh
```

### 3. Configure Paths

```powershell
powershell -File quick_setup.ps1
```

Interactive wizard 鈥?enter your local paths once, all scripts are updated automatically.

### 4. Quick Launch

```powershell
# One-click start all services (llama + Embedding + Live2D + Gateway)
powershell -File start.ps1
```

Startup sequence:
```
[1/5] llama-server        (8080, Qwen3.6-35B, ngl=41)
[2/5] Embedding Server    (9999, all-MiniLM-L6-v2, CPU, ~100MB RAM)
[3/5] Live2D Bridge       (19200, pixi-live2d-display)
[4/5] OpenClaw Gateway    (18789)
[5/5] llama-watchdog      (crash auto-restart)
```

**Shutdown: `shiki.cmd -Stop`** 鈥?gracefully stops all services (llama 鈫?live2d 鈫?sakura 鈫?embedding 鈫?comfyui 鈫?gateway 鈫?cleanup).

### 5. Start Live2D Individually

```powershell
# Start the bridge
Start-Process node -ArgumentList "live2d-bridge.mjs" -WorkingDirectory live2d -WindowStyle Hidden

# Open in standalone window (Chrome app mode)
Start-Process chrome -ArgumentList "--new-window --app=http://localhost:19200/index.html --window-size=450,650"
```

Live2D runs in a frameless Chrome window 鈥?place it anywhere on your desktop.

### 5. Windows Task Scheduler (optional)

```powershell
# Llama health check (every 10 min)
schtasks /create /tn "llama-watchdog" `
  /tr "powershell -File C:\Users\<you>\.openclaw\workspace\skills\llama-watchdog.ps1" `
  /sc minute /mo 10

# Orphan process cleanup (hourly)
schtasks /create /tn "cleanup-orphans" `
  /tr "powershell -File C:\Users\<you>\.openclaw\workspace\skills\cleanup_orphans.ps1" `
  /sc hourly /mo 1
```

## Architecture

```
User (QQ / Telegram / WebChat)
  鈹?
  鈻?
OpenClaw Gateway 鈹€鈹€鈹€鈹€ Sakura Desktop Pet (PySide6)
  鈹?                         鈹?
  鈹?                    (Shared llama-client)
  鈹?                         鈹?
  鈻?                         鈻?
  鈹屸攢鈹€鈹€鈹€鈹€ llama-server :8080 鈹€鈹€鈹€鈹€鈹€鈹?   鈹屸攢鈹€鈹€鈹€鈹€鈹€ Memory System 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
  鈹?        (Qwen3.6-35B)        鈹?   鈹?                                                鈹?
  鈹溾攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?   鈹? 鈹屸攢 Embedding :9999 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹?
  鈹? Main session (roleplay)     鈹?   鈹? 鈹? all-MiniLM-L6-v2 (CPU, ~100MB RAM)       鈹?鈹?
  鈹? TTS (kill 鈫?GPU 鈫?restart)  鈹?   鈹? 鈹? 鈹溾攢 OpenClaw memory_search (hybrid)       鈹?鈹?
  鈹? ComfyUI (kill 鈫?GPU 鈫?restart)鈹? 鈹? 鈹? 鈹斺攢 mem0_bridge.py (search / add / sync) 鈹?鈹?
  鈹? ASR (Whisper 鈫?no kill)     鈹?   鈹? 鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹?
  鈹? Sakura Pet (shared, no kill)鈹?   鈹?                                                鈹?
  鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?   鈹? 鈹屸攢 Qdrant Vector DB 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹?
               鈹?                     鈹? 鈹? collection: sakura_memories               鈹?鈹?
               鈹?                     鈹? 鈹? 鈹溾攢 user_id=sakura   (澶滀箖妗?              鈹?鈹?
               鈻?                     鈹? 鈹? 鈹溾攢 user_id=natsume  (澶忕洰)                鈹?鈹?
     Live2D Bridge (:19200) 鈹€鈹€鈹€ Browser鈹? 鈹? 鈹溾攢 user_id=enola    (Enola)               鈹?鈹?
          (HTTP 鈫?no kill)         (L2D鈹? 鈹? 鈹斺攢 user_id=atori    (Atori)               鈹?鈹?
                                   /Por鈹? 鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹?
                                   trait鈹?                                               鈹?
                                        鈹? 鈹屸攢 CCR (Curate-Consolidate-Retrieve) 鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹?
                                        鈹? 鈹? Every 8 turns 鈫?extract memories         鈹?鈹?
                                        鈹? 鈹? 鈫?mem0 Qdrant (long-term vector)         鈹?鈹?
                                        鈹? 鈹? 鈫?_mem0_auto.md (markdown, searchable)   鈹?鈹?
                                        鈹? 鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹?
                                        鈹?                                                鈹?
                                        鈹? 鈹屸攢 SmartCrusher 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹?
                                        鈹? 鈹? 24 msg / 40K char cap per LLM request     鈹?鈹?
                                        鈹? 鈹? context_trimming.py (all characters share)鈹?鈹?
                                        鈹? 鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?鈹?
                                        鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
```

**Agent Hub 鈥?Immutable Capability Instructions + Memory Layers**:

```
         鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
         鈹? AGENTS.md   鈹? 鈫?Capability hub (never changes on role switch)
         鈹? SOUL.md     鈹? 鈫?Current character persona (hot-swappable)
         鈹? IDENTITY.md 鈹? 鈫?Character metadata
         鈹? TOOLS.md    鈹? 鈫?Quick reference
         鈹? USER.md     鈹? 鈫?User profile
         鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                鈹?
    鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹粹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
    鈻?                       鈻?                        鈻?
 鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?  鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?  鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
 鈹?skills/harem/ 鈹?  鈹?memory/role_play/    鈹?  鈹?Qdrant Vector DB鈹?
 鈹?  (瀛樻。鍚庡)  鈹?  鈹?  <瑙掕壊>/ (鐙珛璁板繂)   鈹?  鈹?(闀挎湡鍚戦噺璁板繂)    鈹?
 鈹?鈹溾攢 natsume/   鈹?  鈹?鈹溾攢 natsume/          鈹?  鈹?user_id=natsume 鈹?
 鈹?鈹溾攢 enola/     鈹?  鈹?鈹? 鈹溾攢 YYYY-MM-DD.md  鈹?  鈹?user_id=enola   鈹?
 鈹?鈹溾攢 sakura/    鈹?  鈹?鈹? 鈹斺攢 _mem0_auto.md  鈹?  鈹?user_id=sakura  鈹?
 鈹?鈹斺攢 atori/     鈹?  鈹?鈹溾攢 enola/...         鈹?  鈹?user_id=atori   鈹?
 鈹?  (瑙掕壊鍗″瓨妗?  鈹?  鈹?鈹溾攢 sakura/...        鈹?  鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
 鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?  鈹?鈹斺攢 atori/...          鈹?        鈫?
                    鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?  CCR + mem0_bridge
                          鈫?                   (瀹氭椂鍚屾 30min)
                    OpenClaw memory_search
                    (hybrid: vector + BM25)
```

- `AGENTS.md` stays constant across role switches 鈥?ComfyUI / TTS / Live2D + Memory instructions are preserved
- `SOUL.md` + `IDENTITY.md` are overwritten on switch; harem archives source of truth
- Memory per character isolated in `memory/role_play/<name>/` 鈥?never cross-contaminated
- Long-term vector memories in Qdrant, scoped by `user_id` per character
- SillyTavern character cards imported via PNG tEXt chunk parsing 鈫?auto-switch agent persona

**Six Skills, One Memory System**:

| Skill | Location | Llama Interaction |
|-------|----------|-------------------|
| **Embedding** | `skills/shared/` | all-MiniLM-L6-v2 (CPU, ~100MB RAM) on port 9999 鈥?never touches GPU |
| **Live2D** | `skills/live2d/` | HTTP API only 鈥?never touches llama |
| **TTS** | `skills/tts/` | Kill llama 鈫?GPT-SoVITS 鈫?restart + wait /health |
| **ComfyUI** | `skills/comfyui/` | Kill llama 鈫?image gen 鈫?restart + wait /health |
| **ASR** | `skills/asr/` | Faster-Whisper small 鈥?coexists with llama on 8GB |
| **Sakura** | `skills/sakura/` | Shared llama-client; detects down 鈫?auto-resume; built-in CCR + mem0 |
| **SmartCrusher** | `skills/shared/context_trimming.py` | 24 msg / 40K char cap per LLM request 鈥?all characters share |
| **CCR** | `skills/sakura/app/agent/memory_curator.py` | Background: extracts facts every 8 turns 鈫?Qdrant |
| **mem0 Bridge** | `skills/shared/mem0_bridge.py` | CLI: search / add / list / sync per character |
| **Auto-Sync** | `skills/shared/mem0_sync_cron.py` | Cron job every 30 min: Qdrant 鈫?`_mem0_auto.md` |
| **Character Importer** | `skills/character_importer/` | Agent-level 鈥?no GPU needed; writes SOUL/IDENTITY + memory dir |

**VRAM Orchestration Flow**:
1. Main session receives user request 鈫?assembles command
2. `sessions_spawn(mode="run")` creates local model sub-session
3. Sub-session execs PS script 鈫?`stop_llama()` kills llama-server
4. Full 8 GB VRAM freed 鈫?TTS/ComfyUI inference
5. `start_llama()` restarts llama-server (~12s load + ~3s warmup)
6. Live2D remains active during entire cycle 鈥?bridge doesn't touch GPU
7. Sub-session writes `.task_flags` 鈫?announces back to main session
8. Main session reads media files 鈫?sends via `<qqmedia>` / `MEDIA:`
9. Background: CCR runs every ~8 turns, extracting long-term memories to Qdrant
10. Cron job syncs Qdrant 鈫?`_mem0_auto.md` every 30 min for native `memory_search`

## 鈿狅笍 Important Notes

- **RTX 50xx (Blackwell) + CUDA 13.x = `munmap_chunk(): invalid pointer` crash** 鈥?CUDA 13.x has known memory management incompatibility with llama.cpp on Blackwell GPUs. **Solution: use pre-built llama.cpp binaries compiled with CUDA 12.x** (not self-compiled with CUDA 13.x). Download from [llama.cpp Releases](https://github.com/ggml-org/llama.cpp/releases), choose `cudart-llama-bin-win-cuda-12.4-x64.zip`. RTX 5070 Ti is fully compatible with CUDA 12.x drivers.
- Llama-server is offline for ~60鈥?20s during TTS/ComfyUI inference 鈥?conversation pauses, but Live2D keeps running
- Sub-sessions use **local model** (same as main), DeepSeek as optional fallback
- Llama-server does not support cross-turn prompt cache reuse (SSM limitation) 鈥?use periodic `/reset`
- **Live2D requires Cubism Core 4** (not 5 or 6) 鈥?pixi-live2d-display v0.5.0 is built for Cubism 4 Framework; Core 5+ causes clipping/layer failures. **Core 4 is bundled** in live2d/live2dcubismcore.min.js — no CDN needed.
- All model files protected by `.gitignore`
- GPT-SoVITS weights are self-trained and not distributed 鈥?train with your own voice data

## 馃檹 Credits

- [@Rvosy](https://github.com/Rvosy) 鈥?Creator of [Sakura Desktop Pet](https://github.com/Rvosy/Sakura), authorized for inclusion (Issue #38)
- [@guansss](https://github.com/guansss) 鈥?Creator of [pixi-live2d-display](https://github.com/guansss/pixi-live2d-display)
- [Live2D Inc.](https://www.live2d.com) 鈥?Cubism SDK (non-commercial use)
- [headroom](https://github.com/chopratejas/headroom) 鈥?Inspiration for SmartCrusher context compression + CCR (Curate-Consolidate-Retrieve) memory pipeline
- [mem0](https://github.com/mem0ai/mem0) 鈥?Inspiration for Qdrant vector memory architecture + hybrid search design
