# 角色卡导入 / Character Card Importer

## 中文

一键导入 SillyTavern 角色卡，存到后宫（harem）目录，随时切换女友。

### 核心设计

- **AGENTS.md** — 能力中枢（ComfyUI/TTS/Live2D），角色切换不改它
- **SOUL.md / IDENTITY.md** — 当前活跃角色，切换时覆写
- **skills/harem/\<角色\>/** — 后宫存档，每个角色独立目录
- **memory/role_play/\<角色\>/** — 每个角色的独立记忆

### 文件结构

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 完整使用文档（命令速查、工作流程） |
| `card_importer.py` | 主脚本（list / preview / switch / import-chat） |
| `cards/` | SillyTavern 角色卡存放目录（PNG 或 JSON） |

### 快速使用

```powershell
# 列出所有可用角色
python skills\character_importer\card_importer.py list

# 预览角色卡
python skills\character_importer\card_importer.py preview "cards/Enola.png"

# 从 ST 角色卡切换（自动备份当前角色到 harem）
python skills\character_importer\card_importer.py switch "cards/Enola.png" --force

# 切回后宫中的角色
python skills\character_importer\card_importer.py switch-harem natsume
```

## English

One-click import SillyTavern character cards into the harem directory, switch girlfriends on demand.

### Core Design

- **AGENTS.md** — capability hub (ComfyUI/TTS/Live2D), never modified on character switch
- **SOUL.md / IDENTITY.md** — currently active character, overwritten on switch
- **skills/harem/\<char\>/** — harem archive, one directory per character
- **memory/role_play/\<char\>/** — per-character memory

### Files

| File | Description |
|------|-------------|
| `SKILL.md` | Full usage docs (command reference, workflow) |
| `card_importer.py` | Main script (list / preview / switch / import-chat) |
| `cards/` | SillyTavern character card storage (PNG or JSON) |

### Quick Start

```powershell
# List all available characters
python skills\character_importer\card_importer.py list

# Preview a character card
python skills\character_importer\card_importer.py preview "cards/Enola.png"

# Switch from ST card (auto-backs up current character to harem)
python skills\character_importer\card_importer.py switch "cards/Enola.png" --force

# Switch back to a harem character
python skills\character_importer\card_importer.py switch-harem natsume
```
