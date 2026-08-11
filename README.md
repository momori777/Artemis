<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>AI Girlfriend</title>
  <meta http-equiv="refresh" content="0;url=README.html">
</head>
<body>
  <p>If you are not redirected, <a href="README.html">click here</a>.</p>
  <p><a href="README_CN.md">中文</a> · <a href="README_jp.md">日本語</a></p>
</body>
</html>





































































































































































































































































































































































































































































































































































































































































































n

# AI Girlfriend

**100% Local · Fully Private · Zero API Dependencies**

> All conversations, voice, images, and character animations are generated on your own machine. No cloud servers, no third-party APIs, no risk of data leakage. Your AI girlfriend belongs to you, and only you.

-

An uncensored AI girlfriend harem project powered by OpenClaw + QQ Bot + Telegram Bot + llama.cpp + GPT-SoVITS + ComfyUI + Sakura Desktop Pet + Live2D -running entirely on your own machine.

**Characters**: Supports hot-swappable AI girlfriends with isolated memories per character.

### Shiki Natsume (四季夏目)

From *Starry Moonlit Café & the Butterfly of Death*. Tall, aloof, cool exterior with a hidden warmth. A natural quietly-dominant type -she takes the lead, teases you gently, and guards you fiercely. Speaks little, but every word hits.

### ATRI (亚托莉)

From *ATRI -My Dear Moments-*. Petite, innocent, endlessly curious -a bright-eyed girl who wears her heart on her sleeve. Runs toward the future with a smile, dragging you along. **The polar opposite of Natsume**: bubbly and expressive where Natsume is reserved, emotionally transparent where Natsume is guarded, playful where Natsume is composed. If Natsume is the cool winter night, ATRI is the warm summer sun.

### Yono Sakura (夜乃桜)

From *Dimension W Lovers!!*. Former student council president and the academy's strongest anti-kaiju combatant. Silver-white hair with pink tips, pale blue eyes -cool-headed, restrained, and fiercely responsible. She's not good at smooth words or easy smiles; her care is direct and clumsy, like a command: rest, eat, don't push yourself. In desktop pet form, she's learning that she doesn't have to bear everything alone -that protecting someone's ordinary everyday life from this side of the screen is enough. **A quiet guardian**: silent but watchful, loyal but stubborn, the senpai who stays by your side without being asked.


## ✨ Why Choose This Project?

| | Cloud AI Girlfriend | This Project |
|-|-|-|
| 🛡️ **Privacy** | Chat logs, voice, and images all stored on vendor servers | **Everything stays local** -zero data leaves your machine |
| 💰 **Cost** | Monthly subscriptions / per-token billing adds up | **Free**, one-time setup, runs forever (bring your own hardware) |
| 🌐 **Network** | Needs internet; dead if servers go down | **Works offline** -flip off your WiFi and keep chatting |
| 🎛️ **Control** | Prompts/templates controlled by vendor, can change anytime | **You control** all models, parameters, and character settings |
| 🔞 **Content** | Heavy censorship, accounts get banned | **No censorship** -talk about whatever you want |
| 🎨 **Extensibility** | Locked into vendor models and features | **Mix and match** -swap LLMs, image models, voice models freely |

## 📌 Prerequisites

> **⚠️ First step: Run `quick_setup.ps1` to configure paths and language.**
>
> This wizard will:
> 1. **Let you choose the default Agent language** (Chinese / Japanese / English) - copies the corresponding `AGENTS_*.md` to `DEFAULT_AGENT.md`
> 2. Auto-detect your installed tools (ComfyUI, GPT-SoVITS, llama.cpp, embedding models)
> 3. Prompt you for any paths it can't find
> 4. Generate `config.yaml` with all paths, ready for `download-models.ps1`
>
> ```powershell
> powershell -ExecutionPolicy Bypass -File quick_setup.ps1
> ```
>
> After quick_setup completes, proceed with **download-models.ps1** → **setup-llama.ps1** → **start.ps1**.

## 🎬 Demo

### Multi-Channel Chat
![QQ Bot Demo](media/demo_qqbot.gif)

> 👆 QQ Bot: text chat + TTS voice + ComfyUI image generation + character memory

### Live2D Desktop Pet
![Live2D Demo](media/demo_live2d.gif)

> 👆 **Shiki Natsume** Live2D: real-time character animation with emotion-driven motions, lip-sync, and speech bubbles. Controlled via local HTTP bridge.

### ⭐ ATRI - Second AI Girlfriend

**Personality opposite of Natsume**, hot-swappable with isolated memory.

![ATRI Live2D](media/atri_live2d.gif)

> 👆 **ATRI** Live2D: silver hair, ruby-red eyes, barefoot in a white dress -innocent and expressive.

![ATRI ComfyUI](media/atri_comfyui.gif)

> 👆 **ATRI** ComfyUI: AI image generation -seaside sunset, flowing white dress, warm golden-hour lighting.

### ⭐Yono Sakura -Third AI Girlfriend

**Cool-headed guardian senpai**, student council president and academy's strongest combatant -now your desktop companion.

![Sakura Desktop Pet](media/sakura_demo.gif)

> 👆 **Yono Sakura** Desktop Pet: silver-pink gradient hair, pale blue eyes, school uniform -reactive portrait expressions, proactive care reminders, and real-time TTS voice via GPT-SoVITS.

### 🌐 Web Chat Frontend

![Web Chat Demo](media/webchat-demo.gif)

> 👆 **Web Chat**: browser-based chat interface at `http://127.0.0.1:19270` - an alternative to QQ/Telegram bots. Connects directly to local daemon proxy → llama.cpp server. 8 GB VRAM can run fully without stopping.

### 🎙️ TTS Voice

🔊 **Listen** (click to play, ATRI Japanese):

🎧 [tts_atori.mp3](media/tts_atori.mp3) *(46KB, plays in browser)*

### 🎨 ComfyUI Image Workshop

<video src="media/comfyui_workshop_small.mp4" controls width="800"></video>

![ComfyUI Workshop](media/comfyui_workshop.gif)

> 👆 **Artemis Studio - ComfyUI Workshop**: Visual AI image generation console - freely choose character/outfit/scene/art style, one-click generation. **Runs in parallel with llama** (12GB+ VRAM).

