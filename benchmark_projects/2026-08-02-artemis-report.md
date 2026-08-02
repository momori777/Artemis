# Artemis 深度分析报告

> 分析对象：`ai-companion-compare/Artemis-master/`（内部另有一层同名目录，实际项目根为 `Artemis-master/Artemis-master/`）
> 分析日期：2026-08-02

## 1. 项目概览（定位/作者/Star 大致量级/许可证/维护状态）

- **定位**：100% 本地运行的「AI 女友」陪伴项目，主打隐私（零云端、零 API 依赖）、免费、无审查；自称所有对话/语音/图像/角色动画均在本地生成。中文社区项目（README_CN 为主，附 EN/JA），通过 B 站教程（BV16XTV6fEoH）、QQ 群（580322386）、百度网盘镜像分发，模型托管于 HuggingFace（作者账号 TAOTAO777）。
- **Star 量级**：本地副本无 `.git` 目录，无法确认 GitHub 主页与 Star 数；从分发方式（网盘 + QQ 群）判断属中小型个人开源项目，量级估计为数十到数百 Star，不宜夸大。
- **许可证**：CC BY-NC 4.0（署名-非商业），整体组合与角色设定禁商用；引用的第三方模型遵循各自原许可证。
- **维护状态**：活跃。备份文件日期到 2026-08-02，记忆目录有 2026-06 的会话记录；README 提到"四号女友投票中"，说明仍在持续迭代，且为 Windows 生态（作者实机 RTX 5070 8GB）。

## 2. 技术栈

- **LLM 推理**：llama.cpp（b9222）+ Qwen3.6-35B-A3B MoE GGUF（16.11GB，8GB 显存优化，实测 31~39 t/s 生成、50~60 t/s 实测标注），支持本地与云端（DeepSeek/Grok）混合路由。
- **Agent 框架**：OpenClaw Gateway（QQ/Telegram/WebChat 消息通道、cron、sessions_spawn）+ 可选 Claude Code（MCP 接入，15 个工具 + AgentRQ 风格任务看板）。
- **语音**：GPT-SoVITS v2 Pro（TTS，3 套角色声线、情绪模式）+ Faster-Whisper small（ASR，99 语言）。
- **图像/形象**：ComfyUI（SDXL/Illustrious 系 checkpoint）AI 画图；pixi-live2d-display v0.5.0 + Cubism Core 4 做 Live2D；PySide6 Sakura 桌宠。
- **记忆**：mem0 + Qdrant 向量库，双 embedding（all-MiniLM-L6-v2 英文 + BGE-small-zh-v1.5 中文），headroom（SmartCrusher 压缩 + CCR）做上下文管理。
- **语言**：Python 3.12+（守护进程/桥接/代理）+ Node.js（Live2D 桥、WebChat 前端）+ PowerShell 脚本为主、Bash 为辅。

## 3. 核心架构（模块划分、入口、数据流）

- **入口**：`quick_setup.ps1`（路径向导）→ `download-models.ps1`（~31.7GB 模型）→ `start.ps1` / `shiki.cmd`（一键启动 8 项服务）；另有 `setup-all.ps1/.sh` 全自动部署。
- **服务编排**：`shiki_daemon.py`（托盘守护，端口 19260 仪表盘）管理 8 个服务：llama-server(:8080)、Embedding Server(:9999)、VRAM 分档检测、Headroom 代理(:19251)、Live2D 桥(:19200/19201)、OpenClaw Gateway(:18789)、llama-watchdog、WebChat 守护(:19270)。
- **数据流**：OpenClaw 角色扮演对话 → `local-llama/*` provider → headroom proxy(:19251) 注入 mem0 向量记忆 + SmartCrusher 压缩（24 条/40K 字符硬限）→ 路由到 llama.cpp 或云端 sidecar；TTS/画图按 VRAM 分档决定是否临时停 llama 腾显存。
- **角色与记忆**：角色由 SOUL.md/IDENTITY.md + `skills/harem/<角色名>/` 定义（内置 50+ 角色），热切换时 TTS 权重/Live2D 模型/记忆全部联动；记忆按角色隔离（`memory/role_play/<角色>/` 每日摘要 + Qdrant user_id 分区）。
- **前端**：web-chat 为纯静态 HTML/JS（vanilla + localStorage 持久化），经 daemon API 代理直连 llama，支持角色导入、多会话、i18n；后端桥接含 `artemis_bridge.py`、`artemis_headroom_proxy.py`。

## 4. 功能能力矩阵

