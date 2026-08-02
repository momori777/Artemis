# neko 深度分析报告

## 1. 项目概览

- **定位**：N.E.K.O.（Networked Emotional Knowing Organism，网络型情感知性生命体）是一个**开源 AI 陪伴（AI 女友/数字生命）平台**，口号是"听见你的心情，看见你的世界，陪你发现更多喜欢"。它明确宣称"不是帮你干活的 Agent，也不是角色扮演聊天前端"，而是有现实时间感知、会主动找你、记得你、也能动手帮你的数字生命。
- **仓库**：GitHub `Project-N-E-K-O/N.E.K.O`（README 徽章指向该仓库与 wehos/N.E.K.O）；本地克隆为浅克隆（仅 1 条 commit），最新提交 2026-08-02，说明**维护极其活跃**。Star 量级无法从本地确认（web 搜索不可用），但已在 **Steam 免费上架**（App 4099310）、有独立官网 project-neko.online、Discord/QQ 社区，属中文圈头部开源陪伴项目（估测数千至万级 Star，以 GitHub 为准）。
- **许可证**：Apache-2.0（核心引擎始终开源）；版权归 Project N.E.K.O. Team / Hongzhi Wen（2025-2026）。
- **版本/状态**：当前 APP_VERSION = 0.8.3；有完善的 CI（unit-tests、plugin-tests、docker-multi-arch、desktop 打包等 13 个 workflow）、Docker 镜像、桌面打包（Nuitka/PyInstaller spec）、Steam 创意工坊 UGC。社区活跃，生态在扩张（移动端 Demo、AI 原生游戏 K.U.R.O.、"猫咪网络"AI 社交）。
- **仓库规模**：顶层 20+ 目录、约 500KB 的 requirements/uv.lock、大量提示词文件（prompts_*.py 单文件可达 300KB+）、数十个内置插件与数百个前端 JS 测试文件，属大型单体工程。

## 2. 技术栈

- **后端**：Python 3.11（严格限定 `==3.11.*`），FastAPI + Uvicorn + WebSockets，多进程（三个服务 + ZeroMQ 进程间桥接），uv 管理依赖（uv.lock）。
- **LLM/API**：openai / google-genai / anthropic / dashscope SDK，支持 14+ 服务商（Qwen-Omni、GPT-Realtime、Gemini、DeepSeek、Step、MiniMax、免费版"lanlan.tech/core"等），含实时语音 API（WebSocket Realtime）与普通 ChatCompletion 双路径。
- **语音**：TTS 多供应商（Qwen/Step/CosyVoice/GPT-SoVITS/MiniMax/ElevenLabs/MiMo/Doubao/GLM 等，ws_bistream 与 http_sentence 两类 worker）；ASR 语音识别 + 端点检测（endpointing）+ 说话人影子（speaker_shadow，ONNX 模型）；soxr 重采样、pyrnnoise 降噪。
- **记忆/嵌入**：SQLAlchemy + SQLite（time_indexed.db）、JSON 存储（recent/facts/reflections/persona）、BM25 + 本地 ONNX 向量（onnxruntime）混合检索（RRF 融合）、tiktoken 预算控制。
- **Agent/工具**：browser-use、Playwright、pyautogui/pywinauto（电脑操作）、CUA、OpenClaw A2A 适配、ZeroMQ（pyzmq）、MCP 适配。
- **形象/前端**：前端主栈为原生 JS（static/，含 live2d/pngtuber-core/vrm/mmd 渲染）+ 新 React 前端（frontend/react-neko-chat，React 18 + Vite + TS + Vitest）；Live2D/VRM/MMD/PNGTuber/桌面宠物五形态；python-osc 走 VMC 协议输出骨骼动画。
- **其他**：pyncm-async（网易云音乐）、bilibili-api/twitchio/aiotieba（直播弹幕/社交）、SteamworksPy（创意工坊）、RapidOCR（galgame 识别）、SQLite + psutil + orjson 等。

## 3. 核心架构