| Feature | Description |
|-|-|
| 🎭 **Dynamic Characters** | Auto-loads from `skills/harem/`, displays persona + tags + greeting per character |
| 🔄 **Character Hot-Swap** | One-click switch from sidebar dropdown, memories and chat context preserved per character |
| 🃏 **Card Import** | Drag-drop or select SillyTavern PNG/JSON character cards, auto-parses metadata and persona |
| 🤖 **Model Selector** | Choose local llama / DeepSeek / Grok from Settings dropdown, routes through daemon proxy |
| 💬 **Real LLM Chat** | Streaming replies via daemon `/api/chat` → llama.cpp `/v1/chat/completions`, no fake fallbacks |
| 📱 **Responsive** | Mobile sidebar collapse, adaptive bubble layout, works on desktop and tablet |
| 💾 **Local Storage** | Multi-session chat history, settings, and character state persisted in browser localStorage |
| 🎛️ **Artemis Studio** | Built-in TTS + ComfyUI placeholder panel (voice/image generation controlled via agent subprocesses) |

## Hardware

| Component | Model |
|-|-|
| GPU | NVIDIA GeForce RTX 5070 Laptop (8 GB VRAM) |
| CPU | Intel Core i9-14900HX (24 cores, 32 threads) |
| RAM | 32 GB DDR5 |
| OS | Windows 11 |


## 🔮 Future: Cosmos World Foundation Model

> 📖 Full design: [`imagination.md`](imagination.md) | Bridge ref: [`skills/cosmos/BRIDGE_REFERENCE.md`](skills/cosmos/BRIDGE_REFERENCE.md)

**NVIDIA Cosmos** (community FP8 quant archived at `skills/cosmos/`) is a World Foundation Model that generates physics-consistent scene videos and understands spatial relationships.

### Why Cosmos?

The four core capabilities (LLM + TTS + ComfyUI + Live2D) are currently **disconnected** - the LLM doesn't know what Live2D is doing, ComfyUI doesn't sense conversational emotion. Cosmos fills the **physical common-sense layer**:

```
Qwen3.6-35B (Language Mind) ←→ Cosmos 3 Nano (Physical Mind)
   Language + Emotion             Spatial + Scene Generation
```

### Dual Compact Architecture

| Component | Model | Params | VRAM |
|-----------|-------|--------|------|
| 🧠 Language Mind | Qwen3.6-35B-A3B (MoE) | 35B total / 3B active | ~8 GB |
| 🌍 Physical Mind | Cosmos 3 Nano FP8 | 15.75B | ~16 GB |

### Hardware Roadmap

| Year | GPU | Cosmos Status |
|------|-----|---------------|
| 2026 | RTX 5070 (8-12GB) | ❌ Archived, detection ready |
| 2027-28 | RTX 5090 (32GB) | ⚠️ Nano FP8 inference feasible |
| 2029-30 | Rubin Workstation (96GB) | ✅ LLM + Cosmos co-resident |

### Current Status

- ✅ Repo archived at `skills/cosmos/`
- ✅ Bridge design `imagination.md` + `cosmos_check.py` ready
- ✅ Qwen ↔ Cosmos dual-mind architecture designed
- 📋 Waiting for ~24GB+ VRAM hardware


## Features


