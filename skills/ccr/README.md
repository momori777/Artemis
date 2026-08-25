# CCR 技能 / CCR (Claude Code Router) Skill

## 中文

让 Claude Code 通过 CCR 网关连接本地 llama.cpp 模型。

- **CCR**：`@musistudio/claude-code-router`（npm 全局安装 `ccr` 命令），本地模型网关
- **架构**：Claude Code → CCR 网关（`ccr_port`，默认 3456）→ llama-server（`ccr_upstream_port`，默认 8080）；管理界面在 `ccr_web_port`（默认 3458）
- **端口**：全部从项目根 `config.yaml` 读取，脚本不硬编码

### 文件结构

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 完整使用文档（启动/停止、MCP 任务面板、端口约定） |
| `start-ccr.ps1` / `start-ccr.sh` | 启动 CCR（后台，自动拉起网关） |
| `stop-ccr.ps1` / `stop-ccr.sh` | 停止 CCR |

### 快速使用

```powershell
# Windows
.\skills\ccr\start-ccr.ps1
.\skills\ccr\stop-ccr.ps1

# Linux / macOS
./skills/ccr/start-ccr.sh
./skills/ccr/stop-ccr.sh
```

CCR provider / 模型 / 客户端 Key 通过管理界面 `http://127.0.0.1:<ccr_web_port>` 配置，
存储在 `%APPDATA%\claude-code-router\config.sqlite`。

## English

Connects Claude Code to the local llama.cpp model through a CCR (Claude Code Router) gateway.

- **CCR**: `@musistudio/claude-code-router` (globally installed `ccr` npm command), a local model gateway
- **Architecture**: Claude Code → CCR gateway (`ccr_port`, default 3456) → llama-server (`ccr_upstream_port`, default 8080); admin UI on `ccr_web_port` (default 3458)
- **Ports**: all read from the project root `config.yaml`; scripts never hardcode them

### Files

| File | Description |
|------|-------------|
| `SKILL.md` | Full usage docs (start/stop, MCP task board, port conventions) |
| `start-ccr.ps1` / `start-ccr.sh` | Start CCR (background, auto-launches the gateway) |
| `stop-ccr.ps1` / `stop-ccr.sh` | Stop CCR |

### Quick Start

```powershell
# Windows
.\skills\ccr\start-ccr.ps1
.\skills\ccr\stop-ccr.ps1

# Linux / macOS
./skills/ccr/start-ccr.sh
./skills/ccr/stop-ccr.sh
```

CCR provider / model / client key are configured via the admin UI at
`http://127.0.0.1:<ccr_web_port>` and stored in
`%APPDATA%\claude-code-router\config.sqlite`.
