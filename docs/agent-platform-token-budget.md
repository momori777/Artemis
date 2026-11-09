# Agent Platform Startup Token Budget

> **Date:** 2026-11-08 ~ 2026-11-09 (measured)
> **Model:** `qwen3.8-flash-next-iq3_s` (IQ3_S quantization, max_context 131072) via Strata llama.cpp `:8080`
> **Method:** Differential token probing (`/v1/chat/completions`, `max_tokens=1`, read `usage.prompt_tokens`) + cold-start isolated session measurement + platform logs/source code
> **Original reports:** `C:\Users\momori\Desktop\Agents\` (kept as source of truth; this file is the project-integrated summary)

---

## 1. Baseline Calibration (Strata / llama.cpp)

| Probe request | prompt_tokens |
|---|---|
| Empty user message (pure chat template overhead) | **52** |
| `"hi"` single user message | 53 |
| system="You are a helpful assistant." (6 tok) + `"hi"` | 60 |

- Template fixed overhead: **52 tokens**
- Text density: **~0.372 tok/char** (for char→token conversion; CJK mixed text)
- Note: `/tokenize` endpoint does not exist (404); differential method required.

---

## 2. Platform Comparison Summary

| Client | Cold-start injection | Main composition | Multiplier vs OpenClaw |
|---|---|---|---|
| **OpenClaw** (sub-agent, isolated) | **9,506 tok** (measured) | Base system prompt + ~30 tool JSON schemas + skill directory (capped at 8,000 chars) | 1.0× |
| **OpenClaw** (webchat main session) | **~12,900 tok** (estimated) | Above + channel instructions, UI presentation, side chat, collapsible details | ~1.4× |
| **Claude Code + CCR** (desktop local-agent) | **35,578 tok** (measured) | Massive base system prompt (~29K chars) + ~28 tool schemas + skill directory (no cap) + environment block | **~3.7×** |
| **DeepSeek Harness (DSH)** | N/A (different architecture) | 4 independent injection chains: env snapshot, LLM credentials, web boot token, subprocess env scrubbing | — |

### Key finding

- **CCR injects 0 tokens into the prompt.** Its role is protocol conversion (Anthropic → OpenAI), model name folding, and header rewriting only.
- The entire 35.6K for Claude Code comes from **Claude Code (Agent SDK) itself**: base system prompt + tool schemas + environment/skill reminders.
- DSH does not inject a single monolithic system prompt like the other two; its "token injection" is distributed across env snapshots, credential resolution, and cookie-based auth (no prompt text added).

---

## 3. OpenClaw Breakdown

### Measured (clean isolated sub-agent)

| Component | Tokens | Measurement |
|---|---|---|
| Chat template overhead | 52 | Measured |
| AGENTS.md (1,930 chars) | 594 | Differential |
| SOUL.md (666 chars) | 157 | Differential |
| IDENTITY.md (203 chars) | 54 | Differential |
| **Project context total (2,801 chars)** | **807** | Differential |
| Skill directory (86 skills, 22,339 chars → capped at 8,000 chars) | **~2,606** | Differential (at cap) |
| Base system prompt + tool policies + runtime context + tool JSON schemas | **~8,500–9,000** | Residual estimate |

### Optimization levers

1. Narrow `tools.alsoAllow` in `openclaw.json` (fewer tool schemas = fewer tokens)
2. Reduce skill count or trim skill descriptions (already at the 8,000 char cap)
3. Disable unused plugin tools

---

## 4. Claude Code + CCR Breakdown

### Measured (first round, fresh session)

| Component | Est. tokens | Confidence |
|---|---|---|
| Base system prompt (`You are a Claude agent…` + `<application_details>` + `<claude_behavior>` + `<computer_use>` + artifacts + auto memory) | ~9–11K | Estimate (visible transcript chars) |
| Tool JSON schemas (~36 tools: Read/Write/Edit/Glob/Grep/Agent/Skill/WebSearch/bash/web_fetch/Task/Cowork×10/plugins/scheduled…) | ~10–15K | Estimate |
| `<available_skills>` (10 skills, descriptions 600–900 chars each, **no truncation**) | ~2K | Estimate |
| Agent type reminders (4 subagent descriptions) | ~0.5K | Estimate |
| Environment block (`role:"system"` in messages) | ~1–1.4K first round, +0.2–0.7K per update | Measured chars |
| Chat template + user message | ~100 | Measured |

- Residual ~8–14K unaccounted (tokenizer density higher for XML/JSON/CJK mixed content than the 0.372 anchor)
- **CCR volume effect:** client body 171,236 B → upstream 134,754 B (−21.3%) due to stripping Anthropic-specific fields (`thinking`, `cache_control`, `metadata`, beta fields)

### Optimization levers

1. **Narrow tool surface:** Remove unused Cowork/artifact/screenshot tools ≈ −3–6K per round (also breaks llama.cpp prefix cache on first hit)
2. **Trim skill descriptions** in profile directory
3. **Edit via CCR profile directory, not `~\.claude`:** CCR sets `CLAUDE_CONFIG_DIR` to `%APPDATA%\claude-code-router\profiles\default-claude-code\claude\`, isolating the user's native `~\.claude`. To customize CLAUDE.md / skills / settings, edit the **profile directory** copy.
4. CCR v3 uses profile/route-level config for prompt injection — do NOT look for v1/v2 `APPEND_PROMPT` env vars.

---

## 5. DeepSeek Harness (DSH) Architecture

DSH does not follow the "one big system prompt" model. Its injection is split into 4 chains:

| Chain | Mechanism | Key packages |
|---|---|---|
| 1. Launch env snapshot | `loadLayeredEnv("dsh")` merges `process.env > cwd/.env > $DSH_HOME/.env`, tags each value with source, provides to all plugins before mounting | dsh-app-boot, dsh-launch-environment |
| 2. LLM credentials | Config stores only `credentialRef` (env name) or `credentialKey`; real values resolved via "managed YAML → process env → project .env → home .env", written as HTTP headers by route packages | dsh-credentials(-local), dsh-llm-* |
| 3. Web boot token | `randomBytes(32)` one-time token in URL `?token=***`, exchanged for HMAC-signed HttpOnly cookie on first visit | dsh-client-connection, dsh-web-app |
| 4. Subprocess env scrubbing | `scrubbedParentEnv()` strips all names matching `/KEY\|PASSWORD\|SECRET\|TOKEN/i` + all `DSH_*`; shell gets only 5 identity keys | dsh-subprocess, dsh-shell-env |

**Design principle:** Secrets live in exactly two places (launch snapshot + credential service). Upward they become headers/cookies; downward they are stripped. Config surfaces see only reference names, never values.

### Editable injection surfaces (DSH)

- Project layer: `cwd/.env` (bootstrap/endpoint/proxy vars forbidden)
- User layer: `$DSH_HOME/.env` (proxy vars allowed)
- Managed: `$DSH_HOME/.credentials.yaml` (plaintext YAML, POSIX 0600 enforced)
- Skills/memory file layout: **not covered in the analysis report** — verify against source when needed

---

## 6. Cross-Platform Editable Injection Files

| Dimension | Claude Code + CCR | OpenClaw | DSH |
|---|---|---|---|
| Base system prompt | Built-in, **not editable** (~29K chars) | Built-in, not editable | Built-in, not editable |
| Project context files | `CLAUDE.md` (via CCR profile dir) | `AGENTS.md` + `SOUL.md` + `IDENTITY.md` (workspace root) | `cwd/.env` + project files |
| User/global context | Profile dir `skills/` + `CLAUDE.md` | `~\.openclaw\openclaw.json` + home skills | `$DSH_HOME/.env`, `~/.agents` |
| Memory mechanism | auto-memory: one `.md` per memory + `MEMORY.md` index (index injected, body on-demand) | mem0 + Qdrant RAG (project-specific) | Not covered in report |
| Skill directory | Profile dir `skills/<name>/SKILL.md` | Global skills dir, `<name>/SKILL.md` | `~/.agents` mounted |
| Skill truncation | **None** (descriptions sent in full) | `skills.limits.maxSkillsPromptChars = 8000` (hard cap) | Not documented |

### One-liner comparison

- **OpenClaw:** Most structured and token-efficient. Three named context files + explicit skill cap. Easiest to control.
- **Claude Code:** Most flexible but most expensive. No truncation, rich file-based memory model. Extra CCR profile isolation layer on this machine.
- **DSH:** Context = layered env + YAML managed files. Skill/memory file layout not fully documented in the analysis.

---

## 7. Practical Implications for This Project

1. **Context budget planning:** When designing context trimming or display features, account for the platform's base injection:
   - OpenClaw path: reserve ~10–13K tokens for startup
   - Claude Code path: reserve ~36K tokens for startup
   - DSH path: platform-specific, verify per deployment

2. **Model context limit:** With `max_context 131072` and Claude Code's 35.6K startup, only ~95K remains for conversation + tools + images. OpenClaw leaves ~118K.

3. **Cross-platform compatibility:** The same character card / memory / skill content behaves differently across platforms:
   - OpenClaw: skill descriptions truncated at 8,000 chars total
   - Claude Code: no truncation (longer descriptions = more tokens every round)
   - DSH: env-based, file layout TBD

4. **When adding new skills/memory:**
   - OpenClaw: keep descriptions concise (already at cap with 86 skills)
   - Claude Code: edit in CCR profile directory, not `~\.claude`
   - All: remember the base system prompt is NOT editable on any platform

---

## 8. Measurement Reproduction

To reproduce these measurements:

1. **Baseline probe:** Send empty user message + `"hi"` to `:8080/v1/chat/completions` (max_tokens=1), read `usage.prompt_tokens`. Expected: 52 / 53.
2. **Cold start:** Create a fresh isolated session on the target platform, send a minimal probe ("PONG"), read `usage.prompt_tokens` from the platform's logs or the Strata access log.
3. **Differential:** Toggle individual files (AGENTS.md, SOUL.md, skills) and measure the delta.

Scripts used (reusable):
- `C:\Users\momori\.openclaw\tmp\tok_probe.mjs` — baseline probe
- `C:\Users\momori\.openclaw\tmp\tok_split.mjs` — component splitting
- `C:\Users\momori\.openclaw\tmp\tok_skills.mjs` — skill directory measurement

API key: `~\.openclaw\openclaw.json → models.providers.strata.apiKey`

---

*Original detailed reports (with line-by-line evidence):*
- OpenClaw: `C:\Users\momori\Desktop\Agents\openclaw\startup-token-analysis-2026-11-08.md`
- Claude Code + CCR: `C:\Users\momori\Desktop\Agents\claude code\claude-code-ccr-启动注入token分析.md`
- DSH: `C:\Users\momori\Desktop\Agents\deepseek harness\dsh-启动注入token分析.md`
- Editable files reference: `C:\Users\momori\Desktop\Agents\claude code\三平台-skill-memory-可编辑注入文件速查.md`