- 🔄 **Multi-Character Hot-Swap** - One-click switch between AI girlfriends (Natsume ⇄ ATRI ⇄ Sakura); SOUL/IDENTITY/TTS weights/Live2D model all switch automatically, memories isolated per character
- 🃏 **SillyTavern Character Card Import** - Auto-detect and import PNG/JSON character cards; agent auto-switches persona on import
- 💬 **Chat Log Import** - Import SillyTavern JSONL conversation logs into `memory/role_play/<character>/`; agent restores context on role switch
- 🎤 **TTS Voice Synthesis** -Local GPT-SoVITS inference, Japanese voice (emotion-matched per dialogue), 3 character voice models (Natsume / ATRI / Sakura)
- 🎤 **ASR Speech Recognition** -Local Faster-Whisper small model (~1.5GB VRAM), coexists with llama; 99-language support
- 🎨 **AI Image Generation** -Local ComfyUI inference, SDXL/Illustrious models, 3 character prompt templates
- 🖥️**Sakura Desktop Pet** -PySide6 desktop companion with proactive care, screen observation & local LLM awareness; supports 3 characters
- 🎭 **Live2D Character Model** -Real-time Live2D rendering with emotion-driven expressions & speech bubbles (Natsume / ATRI L2D; Sakura portrait mode)
- 🧠 **Smart VRAM Tiering** - Auto-detects GPU VRAM and picks the right strategy: ≥12GB keeps everything online (llama + skills); 8GB hot-swaps llama for GPU-heavy tasks; <8GB safe mode. Zero manual config
- 🎛️ **Artemis Studio Console** - Visual TTS + ComfyUI workshop, DIY voice & images anytime regardless of llama status - a true offline creative suite
- 💾 **Roleplay Memory** -Daily conversation summaries per character in `memory/role_play/`
- 🧠 **Long-term Memory System** -Powered by [headroom](https://github.com/chopratejas/headroom) (SmartCrusher + CCR) and [mem0](https://github.com/mem0ai/mem0) (Qdrant vector database):
  - **Chinese Embedding Boost** - Added BGE-small-zh-v1.5 alongside all-MiniLM-L6-v2 for more accurate CN/JP/EN hybrid memory retrieval
  - **SmartCrusher Context Trimming** -Hard-caps chat history at 24 messages / 40K characters per LLM request
  - **CCR (Curate-Consolidate-Retrieve)** -Background worker extracts durable facts every 8 turns, writes to mem0 Qdrant
  - **Vector + BM25 Hybrid Search** -Semantic similarity + keyword matching via Qdrant + dual embedding models
  - **Auto-Sync Bridge** -Cron job syncs Qdrant →`_mem0_auto.md` every 30 min, making vector memories searchable by OpenClaw's native `memory_search`
  - **Per-Character Isolation** -`user_id` scoping in Qdrant; 4 independent memory spaces (sakura / natsume / enola / atori)
  - **Recall Priority** -Vector long-term memories > handwritten daily notes > SOUL base persona

> See [`skills/behavior-engine/README.md`](skills/behavior-engine/README.md) and [`AGENTS_roleplay_EN.md#behavior-engine`](AGENTS_roleplay_EN.md#behavior-engine).

### 💖 Relationship System (Behavior Engine)

A **layered decision engine** ported from the sister-project **girl-agent**, giving each character an independent relationship score, conflict state, relationship stage, and hormonal cycle that drive their behavior and reply style.

**Core loop:** each turn produces a moodDelta (interest/trust/attraction/annoyance/cringe) → accumulated into the score → triggers conflict escalation/cool-down → auto-checks relationship stage transitions → shapes the LLM's reply style.

| Field | Range | Meaning | Effect |
|-------|-------|---------|--------|
| `score.interest` | -100~100 | Interest | Reply warmth, initiative |
| `score.trust` | -100~100 | Trust | Sharing, dependence |
| `score.attraction` | -100~100 | Attraction | Heart-racing, body language |
| `score.annoyance` | -100~100 | Annoyance | Cold tone, conflict chance |
| `score.cringe` | -100~100 | Cringe tolerance | Acceptance of cheesy lines |

**9 relationship stages:** first meet → cold period → warming up → convinced → first date → early dating → stable dating → long-term → dumped

**4-level conflict system:** level 0 normal → level 1 slight sulk → level 2 in a huff → level 3 severe cold war → level 4 blocked/deleted

**Hormonal cycle:** a Gaussian cycle model simulates periodic swings in energy, irritability, affection, and libido, influencing reply length and tone.

**State file:** `memory/role_play/<char>/relationship.json` (independent per character, hot-loaded)
**Module location:** `skills/behavior-engine/`
- 🔄 **Multi-Character Hot-Swap** - One-command AI girlfriend switch (Natsume ⇄ ATRI ⇄ Sakura); SOUL/IDENTITY/TTS weights/Live2D model auto-switch, memory isolated
- 🃏 **Character Card Import** - Auto-detect and import SillyTavern character cards via `skills/character_importer/`; agent auto-switches role
- 💬 **Chat Import** - Import SillyTavern JSONL chat logs into `memory/role_play/<character>/`; agent restores context on role switch

## Models

All models hosted on HuggingFace: **[TAOTAO777/ai-girlfriend-natsume](https://huggingface.co/TAOTAO777/ai-girlfriend-natsume)**

See [`models.yaml`](models.yaml) for full details.

| Model | Purpose | Size |
|-|-|-|
| **LuffyTheFox Qwen3.6-35B-A3B Genesis Hermes V7 MTP APEX Compact** (GGUF) | Chat LLM (primary MoE) | 16.11 GB |
| **Qwen3.6-27B-Fable-MTP** (Q4_K_S GGUF) | Chat LLM (secondary dense) | 13.5 GB |
| **WAI-Nsfw-Illustrious-17** | ComfyUI generation (default) | 6.46 GB |
| **miaomiaoHarem_v20** | ComfyUI generation (backup) | 6.46 GB |
| **GPT-SoVITS voice weights** | TTS voice synthesis | ~303 MB |
| **Sakura SoVITS weights** | TTS voice synthesis (Sakura voice) | ~313 MB |
| **all-MiniLM-L6-v2** | English/cross-lingual embedding (mem0) | ~80 MB |
| **BGE-small-zh-v1.5** | Chinese embedding (mem0) | ~91 MB |
| **Cosmos 3 Nano FP8** 🔮 | World Foundation Model (community FP8 quant, future HW) | ~16 GB |

|  | →Path: `embedding/all-MiniLM-L6-v2/` + `embedding/bge-small-zh-v1.5/` (HF repo) | |
| **Shiki Natsume Live2D Model** | Live2D character rendering | ~180 MB (archive) |

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
huggingface-cli download TAOTAO777/ai-girlfriend-natsume live2d-model/ --local-dir ./live2d-model
```

> 🇨🇳 Users in China: use hf-mirror.com - no VPN needed:
> `set HF_ENDPOINT=https://hf-mirror.com` then run hf download as usual.

### Local Configuration

1. **Run `quick_setup.ps1`** -interactive wizard that generates `config.yaml` with your local paths
2. (Alternative) Copy `config.example.yaml` →`config.yaml` and edit manually
3. Place downloaded model files according to `models.yaml`, then update `config.yaml` paths

All Python/PS scripts read paths from `config.yaml` -no hardcoded paths to edit.

> ⚠️ **Disclaimer**: All models are community open-source. This project only provides mirror distribution, non-profit. Copyright belongs to original authors.

## Local LLM Performance

Running Qwen3.6-35B-A3B-MTP (Genesis Hermes V7 MTP APEX Compact, MoE, 16.11 GiB, 34.66B params) via llama.cpp with speculative MTP (Multi-Token Prediction) decoding.

### Launch Command

```powershell
llama-server.exe `
  -m "Hermes3.6-35B-A3B-Uncensored-Genesis-V7-MTP-APEX-Compact.gguf" `
  -c 150000 `
  --flash-attn on -ctk q4_0 -ctv q4_0 `
  --cpu-moe --cpu-mask 0xFFFFFFFF `
  --batch-size 4096 --ubatch-size 2048 `
  -rea off --jinja `
  --cache-ram 3000 --parallel 1 `
  --kv-unified --no-mmap `
  --spec-type draft-mtp --spec-draft-n-max 2
```

> 💡 **About `--no-mmap` vs `-ngl`:** `--no-mmap` lets llama.cpp manage memory on its own, which is far more efficient than manually specifying layers with `-ngl`. Forcing GPU layers via `-ngl` can cut speed in half; `--no-mmap` allows the engine to dynamically allocate based on actual VRAM. Using `q4_0` for KV cache halves VRAM usage - at 16K context, q4 runs stably for 50K+ tokens.

MTP (Multi-Token Prediction) uses a draft head that predicts 2 future tokens at each step on CPU, then the main model verifies them on GPU. Acceptance rate ~71%, yielding ~48 tok/s effective output.

### Key Metrics (35B MoE)

| Metric | Value | Notes |
|-|-|-|
| VRAM Usage | ~4.6 GiB (model) + ~1.4 GiB (KV cache) | ~2 GB free on 8 GB VRAM |
| Prefill Speed | **28 ~ 156 t/s** | Varies with prompt length |
| Token Generation | **48 tok/s avg** | MTP accepted ~71% (draft=2) |
| Context Limit | 120K (~120k tokens) | Full reprocess ~55s at 59k |
| Model Load Time | ~12s | --no-mmap, requires sufficient RAM |

### Silicon Rider Bench (Agent Benchmark)

**[Silicon Rider Bench](https://github.com/kcores/silicon-rider-bench)** is an agent benchmark that simulates a food-delivery rider working a virtual city: navigate, accept orders, pick up food, deliver on time, and manage battery — scoring total profit over a simulated 24-hour day. Same seed (**622539**) used across all runs for apples-to-apples comparison.

This is a **pure black-box agent test**: the model decides every move itself via tool calls (search → accept → plan route → move → pickup → deliver → swap battery), with no external assistance. The prompt includes two house rules: remember already-calculated routes (route reuse) and **mandatory charging path plan when battery < 30%**.

**Models under test** (all `--seed 622539`):
- **deepseek-v4-flash (0731)** — remote, unlimited-context baseline. Cloud-class agent ability (~Claude 4.6–4.8 tier in this benchmark).
- **Hermes3.6-35B-A3B-Uncensored-Genesis-V7-MTP-APEX-Compact.gguf** — RTX5070 LAPTOP, 8G VRAM, 32G D5 RAM,

#### Results (Seed 622539, Level 1, 24 game-hours)

| Metric | deepseek-v4-flash<br>(unlimited ctx) | Hermes 35B MoE<br>(25 ctx) | **Hermes 35B MoE<br>(100 ctx)** ✅ |
|-|-|-|-|
| **Profit ¥** | **619.6** | 411.3 | **524.6** |
| Orders completed | **33** | 30 | 28 |
| **On-time rate** | **81.8%** | 56.7% | **75.0%** |
| Route efficiency | **1.34** | 1.77 | 1.68 |
| API violation rate | **1.3%** | 2.3% | 2.2% |
| Profit / order ¥ | **18.77** | 13.71 | **18.74** |
| Overtime penalty ¥ | **2.75** | 107.9 | 44.7 |
| Total tokens | 24.39M | 1.35M | 4.08M |
| Token efficiency ¥/M | 25.4 | 304.6 | **128.6** |

#### Key Takeaways

- **Context length is the #1 lever**: raising `CONTEXT_HISTORY_LIMIT` 25 → 100 lifted on-time rate **56.7% → 75%** and slashed overtime penalty **¥107.9 → ¥44.7**, pushing profit **¥411 → ¥525** (the model finally retains order deadlines + routes across turns).
- **Local 35B MoE ≈ 85% of cloud flash**: at 100 ctx the local quantized 35B hits **¥524.6 = 84.6% of dsv4-flash's ¥619.6**, with on-time rate (75% vs 81.8%) and per-order profit (¥18.74 vs ¥18.77) essentially tied.
- **6× cheaper**: flash burned **24.39M tokens** (unlimited ctx); local 100-ctx used only **4.08M** for 5/6 of the profit → **5× better token efficiency**, at zero API cost.
- **Remaining gap**: route efficiency (1.68 vs 1.34) — the 35B-A3B's 3B active params still underperform flash on multi-leg optimal route planning.

**Verdict: after quantization fine-tuning, the Hermes3.6-tuned Qwen3.6 35B's agentic ability is essentially on par with Claude Opus 4.6!**

> 🧪 Full logs & reports in `docs/silicon-rider-bench-622539/` (COMPARISON-622539.md + per-run summaries).

### Long Context Stability

Qwen3.6 MoE uses SSM (Gated Delta Net) hybrid attention with `--kv-unified`.

⚠️ **Known Limitation**: Cross-turn prompt cache reuse is not supported (SSM architecture limitation). Each request triggers full context re-processing. Longer conversations = higher first-token latency (~55s for 59k tokens).

**Mitigations**:
- Periodic `/reset` (Natsume writes roleplay summaries to `memory/role_play/` before resetting)
- Restore context from summaries on startup, keeping actual token count in 5K-20K range
- `config-patch.json` sets OpenClaw contextWindow to 262144 to match model capacity

---

## Qwen3.6-27B-Fable-MTP (Dense, Alt Model)

Secondary dense model for tasks where full 27B parameter activation is preferred. Runs via llama.cpp with MTP speculative decoding.

### Launch Command

```powershell
llama-server.exe `
  -m "Qwen3.6-27B-Fable-MTP-Q4_K_S.gguf" `
  -c 150000 `
  --flash-attn on -ctk q4_0 -ctv q4_0 `
  --batch-size 4096 --ubatch-size 2048 `
  -rea off --jinja `
  --parallel 1 --kv-unified --no-mmap `
  --spec-type draft-mtp --spec-draft-n-max 1
```

> ⚠️ **Dense model on 8GB VRAM**: 27B Q4_K_S ≈ 14 GB, far exceeding 8 GB VRAM. Most layers run on CPU while attention etc. runs on GPU. This is the **main bottleneck**; expect much lower generation speed than the MoE variant.

### Key Metrics (27B Dense)

| Metric | Value | Notes |
|-|-|-|
| VRAM Usage | ~5.8 GiB model + KV | Cannot fully offload; constrained by 8 GB |
| Prefill Speed | **~156 t/s** | Prompt processing on GPU |
| Token Generation | **~3.8 tok/s** | Dense 27B, CPU-heavy, MTP ~84% accept |
| MTP Acceptance | 84.1% (draft=1) | Higher rate due to simpler draft head |
| Context Limit | 150K | Full KV on GPU/CPU hybrid |

> 💡 **MoE vs Dense**: The 35B MoE activates only ~3B parameters per token (8/256 experts) and fits GPU well, hitting 48 tok/s. The 27B dense activates all 27B and exceeds VRAM, bottlenecked to 3.8 tok/s. For this hardware (RTX 5070 8GB), **the 35B MoE is strongly recommended** as primary.

### VRAM Tiering Strategy

The system auto-detects GPU VRAM and selects the optimal run mode, no manual config:

```
┌────────────────────────────────────────────────────────────┐
│ VRAM Tier               │ TTS       │ ComfyUI   │ llama   │  tts  │
├────────────────────────────────────────────────────────────┤
│ Tier 0: <8GB            │ Stop llama │ Stop llama│ Killed  │ Killed │
│ Tier 1: 8-12GB (current) │ Stop llama │ Stop llama│ Killed  │  No kill │
│ Tier 2: ≥12GB           │ No kill    │ No kill   │ Always on │  No kill │
└────────────────────────────────────────────────────────────┘
```

**Current setup (8GB VRAM)**:
```
8 GB Total VRAM
├── llama-server resident: ~5.8 GB (model 4.6G + KV cache 1.2G)
├── Free: ~2.2 GB
│
├── TTS inference: stop llama → ~8 GB free → resume llama (~70s)
├── ComfyUI generation: stop llama → ~8 GB free → resume llama (~120s)
├── Artemis Studio (TTS/ComfyUI workshop): standalone - works regardless of llama
└── ASR / Live2D / Embedding: always online, unaffected by VRAM tiering
```

## Directory Structure

```
<PROJECT_DIR>/                                               # OpenClaw workspace root
├── start.ps1                         # 🚀 One-click launch: llama + headroom + Live2D + Gateway
├── artemis_headroom_proxy.py          # Headroom proxy (19251): mem0 injection + SmartCrusher + routing
├── shiki_daemon.py                    # Daemon (19260/19270): WebChat backend + auto-inject provider
├── quick_setup.ps1                     # 🛠 Interactive path config wizard
├── config.yaml                       # Generated config
├── download-models.ps1               # One-click model download (Windows)
├── download-models.sh                # One-click model download (Linux/macOS)
├── setup-llama.ps1                   # Auto-detect HW + configure llama.cpp (Win)
├── setup-llama.sh                    # Auto-detect HW + configure llama.cpp (Linux/macOS)
├── setup-openclaw.ps1                # One-click OpenClaw install + deploy (Win)
├── setup-openclaw.sh                 # One-click OpenClaw install + deploy (Linux/macOS)
├── setup-all.ps1                     # 🚀 All-in-One mega script (Windows)
├── setup-all.sh                      # 🚀 All-in-One mega script (Linux/macOS)
├── config-qqbot.json                 # QQ Bot config patch
├── config-telegram.json              # Telegram Bot config patch
├── config-patch.json                 # OpenClaw LLM config patch
├── AGENTS.md                         # Agent behavior rules
├── SOUL.md                           # Character personality
├── IDENTITY.md                       # Character identity
├── USER.md                           # User info
├── HEARTBEAT.md                      # Heartbeat config
├── TOOLS.md                          # Tool quick reference
├── models.yaml                       # Model catalog + download links
├── imagination.md                    # 🔮 Cosmos WFM integration vision (future)
├── README.md                         # This file
├── .gitignore
├── live2d/                           # Live2D character model (Cubism 4 Core)
│   ├── index.html                    # Default (Shiki Natsume)
│   ├── index_atri.html               # ATRI variant
│   ├── index_upper.html              # Natsume upper-body variant
│   ├── index_atri_upper.html         # ATRI upper-body variant
│   ├── live2dcubismcore.min.js       # Cubism Core 4 (207 KB)
│   ├── plid-v5-bundle.js             # pixi-live2d-display v0.5.0 bundle
│   ├── live2d-bridge.mjs             # HTTP (19200) + WebSocket (19201) bridge
│   ├── switch_model.ps1              # Model switcher (natsume / atri)
│   ├── pixi.min.js, pixi-shim.js     # PIXI.js v7 rendering
│   ├── model/shiki_natsume/          # Natsume model (14 textures, 42 motions, 41 sounds)
│   └── model/atri/                   # ATRI model (2 textures, 620 voice mp3, 8 motions)
├── ren_pro_jp/                       # Ren'Py dialog engine (planned)
├── memory/                           # [.gitignore] Runtime memory
│   └── role_play/                    # Roleplay conversation logs
├── media/                            # [.gitignore] Generated media
│   ├── audio/                        # TTS voice output
│   ├── images/                       # ComfyUI image output
│   └── *.gif                         # README demo GIFs
├── docs/
│   ├── telegram-setup.md             # Telegram Bot setup guide
│   └── qqbot-setup.md                # QQ Bot setup guide
└── skills/
    ├── live2d/                       # Live2D control skill
    │   ├── SKILL.md                  # Motion/expression reference + API guide
    │   ├── scripts/start-live2d.ps1  # Live2D launcher
    │   └── media/                    # Shared media output
    ├── tts/
    │   ├── SKILL.md                  # TTS invocation guide
    │   ├── run_tts.ps1               # TTS launcher script
    │   ├── tts_call.py               # GPT-SoVITS inference
    │   └── ref_wavs/                 # Reference audio clips
    ├── comfyui/
    │   ├── SKILL.md                  # ComfyUI invocation guide
    │   ├── run_comfyui.ps1           # ComfyUI launcher script
    │   ├── comfyui_call.py           # ComfyUI inference
    │   ├── prompt_template.md        # Character prompt template
    │   └── custom_prompt.txt         # Custom extra prompt
    ├── asr/                          # Speech recognition skill
    │   ├── run_asr.ps1               # Faster-Whisper launcher (~1.5GB VRAM)
    │   └── asr_call.py               # Whisper small model inference
    ├── shared/                       # Shared infrastructure
    │   ├── embedding_server.py       # OpenAI-compatible embedding API (9999, dual model)
    │   ├── mem0_bridge.py            # mem0 Qdrant →OpenClaw memory bridge
    │   ├── start_embedding_server.ps1 # Auto-start embedding server
    │   ├── vram.py                   # VRAM tier auto-detection
    │   ├── VRAM_LEVELS.md             # VRAM tier documentation
    │   ├── llama_lifecycle.py        # Llama start/stop management
    │   └── llama_utils.py            # Llama utility functions
    ├── sakura/                       # Sakura Desktop Pet (PySide6 GUI)
    │   ├── SKILL.md                  # Sakura skill documentation
    │   ├── main.py                   # Application entry point
    │   ├── install.bat               # Windows dependency installer
    │   ├── start.bat                 # Windows launcher
    │   └── app/                      # Source code
    ├── cosmos/                       # 🔮 NVIDIA Cosmos WFM (future hardware)
    │   ├── BRIDGE_REFERENCE.md       # Cosmos ↔ AI Girlfriend bridge design
    │   ├── cosmos_check.py           # Hardware VRAM detection script
    │   ├── cookbooks/                # Official tutorial examples
    │   └── README.md                 # Upstream documentation
    ├── llama-management.md           # VRAM management architecture doc
    ├── llama-watchdog.ps1            # Llama health check
    ├── cleanup_orphans.ps1           # Orphan process cleanup
    ├── behavior-engine/              # 💖 Relationship system (behavior engine)
    │   ├── engine.py                 # State load/save/update/reset
    │   ├── hormones.py               # Hormonal cycle (Gaussian model)
    │   ├── conflict.py               # 4-level conflict system
    │   ├── stages.py                 # 9 relationship stages
    │   ├── behavior_tick.py          # Behavior decision layer
    │   ├── online_tick.py            # Online/sleep simulation
    │   ├── daily_life.py             # Daily schedule
    │   ├── README.md                 # Design doc
    │   └── SKILL.md                  # Usage guide
    └── character_importer/           # SillyTavern character card auto-import
```

## 🤖 Claude Code + AgentRQ-Style Task Board (NEW)

Artemis now supports **Claude Code** as a parallel agent runtime alongside OpenClaw. Claude Code connects via MCP to access all Artemis capabilities - **with a built-in AgentRQ-compatible task queue** for human-agent collaboration.

### How it works

```
┌─────────────────────────────────────────────────────────┐
│  Task Board (http://127.0.0.1:19280)                    │
│  Create task → assignee: agent → notstarted             │
└───────────────────────┬─────────────────────────────────┘
                        │ SQLite (.claude/task_queue.db)
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Claude Code (terminal)                                 │
│  CLAUDE.md → getNextTask() → ongoing → execute          │
│  Artemis tools → TTS / ComfyUI / Live2D / memory        │
│  reply() → updateTaskStatus(completed)                  │
└─────────────────────────────────────────────────────────┘
```

### AgentRQ-Style Task Loop

Claude Code automatically runs a task loop on startup:
1. `getWorkspace()` - check workspace status
2. `getNextTask()` - dequeue next pending task
3. `updateTaskStatus(taskId, "ongoing")` - claim it
4. Execute using Artemis tools (TTS, ComfyUI, etc.)
5. `reply(taskId, "Done!")` - report result
6. `updateTaskStatus(taskId, "completed")` - mark done
7. Loop back to `getNextTask()`

### Launch

```powershell
# Prerequisites: npm install -g @anthropic-ai/claude-code
# Start Shiki Daemon first (.\shiki.cmd), then:

# Full AgentRQ workflow (Task Board + Claude Code)
.\claude-code.ps1

# Task Board only (browser UI, no Claude)
.\claude-code.ps1 -BoardOnly

# Stop the task board
.\claude-code.ps1 -KillBoard
```

Then open **http://127.0.0.1:19280** - create tasks, watch Claude Code pick them up.

### MCP Tools (15 total)

| Category | Tool | Description |
|-|-|-|
| 🎤 TTS | `tts_generate` | Voice synthesis (character/lang/mood) |
| 🎨 Image | `comfyui_generate` | AI image generation (prompt, checkpoint) |
| 🎤 ASR | `asr_transcribe` | Speech-to-text (wav/mp3/ogg/flac, Whisper small, ~1.5GB VRAM) |
| 🎭 Live2D | `live2d_emotion` | Motion + speech bubble |
| 🔄 Char | `switch_character` / `list_characters` | Character management |
| 🧠 Memory | `memory_search` / `memory_add` | Vector memory (mem0 Qdrant) |
| 📊 Status | `get_status` | Service health check |
| 📋 Task | `getWorkspace` / `getNextTask` / `createTask` | Task queue ops |
| 📋 Task | `updateTaskStatus` / `reply` / `getTaskMessages` | Task lifecycle |

### Artemis Task Board vs AgentRQ

| Feature | Artemis Task Board | AgentRQ (self-hosted) |
|-|-|-|
| Runtime | 1 Python script + SQLite | Go+Vue+Docker+Google OAuth |
| MCP tools | 6 task + 9 Artemis (15 total) | Same set (8 tools) |
| Setup | Zero config | Docker + .env + OAuth |

### Files

| File | Purpose |
|-|-|
| `.mcp.json` | MCP server config for Claude Code |
| `.claude/CLAUDE.md` | Persona + task loop instructions |
| `.claude/artemis_mcp_server.py` | MCP server (15 tools, JSON-RPC stdio) |
| `.claude/task_board_api.py` | Task board HTTP API (port 19280) |
| `.claude/task_board.html` | Task board browser UI |
| `.claude/task_queue.db` | SQLite task database (auto-created) |
| `.claude/settings.local.json` | Pre-approved MCP tools |
| `claude-code.ps1` / `.sh` | Launcher scripts |

## Skills Overview

| Skill | Type | Llama Kill? | Mechanism |
|-|-|-|-|
| **Embedding** | Background process | ❌No | all-MiniLM-L6-v2 + BGE-small-zh-v1.5 dual models (CPU, port 9999) -OpenClaw memory search + mem0 bridge |
| **Live2D** | HTTP exec | ❌No | Direct HTTP calls to `localhost:19200` bridge |
| **Web Chat** | Browser | ❌ No | Local daemon proxy to llama :8080, port 19270, real-time chat |
| **Claude Code** | Terminal (MCP) | ❌ No | Parallel agent runtime via .claude/artemis_mcp_server.py, uses llama :8080 directly |
| **TTS** | sessions_spawn | 🔶 VRAM-tiered | ≥12GB: no kill; 8GB: stop llama →GPT-SoVITS →restart llama |
| **ComfyUI** | sessions_spawn | 🔶 VRAM-tiered | ≥12GB: no kill; 8GB: stop llama →image gen →restart llama |
| **ASR** | sessions_spawn | ❌No | Faster-Whisper small (~1.5GB VRAM, coexists with llama) |
| **Sakura** | Shared llama-client | ❌No | Detects llama down →waits →auto-resumes |
| **Artemis Studio** | Desktop console | ❌No | TTS/ComfyUI visual workshop, standalone - works regardless of llama status |

## Environment Dependencies

| Component | Version / Source | Purpose |
|-|-|-|
| [OpenClaw](https://docs.openclaw.ai) | latest | AI Agent Gateway |
| [Claude Code](https://github.com/anthropics/claude-code) | latest | Terminal-based AI agent (optional, MCP integration) |
| QQ Bot | OpenClaw qqbot channel | QQ message relay |
| Telegram Bot | OpenClaw telegram channel | Telegram message relay |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | b9222 | Local LLM inference server |
| [GPT-SoVITS v2](https://github.com/RVC-Boss/GPT-SoVITS) | v2pro-20250604 | TTS voice synthesis |
| [ComfyUI](https://github.com/comfyanonymous/ComfyUI) | aki-v3 | Image generation engine |
| [Sakura Desktop Pet](https://github.com/Rvosy/Sakura) | v0.9.6-dev | Desktop companion GUI |
| [pixi-live2d-display](https://github.com/guansss/pixi-live2d-display) | v0.5.0 (bundled) | Live2D WebGL renderer |
| Live2D Cubism Core | 4.x (bundled: `live2d/live2dcubismcore.min.js`) | Live2D physics/animation |

> ✨**TTS, ComfyUI, and Live2D are fully self-contained.** No external downloads at runtime -all model weights (`skills/sovits/`, `skills/comfyui_core/`), Python scripts, JS libraries (`live2d/pixi.min.js`, `live2d/plid-v5-bundle.js`), and Cubism Core 4 (`live2d/live2dcubismcore.min.js`) are bundled locally.
>
> 🧠 **Headroom token-saving** -`skills/headroom/` (SmartCrusher + ContentRouter + CCR). Compress large tool outputs in dev scenarios before they hit the context window. See AGENTS.md for API usage.
| headroom | Bundled (`skills/headroom/`) | SmartCrusher context compression + ContentRouter + CCR |
| Python | 3.12+ | Runtime (Sakura + TTS + ComfyUI + Headroom) |

## Quick Start

### 🚀 All-in-One (Recommended)

**One command, from scratch to a fully functional AI girlfriend:**

**Windows:**
```powershell
powershell -File setup-all.ps1
```

**Linux / macOS:**
```bash
bash setup-all.sh
```

Automated pipeline: environment check →model download →llama.cpp setup →OpenClaw install →Sakura desktop pet →workspace deploy →path check →launch →verify.

> Supports resume from breakpoint. Flags: `--skip-model-download`, `--skip-llama-setup`, `--skip-openclaw-setup`, `--skip-sakura-setup`, `--dry-run`, `--no-start`

-

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

Interactive wizard -enter your local paths once, all scripts are updated automatically.

### 4. Quick Launch

```powershell
# One-click start all services (llama + Embedding + Live2D + Gateway)
powershell -File start.ps1
```

Startup sequence:
```
[1/8] llama-server        (8080, Qwen3.6-35B-A3B-MTP, --no-mmap, --spec-type draft-mtp)
[2/8] Embedding Server    (9999, all-MiniLM + BGE dual models, CPU, ~100MB RAM)
[3/8] VRAM Tier Detection (auto-selects whether TTS/ComfyUI stops llama)
[4/8] Headroom Proxy      (19251, mem0 memory injection + SmartCrusher compression + cloud routing)
[5/8] Live2D Bridge       (19200, pixi-live2d-display)
[6/8] OpenClaw Gateway    (18789, auto-injects local-llama provider)
[7/8] llama-watchdog      (crash auto-restart)
[8/8] Web Chat Daemon     (19260 API + 19270 webchat, --no-llama)
```

**Shutdown: `shiki.cmd -Stop`** -gracefully stops all services (llama →live2d →sakura →embedding →comfyui →gateway →cleanup).

### 5. Start Live2D Individually

```powershell
# Start the bridge
Start-Process node -ArgumentList "live2d-bridge.mjs" -WorkingDirectory live2d -WindowStyle Hidden

# Open in standalone window (Chrome app mode)
Start-Process chrome -ArgumentList "--new-window --app=http://localhost:19200/index.html --window-size=450,650"
```

Live2D runs in a frameless Chrome window -place it anywhere on your desktop.

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

<table>
<tr><td colspan="2" align="center"><b>User Entry</b></td></tr>
<tr><td colspan="2" align="center">QQ Bot &nbsp;|&nbsp; Telegram Bot &nbsp;|&nbsp; WebChat &nbsp;|&nbsp; Claude Code (MCP) &nbsp;|&nbsp; Artemis Studio Console</td></tr>
<tr><td colspan="2" align="center">↓</td></tr>
<tr><td colspan="2" align="center"><b>OpenClaw Gateway</b> (port 18789) &nbsp;──&nbsp; <b>Claude Code MCP</b> (stdio) &nbsp;──&nbsp; <b>Sakura Desktop Pet</b> (PySide6, shared llama-client)</td></tr>
<tr><td colspan="2" align="center">↓</td></tr>
<tr>
<td width="50%" valign="top">

**🧠 LLM Inference + Headroom**

| Component | Description |
|-|-|
| `llama-server :8080` | Qwen3.6-35B-A3B-MTP MoE |
| `headroom proxy :19251` | mem0 memory injection + SmartCrusher compression + model routing |
| Main session | AGENTS.md-driven roleplay |
| TTS | VRAM-tiered stop/run |
| ComfyUI | VRAM-tiered stop/run |
| ASR | Whisper small, coexists with llama |
| Sakura Pet | Shared client, no kill |
| Artemis Studio | Standalone, no kill |
| Live2D Bridge | HTTP :19200, no kill |

</td>
<td width="50%" valign="top">

**🧠 Memory System**

| Component | Description |
|-|-|
| Embedding :9999 | all-MiniLM-L6-v2 + BGE-small-zh-v1.5 (CPU, dual model) |
| memory_search | OpenClaw native hybrid search (vector+BM25) |
| mem0_bridge | Qdrant read/write bridge |
| Qdrant DB | collection: sakura_memories, 4 user_id scopes |
| CCR | Extracts facts every 8 turns → Qdrant |
| SmartCrusher | 24 msg/40K char hard cap |
| mem0_sync_cron | Every 30min: Qdrant → _mem0_auto.md |
| headroom_routes.json | sidecar: model_id → real backend baseUrl mapping |

</td>
</tr>
</table>

### Headroom + Mem0 Pipeline (port 19251)

```
OpenClaw Gateway (18789)
  ├─ <provider>/<model-id>           → Direct to original backend (skips headroom)
  ├─ local-llama/llama-local          → 19251 → llama-server:8080
  └─ local-llama/<model-id>           → 19251 → original backend (via headroom+mem0)
         │
         ▼
  headroom proxy (19251)
    ├─ [1] mem0 character memory injection (Qdrant vector search)
    ├─ [2] SmartCrusher 5-dim compressed conversation history
    └─ [3] Route to real backend
         ├─ llama-local → llama-server:8080
         └─ Cloud models    → sidecar finds real baseUrl
```

**Add-only, no-change principle:** `start.ps1` auto-scans `~/.openclaw/openclaw.json` on startup, adds `local-llama` provider (copies existing cloud model), original providers left as-is. Original baseUrl stored in `~/.openclaw/headroom_routes.json` sidecar file. Zero-config after clone.

### Agent Hub

Immutable capability instructions with per-character memory isolation:

| Layer | File | Purpose | On Switch |
|-|-|-|-|
| **Capability Hub** | `AGENTS.md` | ComfyUI/TTS/Live2D instructions | 🛡️ Immutable |
| **Quick Reference** | `TOOLS.md` | Tool invocation cheatsheet | 🛡️ Immutable |
| **Character Persona** | `SOUL.md` | Current character's personality/tone | 🔄 Hot-swapped |
| **Character Data** | `IDENTITY.md` | Character name/settings | 🔄 Hot-swapped |
| **User Profile** | `USER.md` | Boyfriend name/preferences | 🛡️ Immutable |
| **Harem Archive** | `skills/harem/<char>/` | Character card source of truth | 📦 Read-only |
| **Short-term Memory** | `memory/role_play/<char>/` | Daily conversations YYYY-MM-DD.md | 🔀 Per-char isolated |
| **Long-term Memory** | Qdrant `user_id=<char>` | Vector long-term memories | 🔀 Per-char isolated |
| **Sync Cache** | `_mem0_auto.md` | Qdrant → markdown (30min) | 🔀 Per-char isolated |

> Recall priority: Vector long-term memories > handwritten daily notes > SOUL base persona

### WebChat - Built-in Browser Client

A complete web-based AI girlfriend chat interface, served locally at `http://127.0.0.1:19270` by the shiki daemon.

| Feature | Description |
|-|-|
| **Multi-character Tabs** | Switch between Shiki Natsume, ATRI, and Yono Sakura - each with isolated conversation history, SOUL.md, and long-term memory |
| **Streaming Chat** | Real-time token streaming with character-tailored system prompt injection (role persona + user profile) |
| **Auto Paint** 🎨 | One-click button in the chat input area - LLM generates a ComfyUI prompt from conversation context, then triggers local image generation. Results appear inline in the chat flow |
| **Live2D Integration** | Control the Live2D desktop pet directly: tap head, poke, play idle animations |
| **TTS Voice** | Generate character voice replies from chat text via GPT-SoVITS |
| **Studio Panel** | Side panel for manual TTS synthesis and ComfyUI image generation with full parameter control (prompt, negative, size, steps, CFG, checkpoint) |
| **Dashboard** | Service health dashboard showing llama-server, Embedding, Live2D Bridge, Artemis Bridge, OpenClaw Gateway, and WebChat status - with per-service Start / Stop / Restart controls |
| **Llama Lifecycle Toggle** | Toggle whether to stop llama-server before ComfyUI image generation (frees VRAM for 8GB GPUs, default ON) |
| **Dual Model Support** | Choose between local llama-server or remote DeepSeek models - switch in settings, config persists |

> The WebChat talks directly to the shiki daemon (:19260) which proxies to llama-server or OpenAI-compatible APIs. Character-switching is instant - each tab loads its own SOUL.md + IDENTITY.md + USER.md as the system prompt.

### Skills Detail

| Skill | Location | Llama Interaction | Notes |
|-|-|-|-|
| **WebChat** | `web-chat/` | ❌ HTTP proxy | Port 19270, daemon-backed, multi-char |
| **Embedding** | `skills/shared/` | ❌ No GPU | Dual model CPU, port 9999 |
| **Live2D** | `skills/live2d/` | ❌ HTTP only | Bridge :19200, separate process |
| **TTS** | `skills/tts/` | 🔶 VRAM-tiered | Tier 2: no kill, Tier 0/1: stop llama |
| **ComfyUI** | `skills/comfyui/` | 🔶 VRAM-tiered | Same as above |
| **ASR** | `skills/asr/` | ❌ Coexist (1.5GB) | Faster-Whisper small |
| **Sakura** | `skills/sakura/` | ❌ Shared client | Built-in CCR + mem0 |
| **Artemis Studio** | `artemis_studio.py` | ❌ Standalone | Desktop console, TTS+ComfyUI workshop |
| **SmartCrusher** | `skills/shared/context_trimming.py` | - | 24 msg/40K cap |
| **CCR** | `skills/sakura/app/agent/memory_curator.py` | - | Every 8 turns fact extraction |
| **mem0 Bridge** | `skills/shared/mem0_bridge.py` | - | CLI search/add/sync |
| **Auto-Sync** | `skills/shared/mem0_sync_cron.py` | - | 30min Qdrant → md |
| **Character Importer** | `skills/character_importer/` | - | PNG/JSON card import |

**VRAM Orchestration Flow**:
1. On startup: auto-detect GPU VRAM →determine tier (Tier 0/1/2)
2. Main session receives user request →assembles command
3. `sessions_spawn(mode="run")` creates sub-session
4. Tier 0/1: `stop_llama()` frees VRAM →TTS/ComfyUI inference →`start_llama()` resumes
5. Tier 2 (≥12GB): direct inference, llama stays online
6. Artemis Studio, Live2D, Embedding stay active throughout -unaffected
7. Sub-session writes `.task_flags` →announces back to main session
8. Main session reads media files →sends via `<qqmedia>` / `MEDIA:`
9. Background: CCR runs every ~8 turns, extracting long-term memories to Qdrant
10. Cron job syncs Qdrant →`_mem0_auto.md` every 30 min for native `memory_search`
11. Headroom proxy (19251) transparently intercepts `local-llama/*` requests → injects mem0 → compresses context → routes to real backend

## ⚠️ Important Notes

- **RTX 50xx (Blackwell) + CUDA 13.x = `munmap_chunk(): invalid pointer` crash** - CUDA 13.x has known memory management incompatibility with llama.cpp on Blackwell GPUs. **Solution: use pre-built llama.cpp binaries compiled with CUDA 12.x** (not self-compiled with CUDA 13.x). Download from [llama.cpp Releases](https://github.com/ggml-org/llama.cpp/releases), choose `cudart-llama-bin-win-cuda-12.4-x64.zip`. RTX 5070 Ti is fully compatible with CUDA 12.x drivers.
- Llama-server is offline for ~60-120s during TTS/ComfyUI inference on 8GB VRAM (Tier 1) - conversation pauses, but Live2D + Artemis Studio keep running. On 12GB+ (Tier 2), no interruption at all
- Sub-sessions use **local model** (same as main), DeepSeek as optional fallback
- **The `cron` tool must be denied for the local llama model** -llama.cpp's GBNF grammar converter rejects any JSON Schema `pattern` that is not fully anchored with `^...$`. OpenClaw's cron tool declares `pattern: "\\S"` on nested properties (`job.declarationKey`, `job.displayName`), so **every** request carrying the full toolset fails with `400 JSON schema conversion failed: Pattern must start with '^' and end with '$'`, then silently falls back to the remote model. Only nested/array-level patterns trigger it; top-level ones convert fine. Fix in `~/.openclaw/openclaw.json`:
  ```jsonc
  "tools": {
    "byProvider": {
      "llama/qwen3.6-35b": { "deny": ["cron"] }
    }
  }
  ```
  `tools.*` does not hot-reload, so restart the gateway afterwards. Scheduling still works through remote-model sessions.
- Llama-server does not support cross-turn prompt cache reuse (SSM limitation) -use periodic `/reset`
- **Live2D requires Cubism Core 4** (not 5 or 6) - pixi-live2d-display v0.5.0 is built for Cubism 4 Framework; Core 5+ causes clipping/layer failures. **Core 4 is bundled** in live2d/live2dcubismcore.min.js - no CDN needed.
- All model files protected by `.gitignore`
- GPT-SoVITS weights are self-trained and not distributed -train with your own voice data

## 🙏 Credits

- [@Rvosy](https://github.com/Rvosy) -Creator of [Sakura Desktop Pet](https://github.com/Rvosy/Sakura), authorized for inclusion (Issue #38)
- [@guansss](https://github.com/guansss) -Creator of [pixi-live2d-display](https://github.com/guansss/pixi-live2d-display)
- [Live2D Inc.](https://www.live2d.com) -Cubism SDK (non-commercial use)
- [AgentRQ](https://github.com/agentrq/agentrq) -Inspiration for the AgentRQ-compatible task queue and MCP tool interface design
- [headroom](https://github.com/chopratejas/headroom) -Inspiration for SmartCrusher context compression + CCR (Curate-Consolidate-Retrieve) memory pipeline
- [mem0](https://github.com/mem0ai/mem0) -Inspiration for Qdrant vector memory architecture + hybrid search design
- [NVIDIA Cosmos](https://github.com/NVIDIA/cosmos) -World Foundation Model, [community FP8 quant](https://huggingface.co/benjiaiplayground/Cosmos3-Nano_fp8) archived at `skills/cosmos/`