- **模块划分**：顶层 `launcher_core`（启动器）、`main_logic`（核心会话逻辑）、`main_routers`（REST 路由）、`app`（三个服务器）、`local_server`（可选本地服务）、`memory`（记忆实现）、`brain`（Agent 执行）、`plugin`（插件系统）、`steamworks`、`frontend`/`static`/`templates`（前端）、`config`（配置与提示词）、`docs`（VitePress 文档站）。
- **三服务器结构**：① **Main Server**（:48911）— Web UI/静态资源、REST API、`/ws/{name}` 浏览器 WebSocket、每角色 `LLMSessionManager`、外部 TTS 线程；② **Memory Server**（:48912）— 对话持久化、recent/facts/reflections/persona、新对话上下文渲染、混合召回；③ **Agent/Tool Server**（:48915，另内嵌用户插件服务 :48916）— 任务评估与分派；可选 Monitor Server（:48913）。三进程经 HTTP + ZeroMQ（PUB/SUB、PUSH/PULL，:48961-48963）通信。
- **入口**：`launcher.py` → `launcher_core.bootstrap/runtime`（venv 检测、端口策略、云存档、启动锁、多进程编排）；独立开发命令 `uv run python -m app.main_server` 等；`main_logic/core/manager.py` 的 `LLMSessionManager` 是核心装配点（每角色一个，聚合锁/队列/状态机/上下文追加/焦点/TTS/工具调用 mixin）。
- **数据流**：浏览器 WebSocket 发 `start_session(audio|text)` → 实时路径建 `OmniRealtimeClient`（原生音频 24k→48k 重采样）或离线路径建 `OmniOfflineClient` + 外部 TTS worker（48k PCM 回传）→ 会话结束 `cross_server.py` 把回合投递到 Memory Server 持久化/抽取 → Agent 桥对回合做任务意图分析 → 结果经 ZeroMQ 回传并注入聊天。
- **插件系统**：成熟 SDK（plugin/sdk：adapter/plugin/shared/hosted-ui）+ plugin.toml 清单契约 + CLI（neko-plugin）+ 插件市场（Steam 创意工坊），内置 20+ 插件（bilibili 弹幕、galgame、微信、米家智能家居、Minecraft、WarThunder、学习陪伴、音乐推送、QQ 自动回复、web_search 等）。

## 4. 功能能力矩阵

| 能力 | 支持度 | 证据 |
|---|---|---|
| LLM 后端 | ★★★★★ | 14+ 提供商（Qwen/GPT-Realtime/Gemini/DeepSeek/Step/免费版），实时语音+文本双路径，config/api_providers.json |
| 记忆 | ★★★★★ | 五维记忆：工作上下文/近期(recent.json)/事实(facts)/反思(reflections)/人格(persona)，BM25+ONNX 混合召回，事件日志+归档 |
| 角色定义 | ★★★★★ | 每角色独立 LLMSessionManager、角色卡（character_card_manager、角色卡分享/创意工坊）、多语言角色配置 |
| 语音 | ★★★★★ | 实时语音对话（Realtime API）、外部 TTS 多供应商管线、ASR+端点检测+说话人识别、声音克隆（voice_clone.html） |
| 虚拟形象 | ★★★★★ | Live2D/VRM/MMD/PNGTuber/桌面宠物五形态，动作捕捉、全屏追踪、VMC 骨骼输出、表情管理 |
| Agent 能力 | ★★★★☆ | 任务评估+DirectTaskExecutor，通道：browser-use/computer_use/MCP/OpenClaw A2A/OpenFang/用户插件；干完活自动注入聊天回执 |
| 多模态 | ★★★★☆ | 图像输入（截图/拖拽）、屏幕理解、实时视觉、OCR（galgame）、音乐/视频播放 |
| 多渠道 | ★★★★☆ | 桌面 Electron/浏览器 + 移动端 Demo + 直播弹幕（B站/Twitch）+ QQ/微信插件 + 智能家居（米家） |
| 主动性 | ★★★★★ | proactive_chat 服务：屏幕理解、社交媒体热梗、个人动态、音乐推荐、迷你游戏邀约、定时提醒（proactive_controller 插件） |

补充说明：免费版 LLM 通道开箱可用，但图像/视觉、本地 ASR/TTS、Agent 电脑操作等高级能力按需配置；记忆与角色数据全部本地存储（数据在用户手里）。

## 5. 部署与上手难度

