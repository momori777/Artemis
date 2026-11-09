# Agent Platforms — Configuration Reference

三个 Agent 运行时的配置示例与分析文档。每个子文件夹对应一个平台，包含：
- 实际配置文件示例（example/config）
- 启动 token 注入分析
- 可编辑注入文件速查

## Directory Structure

```
Agents/
├── openclaw/          # OpenClaw Gateway (main runtime)
├── claude-code-ccr/   # Claude Code via Claude Code Router
└── deepseek-harness/  # DeepSeek Harness (dsh)
```

## Platforms

### 1. OpenClaw (`openclaw/`)

Primary agent runtime. Uses monolithic system prompt injection.

| File | Description |
|------|-------------|
| `openclaw.example.json` | Gateway config template (copy to `~/.openclaw/openclaw.json`) |
| `startup-token-analysis-2026-11-08.md` | Startup token budget measurement (9,506 tok subagent) |

**Config locations:**
- Project: `openclaw.example.json` (root)
- User: `~/.openclaw/openclaw.json`
- Skills: `~/.openclaw/agents/main/agent/workshop-skills/`

### 2. Claude Code + CCR (`claude-code-ccr/`)

Claude Code routed through Claude Code Router (CCR). CCR isolates `~/.claude` into profile directories; customizations must edit the profile directory copy, not the global one.

| File | Description |
|------|-------------|
| `ccr-profile-settings.json` | CCR profile settings (from `AppData/Roaming/claude-code-router/profiles/default-claude-code/claude/settings.json`) |
| `ccr-profile-dot-claude.json` | Profile `.claude.json` |
| `CLAUDE.md` | Project-level Claude Code instructions |
| `claude-code-ccr-启动注入token分析.md` | Startup token analysis (35,578 tok) |
| `claude-code-ccr-上下文窗口与autocompact配置.md` | Context window & autocompact config |
| `三平台-skill-memory-可编辑注入文件速查.md` | Cross-platform editable injection file reference |

**Config locations:**
- CCR root: `~AppData/Roaming/claude-code-router/`
- Profile: `~AppData/Roaming/claude-code-router/profiles/default-claude-code/claude/`
- Project: `.claude/CLAUDE.md`, `.claude/settings.local.json`
- CCR port: `3456` (model gateway), `3458` (web UI) — see `config.yaml`

### 3. DeepSeek Harness (`deepseek-harness/`)

Community-named "大肥鱼". Different architecture: layered env + YAML credentials, no monolithic system prompt. Core clone in `benchmark_projects/deepseek-harness/` (git-ignored).

**Config composition:** dsh uses a layered profile system:
```
cordis.yml (empty base []) 
  → package.json bundles (@deepseek-ai/dsh-base, dsh-web-app)
  → cordis.patch.yml (user overrides)
  → --patch CLI overlays
```

| File | Description |
|------|-------------|
| `dsh-credentials.example.yaml` | Credentials template (masked) — API tokens, device grants |
| `dsh-profile-desktop-cordis.yml` | Desktop profile base (empty entry list) |
| `dsh-profile-desktop-cordis.patch.yml` | Desktop user patch: default model, UI settings, theme |
| `dsh-profile-desktop-package.json` | Desktop bundle definitions (dsh-base + dsh-web-app) |
| `dsh-profile-desktop-pnpm-workspace.yaml` | Desktop pnpm workspace config |
| `dsh-profile-web-cordis.patch.yml` | Web user patch: **includes Strata :8080 provider config** |
| `dsh-profile-web-package.json` | Web bundle definitions |
| `dsh-profile-web-pnpm-workspace.yaml` | Web pnpm workspace config |
| `dsh-workspace.example.json` | Workspace storage (workspace IDs, sessions) |
| `dsh-启动注入token分析.md` | Startup token analysis (gitignored) |

**Key:** The web profile's `cordis.patch.yml` configures dsh to use the local Strata engine (`http://127.0.0.1:8080/v1`) as an OpenAI-compatible provider — no model duplication needed.

**Config locations:**
- User: `~/.dsh/.credentials.yaml`
- Profiles: `~/.dsh/profiles/<name>/` (cordis.yml + cordis.patch.yml + package.json)
- Storage: `~/.dsh/storages/workspace.json`
- Setup: `setup-dsh.ps1` / `setup-dsh.sh` (project root)
- Web UI: `dsh web` (npx, no install needed)

## Cross-Platform Reference

For the full cross-platform comparison (token budgets, editable files, architecture differences), see:
- [`../docs/agent-platform-token-budget.md`](../docs/agent-platform-token-budget.md) — Integrated 3-platform token budget document
- `claude-code-ccr/三平台-skill-memory-可编辑注入文件速查.md` — Quick reference for editable injection files (gitignored, source of truth on Desktop)

## Notes

- Desktop source of truth: `C:\Users\momori\Desktop\Agents\` (original analysis reports)
- This directory contains project-integrated copies + actual config examples
- CCR profile directory isolation means `~/.claude` edits don't affect Claude Code; edit the profile copy instead
- dsh references existing inference backends (llama.cpp :9931 / Strata :8080) directly — no model duplication
