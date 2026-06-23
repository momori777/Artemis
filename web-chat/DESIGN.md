# Web Chat UI - AI Girlfriend Chat Frontend

## Overview

Browser-based chat interface for the AI Girlfriend project, serving as an alternative to QQ/Telegram bots. Directly connects to the local daemon proxy which routes to llama.cpp server or cloud LLM providers.

## Design Direction

| Dimension | Value |
|-----------|-------|
| **Design Read** | Desktop web app - private-haven - dark-tech + warm-intimate |
| **VARIANCE** | 5 (offset, left-sidebar + right-chat) |
| **MOTION** | 4 (CSS transitions + entry animations) |
| **DENSITY** | 3 (airy, art-gallery spacing) |
| **Color** | off-black deep - singular rose accent (#d4787a) - no AI-purple |
| **Font** | Inter + Noto Sans SC + JetBrains Mono |
| **Shape** | rounded-md 14px - all-soft system |

## Architecture

```
Browser (http://127.0.0.1:19270)
    |
    v
shiki_daemon.py (port 19260 API, 19270 webchat thread)
    |
    v
llama.cpp server (port 8080, OpenAI-compatible /v1/chat/completions)
or cloud LLM providers (DeepSeek, Grok via openclaw.json config)
```

## File Structure

```
web-chat/
  index.html              Main chat interface (single-page app)
  DESIGN.md               This file - design documentation
  scripts/
    api.js                Chat API client, routes through daemon /api/chat
    chars.js              Character definitions + fallback + API loading
    importer.js           SillyTavern character card importer (PNG/JSON)
    store.js              LocalStorage persistence (settings, chats, sessions)
    studio.js             Artemis Studio panel (TTS/ComfyUI placeholder)
    ui.js                 Chat UI controller with multi-session support
  styles/
    main.css              Core theme + layout (~1000 lines)
    polish.css            Micro-polish + animation refinements
  assets/                 (reserved) character avatars, icons, static resources
```

## Implemented Features

- [x] Three-column layout: character info panel + chat flow + input area
- [x] Dynamic character loading from daemon `/api/characters` (scans `skills/harem/`)
- [x] Character card import (SillyTavern PNG/JSON format)
- [x] Model/provider selector (local llama + cloud via openclaw.json)
- [x] Real LLM chat via daemon `/api/chat` proxy (llama.cpp + DeepSeek + Grok)
- [x] Chat bubbles (user/character colors, timestamps)
- [x] Typing indicator animation
- [x] Auto-expanding textarea
- [x] Fallback replies when API is unavailable
- [x] Session reset/clear
- [x] Multi-session chat history (localStorage)
- [x] Mobile responsive (sidebar collapse)
- [x] Toast notifications
- [x] Artemis Studio placeholder panel (TTS/ComfyUI)
- [x] Settings panel with model selection
- [x] Desktop notifications on message receive

## API Flow

1. User types message -> `ui.js` captures input
2. `api.js` sends POST to `http://localhost:19260/api/chat` with model + messages
3. Daemon `_handle_chat_proxy()` resolves provider from model ID prefix:
   - `local/qwen3.6-35b` -> llama.cpp :8080 (no auth)
   - `deepseek/deepseek-v4-pro` -> DeepSeek API via openclaw.json
4. Response streamed back through daemon -> `api.js` -> `ui.js` renders bubble

## Taste-Skill Compliance

- [x] Emoji banned (none in UI text, Phosphor icons only)
- [x] No em-dash anywhere
- [x] No AI-purple (#d4787a rose accent only)
- [x] No pure black (#000000) or white (#ffffff)
- [x] No generic 3-column feature cards
- [x] Color lock: single accent, single palette
- [x] Shape lock: all-soft radius system
- [x] Dark mode only (consistent, no section inversions)
- [x] Reduced motion: all animations are CSS-only, light
- [x] Hero fits viewport (chat IS the hero)
- [x] Nav single-line on desktop
- [x] No hand-rolled SVG icons
- [x] No decorative status dots (only semantic online indicator)
- [x] Responsive: mobile sidebar collapse

## Known Limitations

- Chat history is localStorage-only (no cloud sync)
- No message search yet
- No dark/light theme toggle (always dark)
- No real-time notifications (polling, not WebSocket)
- Artemis Studio panel is placeholder UI (TTS/ComfyUI controlled via AGENTS.md subagents)