- **开箱即用**：Windows/macOS/Linux 一键包（N.E.K.O.exe/.app/n.e.k.o），README 主打"零配置开箱即用，奶奶也能轻松唤醒的赛博猫娘"；内置免费版 LLM 通道（lanlan.tech/core，无需 API Key），大幅降低上手门槛。
- **源码运行**：Python 3.11 + `uv sync`（依赖极多：onnxruntime/playwright/浏览器内核、语音模型、GPU 可选），开发模式 `uv run python -m app.main_server` 等三进程，另需准备前端构建（vite）、语音/嵌入模型资产（scripts/prepare_*.py）。
- **配置**：config/ 下集中管理 API 提供商（api_providers.json）、角色/模型/记忆/主动性/配额等设置；角色卡、语音克隆、Live2D/VRM 素材均可在 Web UI（templates/ 各管理页）中配置，无需改代码。
- **发布物**：Steam 商店页（含创意工坊）、GitHub Releases 桌面安装包、Docker Hub/GHCR 镜像、VitePress 文档站（多语言）。
- **Docker（Linux）**：提供官方镜像（ghcr.io/project-n-e-k-o/n.e.k.o）与 docker-compose 示例（:48911/:48912），数据卷含配置/日志/SSL。
- **难度评价**：终端用户极低（解压即用）；自托管源码部署中高（依赖面大、多进程 + 端口策略 + 模型下载 + 桌面打包链路复杂）；二次开发有插件 SDK 门槛但文档齐全（docs/ 有架构、模块、插件、部署、基准测试等专题页）。

## 6. 优点与缺点

**优点**
- 功能密度极高：语音/形象/记忆/Agent/插件/多渠道/创意工坊全栈闭环，是市面上最完整的开源陪伴平台之一。
- 架构工程化程度惊人：三服务拆分、ZeroMQ 桥、每角色会话状态机、记忆管道分层（facts→reflections→persona）、队列化 TTS/异步抽取，代码规范（lint 门禁、禁止 loguru 等守卫脚本、大量单测/e2e/基准）。
- 文档与工具链完备：docs/ 有架构（三服务/数据流/记忆系统/TTS 管线/Agent 系统）、部署、插件开发等专题；scripts/ 有几十个诊断与准备脚本，开发友好度高于同类项目。
- 开源友好 + 商业化兼顾：Apache-2.0 核心、Steam 免费上架 + 创意工坊 UGC 分发、活跃社区与文档站。
- 主动性设计深入（屏幕感知、热梗、音乐、休息提醒），贴近"数字生命"而非"聊天框"。

**缺点**
- 体量巨大、复杂度高：单文件上万行（launcher_core/runtime.py 136KB、prompts_memory.py 336KB），依赖上百项，初次阅读/二次开发学习曲线陡峭。
- 部分能力依赖自有/第三方服务（免费版 lanlan.tech 通道、Steam、云存档），非 100% 纯离线；本地 ASR/TTS 需另配模型。
- 代码中存在编码显示问题与历史遗留（如 time_indexed_compressed 兼容表、旧 appendMessage 适配层），仓库规模对维护者要求高。
- Windows 生态偏重（pywin32/pywinauto/dxcam/Steamworks DLL），跨平台一致性依赖 CI 保障。
- 内部依赖自有福利通道与云服务（免费版 lanlan.tech、Steam、云存档），核心依赖链并不完全去中心化；对"纯离线、完全自持"的部署诉求需要额外改造。

## 7. 与 AI 陪伴场景的契合度总结

**评分：9.5 / 10**

- 契合度极高：N.E.K.O. 几乎就是"AI 陪伴"这一品类的标准答案——语音实时对话、Live2D/VRM 形象、五维持久记忆、主动搭话、屏幕/社交感知、Agent 动手能力全部围绕"关系与陪伴"而非"任务执行"设计，且零配置开箱即用、有免费通道和成熟社区生态。
- 作为对比基准的价值突出：本项目可直接作为陪伴场景的**功能天花板参照物**（记忆分层、TTS 管线、主动聊天服务、三服务器架构都是可借鉴的蓝本）；但因其复杂度，若对照项目目标是轻量/可移植/纯本地，则需取其设计精华而非整体复刻。
- 唯一保留：重度依赖在线 LLM/实时语音通道（自带免费福利通道缓解），完全离线场景需自行接入本地模型（vLLM-Omni/GPT-SoVITS 等已有雏形）。
- 横向对照提示：与 SillyTavern 类纯文本 RP 前端相比，neko 在"跨场景持久记忆 + 原生语音 + 形象 + 主动性"上完胜；与通用 Agent 框架相比，它把 Agent 能力降维为陪伴关系的一部分（A2A 可被调用），这正是陪伴类产品的正确姿态。

---

*报告生成时间：2026-08-02；依据：本地源码树（README/CONTEXT/pyproject.toml/launcher.py、main_logic 核心模块、app 三服务器、memory/brain/plugin/frontend、docs/architecture 文档）静态分析。*