| 能力 | 支持度 | 证据 |
|---|---|---|
| LLM 后端 | ★★★★★ | llama.cpp 本地 Qwen3.6-35B MoE + DeepSeek/Grok 云端路由（headroom sidecar） |
| 记忆系统 | ★★★★★ | mem0+Qdrant 向量+BM25 混合检索、双语言 embedding、角色隔离、30 分钟自动同步 `_mem0_auto.md` |
| 角色定义 | ★★★★★ | SOUL/IDENTITY + harem 目录 50+ 角色、SillyTavern PNG/JSON 角色卡导入、JSONL 聊天记录导入 |
| 语音 | ★★★★★ | GPT-SoVITS TTS（3+ 声线、4 种情绪模式、中英日）、Faster-Whisper ASR（99 语言） |
| 虚拟形象 | ★★★★☆ | Live2D 实时渲染（2 个模型、情绪驱动表情/口型/气泡）+ Sakura 桌面宠物（主动关怀） |
| Agent 能力 | ★★★★★ | OpenClaw（cron 定时、sessions_spawn、多通道）+ Claude Code MCP 15 工具 + 任务看板 |
| 多模态 | ★★★★☆ | 文/图（ComfyUI）/语音/动画已打通；Cosmos 物理世界模型仅设计稿，等 24GB+ 显存 |
| 多渠道 | ★★★★★ | QQ Bot、Telegram Bot、WebChat 浏览器、终端、Claude Code 任务看板 |

## 5. 部署与上手难度

- **难度：中高**。虽有 `setup-all.ps1`/`setup-all.sh` 一键脚本（含断点续传、分步跳过），但整体是"8 个常驻服务 + 5 组模型"的组合系统，出问题时排障面广。
- **硬件门槛**：作者实机 RTX 5070 8GB 可跑全量（VRAM 分档自动停启 llama），推荐 8GB+ 显存、32GB 内存、约 32GB 磁盘下载模型；低于 8GB 会降级为纯聊天模式。
- **依赖**：Python 3.12+、Node.js、OpenClaw、llama.cpp、模型需从 HuggingFace 或百度网盘下载；ComfyUI/GPT-SoVITS 推理引擎已内置于 `skills/`，无需另装。
- **Windows 优先**：PS1 脚本为主力，sh 脚本覆盖 Linux/macOS；文档齐全（CN/EN/JA + 省流版手册），且有交互式配置向导降低门槛。

## 6. 优点与缺点

**优点**
- 全本地运行：隐私、离线可用、零 token 费用，明确移除内容审查（对成人陪伴场景是卖点）。
- 功能密度极高：多角色热切换、向量记忆、TTS/ASR、Live2D、画图、桌宠、双 Agent 运行时、SillyTavern 生态兼容，几乎覆盖 AI 陪伴全部能力面。
- 工程化程度好：VRAM 自适应分档、llama 看门狗自愈、headroom 上下文压缩、角色记忆隔离、一键部署脚本，中文文档详实且活跃维护。

**缺点**
- CC BY-NC 4.0 非商业许可限制商用分发/二次开发。
- 硬件与存储要求偏高（32GB 模型下载、8GB+ 显存），低配机器体验大幅缩水。
- 架构复杂、服务多（llama/embedding/headroom/live2d/gateway/watchdog/webchat），Windows+PS 生态为主，跨平台与运维成本高。
- 本地模型局限：输出上限 8192 tokens、SSM 架构无跨请求 prompt cache（长对话每次全量重处理，59K token 约 55s）。
- Cosmos 世界模型仍为规划态；部分配置文件中文注释存在编码乱码现象，社区分发（网盘）非官方 Git 源。

## 7. 与 AI 陪伴场景的契合度总结

- **评分：9/10**。这是为"AI 陪伴"这一场景量身定制的项目——多角色热切换 + 独立记忆 + 情绪化 TTS 声线 + Live2D 形象 + 桌宠 + 多渠道接入，契合度是横向对比中最完整的。
- **结论**：若用户具备 8GB+ 显存 NVIDIA 显卡、愿意投入约半天部署，Artemis 是当前功能最全、私密性最好的本地 AI 伴侣方案；扣分项主要在部署复杂度和硬件门槛。若追求低配置/轻量级陪伴，可考虑更简单的单服务方案。

---
*报告生成方式：读取 README_CN.md、AGENTS.md、USAGE.md、web-chat/README.md、config.example.yaml、skills/tts/SKILL.md、shiki_daemon.py、LICENSE、memory 目录等代表性文件后综合整理。*
