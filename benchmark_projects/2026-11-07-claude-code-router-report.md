# Claude Code Router 生态调研 — 2026-11-07

搜索方式：GitHub Search API（unauthenticated），14 组查询（`claude code router in:name,description` / `topic:claude-code-router` / `ccr ui|gui|dashboard|webui|frontend|manager windows|可视化|面板` / `musistudio claude-code-router` / `users/musistudio/repos`），逐个 README 前 14~20 行验货。

本机上下文：已装 `@musistudio/claude-code-router` v3.1.3，CCR 网关 3456 / 管理界面 3458 已跑通（上游 Strata:8080，Anthropic `/v1/messages` → OpenAI chat 转译，200 OK）。本报告回答「GitHub 上有没有 CCR 项目 + 有没有写得不错的前端」。

## 已克隆（benchmark_projects/，--depth 1）

| 目录 | 上游 | Stars | 最近 push | 语言/栈 | 关键点 |
|---|---|---|---|---|---|
| `cc-router` | [finch-xu/cc-router](https://github.com/finch-xu/cc-router) | **293** | 2026-11-05 | Rust + Tauri 2 + React 19 + TS5 + Tailwind4 | 本地大模型聚合网关 + 桌面 GUI，零代码；把 Coding Plan / API 额度合成一个虚拟 Plan；入站 Anthropic Messages + OpenAI Responses + Chat Completions 三口并存，出站 24 家 preset；顺序/轮询/会话亲和调度 + 自动故障切换；用量「小票」导出；中/繁/英/日四语 UI，有官网 ccrouter.app + 三语文档 + DeepWiki。**工程质量本次最高**（11.4MB 仓库，含 .github、docs、release-notes、scripts）。注意：它是**自己的网关**（监听 127.0.0.1:23456），不是 CCR 的前端 |
| `ccr-ui` | [windviki/ccr-ui](https://github.com/windviki/ccr-ui) | 0 | 2026-08-18 | Python FastAPI + 原生 JS（`static/app.js` 9.4KB） | 自称「CCR v3 内置 Web UI 打不开时的替代品」。走 CCR 的 HTTP RPC（`getConfig`/`saveConfig`）**不直接碰 config.sqlite**，提供模型切换 / Provider 增删改 / 默认切换。src 只有 4 个模块约 26KB，但配了 unit + integration（含 `test_e2e.py`）共 33KB 测试——**代码量小、结构干净、有测试**。为 VS Code Server 网页内嵌场景写的 |
| `ccr_service_manager` | [KoSukeWork/ccr_service_manager](https://github.com/KoSukeWork/ccr_service_manager) | 1 | 2025-09-28 | 单文件 PowerShell（`ccr_manager.ps1`） | **Windows 专用** CCR 后台运行管理：start/stop/restart/status/logs/errors/clean + 守护进程（崩溃自动重启、防僵尸、隐藏运行）+ 日志管理。param/ValidateSet 写得规范。解决的就是我们刚踩到的坑：CCR 挂在启动它的终端下，会话一死端口就掉 |

## 未克隆备选（按「是否给 CCR 做前端」排序）

| 上游 | Stars | push | 说明 |
|---|---|---|---|
| [musistudio/claude-code-router](https://github.com/musistudio/claude-code-router) | **38,030** | 2026-10-10 | 本项目本体。定位已从「Claude Code 专用 router」升级成「one local control plane for every AI agent」。dist/ 里带 `main/next-ai-gateway.js`（1.9MB 网关核心）+ `renderer/`（内置管理界面），所以 **:3458 那个 Web UI 就是官方前端**，不必另找 |
| [danscMax/castellyn](https://github.com/danscMax/castellyn) | 0 | 2026-11-05 | Tauri v2 + Rust 原生「AI coding 环境控制中心」：多 profile（`~/.claude-<name>`）、providers & routers、MCP、plugins & skills、并行会话/fork 维护，一个窗口全包；英/俄/中三语 UI 热切换；明确反 Electron（省内存）。**当天还在 push**，新星但方向极对 |
| [Ding-Ding-Projects/claude-code-router](https://github.com/Ding-Ding-Projects/claude-code-router) | 0 | 2026-10-01 | 描述写「Material Design 3 rewrite of the Claude Code Router management UI」——CCR 管理界面的 MD3 重写。README 列的能力（retries/credential pools/key rotation/ordered fallback/Fusion vision/web search/MCP/ToolHub/request logs/latency/token/cost 估算）与 CCR v3 本体一致，更像官方 UI 的主题化改版 + Claude Design 迁移桥。Kimi 赞助 |
| [NightYuYyy/ccr-desktop](https://github.com/NightYuYyy/ccr-desktop) | 12 | 2025-08-16 | Electron + Vue3 跨平台 CCR 桌面面板：服务一键启停、实时状态、执行日志、默认模型切换、多服务商配置。功能对口但**一年多没动**，Electron 体积也不划算 |
| [misswell/CCRBar](https://github.com/misswell/CCRBar) | 1 | 2026-10-23 | 纯 SwiftUI **macOS 菜单栏**应用，管 CCR 启停/状态，刻意不嵌 WebView（省内存），已 Apple 公证 + Sparkle 自动更新，中英双语。mac 限定，我们是 Windows 用不上 |
| [HiderX/CCRouter](https://github.com/HiderX/CCRouter) | 5 | 2026-11-06 | 名字带 CCRouter 但**不做代理**：按会话绑定 Claude Code 账号，菜单栏看各账号额度，`ccrouter` 像 `claude` 用。macOS 菜单栏 + 官方 CLI 取额度，不碰 token/不转发流量 |
| [Jonny-china/3router](https://github.com/Jonny-china/3router) | 0 | 2026-06-22 | 本地 Claude Code API 路由代理，按消息内容路由到不同上游/模型，规则引擎 + 多上游 + 系统守护进程 + Web 管理面板 |
| [ekmungi/switchboard](https://github.com/ekmungi/switchboard) | 0 | 2026-07-06 | 把 CCR 指向 OpenRouter 模型的 CLI 控制面板（catalog browse） |
| [DiMY-CN/Claude-Code-Chat-for-Claude-Code-Router](https://github.com/DiMY-CN/Claude-Code-Chat-for-Claude-Code-Router) | 9 | 2025-08-16 | VSCode 扩展（fork 自 andrepimenta/claude-code-chat），把 Claude Code 调用路径改走 CCR |
| [KoSukeWork/ccr_service_manager](https://github.com/KoSukeWork/ccr_service_manager) | 1 | 2025-09-28 | 已克隆，见上表 |
| [QAA-Tools/ccproxy](https://github.com/QAA-Tools/ccproxy) | 18 | 2026-02-04 | 轻量 Claude API 反代，Web UI 即时切供应商、自动发现模型、批量测模型可用性 |
| [codeking-ai/cligate](https://github.com/codeking-ai/cligate) | 135 | 2026-10-15 | 私有 AI 助手 + 统一模型代理（Claude Code / Codex CLI / Gemini），带 dashboard |
| [lich0821/ccNexus](https://github.com/lich0821/ccNexus) | 973 | 2026-10-30 | Go 写的 Claude Code / Codex CLI 智能 API 网关：端点轮换、用量监控。`topic:claude-code-router` 下星数最高的第三方 |
| [routatic/proxy](https://github.com/routatic/proxy) | 979 | 2026-11-06 | Go，把 Claude Code 请求路由到多家上游（OpenCode Go/Zen 等） |
| [yinxulai/osw](https://github.com/yinxulai/osw) | 199 | 2026-11-03 | 所有 LLM channel 收到一个本地地址后面，挂了就自动切下一个 |
| [finch-xu/cc-router](https://github.com/finch-xu/cc-router) | 293 | 2026-11-05 | 已克隆，见上表 |
| [luohy15/y-router](https://github.com/luohy15/y-router) | 384 | 2026-01-11 | TS，让 Claude Code 直连 OpenRouter 的简单 proxy |
| [pleaseai/shunt](https://github.com/pleaseai/shunt) | 261 | 2026-11-07 | Rust，按 agent 做选择性推理层路由，把 Claude Code 甩到任意模型 |
| [PAIArtCom/Clipal](https://github.com/PAIArtCom/Clipal) | 158 | 2026-11-01 | Go，最小化 LLM 反代（Claude Code/Codex/Gemini CLI），YAML 路由 + 热加载 |
| [glidea/claude-worker-proxy](https://github.com/glidea/claude-worker-proxy) | 276 | 2026-07-10 | Cloudflare Worker 版 CCR，部署简单，适合要公网入口的场景 |
| [router-for-me/CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI) | **57,845** | 2026-11-07 | 全场最高星。Go，把 Antigravity / ChatGPT Codex / Claude Code / Grok / Devin 反向包装成 OpenAI 兼容 API。方向是「订阅转 API」，不是 CCR 前端 |
| [decolua/9router](https://github.com/decolua/9router) | 32,062 | 2026-10-28 | JS，免费 AI coding 全家桶路由（Claude Code/Codex/Cursor/Cline/Copilot/Antigravity） |

## 结论与建议

1. **CCR 项目在 GitHub 上确认存在且很活跃**：`musistudio/claude-code-router`，38k star，最近 push 2026-10-10，与我们本机装的 npm `@musistudio/claude-code-router` v3.1.3 同一项目。v3 已经**自带 Web 管理前端**（就是我们现在用的 :3458，带 token 鉴权），另有 Tauri/Electron 官方外壳的说法不成立——`dist/` 里只有 `main/`（网关）+ `renderer/`（内置 UI）。
2. **「写得不错的前端」——如果指 CCR 的第三方 GUI**，本次实际找到三类：
   - **对口但质量一般**：`NightYuYyy/ccr-desktop`（Electron+Vue3，12★，一年未更新）、`windviki/ccr-ui`（FastAPI 薄前端，0★ 但代码干净有测试）。
   - **工程质量最好**：`finch-xu/cc-router`（293★，Tauri2+React19，四语文档 + 官网）——但它自带网关，**是 CCR 的替代品而不是皮肤**。想换架构可以试，想保留现有 CCR 就不适用。
   - **方向最对的新星**：`danscMax/castellyn`（Tauri 原生控制中心，管 profile/providers/routers/MCP/skills/并行会话，英中俄中三语，2026-11-05 仍在 push）。星数低但覆盖面正好是我们这套 Claude Code + 本地模型的用法。
3. **本机最实用的其实不是 GUI**：刚踩到「CCR 挂在启动它的终端会话下、会话一死 3456/3458 就掉」的坑。`KoSukeWork/ccr_service_manager`（Windows 专用，后台运行 + 守护进程崩溃自动重启 + 防僵尸 + 日志）正好对症，建议先把它移植成我们 `skills/ccr/` 里的常驻方案，而不是急着换前端。

推荐优先级：**A) 用 ccr_service_manager 的思路把 CCR 做成带守护的常驻服务**（解决稳定性，收益最直接）→ **B) 想要更好看的界面就看 castellyn**（原生 Tauri、管我们全套）→ **C) 想要 CCR 现成桌面皮肤再看 ccr-desktop / ccr-ui**（够用但维护弱）。`finch-xu/cc-router` 只在「考虑整体换掉 CCR」时才评估。
