# CCR (Claude Code Router) 技能

让 Claude Code 通过 CCR 网关连接本地 llama.cpp 模型。

## 架构

```
Claude Code ──settings.json──► CCR 网关(:ccr_port) ──► llama-server(:ccr_upstream_port)
                                    │
                                    └── 管理界面(:ccr_web_port)
```

- **CCR**：`@musistudio/claude-code-router`（npm 全局安装 `ccr` 命令），本地模型网关，负责
  Claude Code 的 Anthropic 协议 ↔ OpenAI 兼容协议转换、密钥注入、请求路由与用量统计。
- **端口集中配置**：所有端口从项目根 `config.yaml` 读取，脚本不硬编码。
  - `ccr_port`（默认 3456）— 模型网关，Claude Code 的 `ANTHROPIC_BASE_URL` 指向它
  - `ccr_web_port`（默认 3458）— 管理界面
  - `ccr_upstream_port`（默认 8080）— 上游 llama-server

## 启动 / 停止

```powershell
# 启动 CCR（后台，自动拉起网关）
.\skills\ccr\start-ccr.ps1

# 停止 CCR
.\skills\ccr\stop-ccr.ps1

# 启动 Claude Code（走 CCR + 加载 Artemis MCP + 可选任务面板）
.\claude-code-ccr.ps1
.\claude-code-ccr.ps1 -NoTaskBoard   # 不起任务面板网页

# 关闭 Claude Code 配套服务（任务面板 + 可选 CCR）
.\stop-claude-code-ccr.ps1
.\stop-claude-code-ccr.ps1 -All     # 同时停 CCR
```

`ccr start` 会复用已运行的服务（写 `service.json`），重复执行不会起第二份。

## 配置（一次性）

CCR 的 provider / 模型 / 客户端 Key 通过管理界面 `http://127.0.0.1:<ccr_web_port>` 配置，
存储在 `%APPDATA%\claude-code-router\config.sqlite`，不经由本仓库配置文件。

- 供应商：自定义「其他 / 自定义 API 地址」，`http://127.0.0.1:<ccr_upstream_port>/v1`
- 模型 ID 自由命名（llama.cpp 不校验，会路由到已加载模型）
- Claude Code 的 `ANTHROPIC_BASE_URL`/`apiKeyHelper` 由 CCR 自动写入 `~/.claude/settings.json`

## MCP 任务面板

Claude Code 从项目根启动时**自动加载 `.mcp.json`**，其中定义了 `artemis` stdio MCP server
（`.claude/artemis_mcp_server.py`）。该 server 提供：

- **任务队列工具**（AgentRQ 兼容）：`getWorkspace` / `getNextTask` / `createTask` /
  `updateTaskStatus` / `reply` / `getTaskMessages`
- **Artemis 能力工具**：`tts_generate` / `comfyui_generate` / `live2d_emotion` /
  `switch_character` / `list_characters` / `memory_search` / `memory_add` / `get_status` / `asr_transcribe`

首次启动需在 Claude Code 会话里 approve 一次 `artemis` MCP server。工具权限已在
`.claude/settings.local.json` 预置 allow。

此外还有独立的可视化任务面板（`.claude/task_board_api.py`，端口 `task_board_port`，默认 19280），
`claude-code-ccr.ps1` 会默认拉起并在浏览器打开，供人工查看任务队列。

## 端口约定

| 端口 | 服务 | 配置键 |
| --- | --- | --- |
| 8080 | llama-server | `llama_port` / `ccr_upstream_port` |
| 3456 | CCR 模型网关 | `ccr_port` |
| 3458 | CCR 管理界面 | `ccr_web_port` |
| 19280 | 任务面板网页 | `task_board_port` |

OpenClaw 相关端口（`19251` headroom、`18789` gateway 等）与本技能无关，启动脚本不会触碰。
