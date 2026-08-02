# airi 深度分析报告

> 分析对象：`C:\Users\TK\.openclaw\workspace\ai-companion-compare\airi`（moeru-ai/airi，本地克隆 v0.11.3）
> 分析日期：2026-08-02

## 1. 项目概览

- **定位**：Project AIRI（アイリ），自我定位为"Re-creating Neuro-sama"——
  一个把 AI waifu / 虚拟角色带入现实世界的"灵魂容器"，官方描述是 LLM powered virtual character。
- **目标**：让用户"随时随地拥有自己的数字生命"，远不止聊天：能看屏幕、玩游戏、进 Discord、上直播。
- **作者/组织**：Moeru AI Project AIRI Team（主创 Neko Ayaka / nekomeowww），
  衍生子项目另立组织 `@proj-airi`（RAG、记忆、DuckDB、Live2D 工具等）。
- **Star 量级**：约 1 万+（曾登 Trendshift、Product Hunt 精选；社区含 Discord/QQ/Telegram/微信；
  注：本地无网络，未核实精确数字）。
- **许可证**：MIT（Copyright 2024-PRESENT Neko Ayaka）。
- **维护状态**：非常活跃。版本已至 0.11.3（bucket/scoop 清单仍停在 0.9.0-alpha.18）；
  DevLog 更新到 2026.03；本地 git 最新提交 2026-08-02；官方手册对应 0.10.2。
- **成熟度**：文档自称仍处"早期阶段"，大量功能标记 WIP / Not yet released。

## 2. 技术栈

- **工程底座**：pnpm 10 monorepo（catalog 依赖）+ Turbo、TypeScript、Nix flakes（`nix run` 一键运行）、
  Vitest / ESLint(antfu) / oxlint / tsdown 构建。
- **前端**：Vue 3 + Vite + Pinia + VueUse + UnoCSS + reka-ui。
- **渲染层**：Three.js（stage-ui-three）、Live2D（stage-ui-live2d）、MMD、Spine、Tachie 立绘。
- **客户端形态**：Electron 桌面（旧 Tauri 已废弃）、Capacitor + Kotlin/Swift 移动端、Web PWA。
- **AI 层**：自研 `xsai`（类 Vercel AI SDK 的轻量库），对接 30+ LLM provider，支持 OpenAI 兼容接口。
- **语音**：`unspeech` 通用 ASR/TTS 代理 + ElevenLabs / Azure / 阿里云 / Kokoro 本地 TTS。
- **本地推理**：HuggingFace candle（CUDA/Metal）；浏览器 WebGPU 推理为 WIP。
- **数据/记忆**：DuckDB WASM、PGlite、Drizzle ORM（自研驱动）、memory-pgvector（Postgres 向量记忆）。
- **后端**：Hono（HTTP + WebSocket）+ better-auth + Stripe + OpenTelemetry/Langfuse + Postgres/Redis（docker-compose）。
- **其他**：Godot 4（C#）实验舞台引擎（engines/）、类型安全 IPC（eventa）、DI（injeca）。

## 3. 核心架构

- **apps/**：stage-web（浏览器端）、stage-tamagotchi（Electron 桌面端）、stage-pocket（移动端）、component-calling、ui-server-auth。
- **packages/**：core-agent（agent 运行时编排）、core-character（分段/情绪/延迟/可选 TTS 流水线）、
  pipelines-audio、stream-kit、memory-pgvector、server-runtime/server-sdk/server-shared、stage-ui* 系列、ui、i18n。
- **engines/**：stage-tamagotchi-godot（Godot 3D 舞台，含 Godot-MToon-Shader，实验性）。
- **services/**：computer-use-mcp；**plugins/**：bilibili 直播、claude-code、chess、homeassistant、web-extension。
- **integrations/**：discord-bot、telegram-bot、satori-bot（可接 QQ 等）、minecraft（mineflayer）、twitter-services、vscode。
- **server/**：apps/api（Hono HTTP+WS：鉴权、计费、聊天同步、模型网关、可观测）+ drizzle-migration + docker-compose。
- **数据流（官方架构图）**：Core ← xsai(LLM) + Memory(DuckDB/PGlite/pgvector)；Core → Stage(UI)；
  Core → STT(unspeech)；Core → Server(server-runtime/SDK)；Core 另驱动 Minecraft/Factorio 游戏 agent。
- **入口**：`pnpm dev`(web) / `pnpm dev:tamagotchi`(桌面) / `pnpm dev:pocket:*`(移动) / `pnpm dev:server`(后端)。
- **"身体模块"概念**：意识(LLM)、发声(TTS)、听觉(STT)、视觉(截屏+vision)、作画(Artistry)、
  记忆(未发布)、Discord/X/Minecraft/Factorio/MCP/音游等模块可独立开关。

## 4. 功能能力矩阵

| 能力 | 支持度 | 证据 |
| --- | --- | --- |
| LLM 后端 | ★★★★★ | xsai 驱动 30+ provider，OpenAI 兼容兜底；Ollama/vLLM/SGLang 本地；WebGPU 本地推理 WIP |
| 记忆 | ★★☆ | DuckDB/PGlite/pgvector 包已有，但 UI 短期/长期记忆与 Memory Bank 均标 "Not yet released" |
| 角色定义 | ★★★★ | Character Card 全字段（Identity/Behavior/Modules/Artistry/Settings），可创建/导入/切换/激活 |
| 语音 TTS | ★★★★ | 多 provider 音色 + 试听；lipsync/mediapipe 口型同步包 |
| 语音输入 STT | ★★★☆ | 浏览器/桌面/Discord 音频、客户端识别、VAD 说话检测；手册自述听力功能未成功跑通 |
| 虚拟形象 | ★★★★★ | Live2D/VRM/MMD/Spine/Tachie；自动眨眼、视线跟随、待机动画；Three.js + Godot 舞台 |
| Agent 能力 | ★★★★ | 玩 Minecraft/Factorio/KSP/DomeKeeper；屏幕视觉、computer-use MCP、下棋、Home Assistant |
| 多模态 | ★★★☆ | 视觉（截屏+vision 模型）、图像生成（Artistry）；纯本地推理未完成 |
| 多渠道 | ★★★★★ | Web/PWA、Win/macOS/Linux、iOS/Android、Discord/Telegram/Satori/Bilibili 直播/X |

## 5. 部署与上手难度

- **普通用户**：极易。下载安装包（或 winget / scoop / brew / flatpak），
  启动后选语言 → 填 LLM API Key（手册以 DeepSeek 为例）→ 选模型即可聊天。
- **开发者**：门槛高。巨型 pnpm monorepo（catalog 依赖 + postinstall 自动构建），
  需 Node + pnpm；桌面端需 Electron 工具链；移动端需 Xcode/Android Studio；NixOS 需 `nix develop .#fhs`。
- **自托管后端**：可选。server/ 提供 docker-compose（API + Postgres + Redis）支撑账号/计费/同步，单机可不开。
- **外部依赖**：LLM API Key 为硬需求（除非自建本地推理）；
  Discord/X/Minecraft 等模块需自备 bot token 与文件，未随安装包分发。

## 6. 优点与缺点

**优点**：
- 最接近"数字生命"完整闭环：意识→听觉→发声→身体全身模块化，远超纯聊天式陪伴应用。
- 形象渲染能力顶级：多格式模型 + 自动眨眼/视线/待机，桌面常驻（置顶/点击穿透/托盘）。
- LLM provider 覆盖极广，OpenAI 兼容 + 本地推理（Ollama/vLLM/candle），国内模型齐全。
- 渠道覆盖全：Web/桌面/移动/QQ(Satori)/Discord/Telegram/直播/游戏内。
- Agent 扩展性强：游戏、屏幕视觉、MCP、Home Assistant、VSCode/Claude Code 插件。
- 工程与社区活跃：devlog 持续、多语言、多平台安装渠道、迭代快。

**缺点**：
- 记忆系统名不副实：核心包有雏形，但产品级记忆（Memory Bank、短期/长期记忆）未发布，陪伴连续性打折。
- 门槛与文档问题：monorepo 庞大、文档滞后，手册自述大量功能"未测试/仅为猜测"。
- 半成品与 bug 并存：模型重载需重启、Window Shortcuts 空页无返回、启动闪烁等被官方手册直接记录。
- 部分能力依赖外部机器人/服务；STT、本地推理等关键链路成熟度待验证。
- 深度依赖外部 LLM API，纯离线/私有化体验尚不完整。

## 7. 与 AI 陪伴场景的契合度总结

- **评分：8.5 / 10**。
- **结论**：airi 是当前开源 AI 陪伴赛道中"形态最完整、上限最高"的项目之一。
- 虚拟形象（Live2D/VRM）、角色卡定制、多端常驻、语音双向对话、屏幕视觉与游戏陪伴一应俱全，
  "活着的伙伴感"远超同类。
- 扣分点：记忆系统未落地（影响长期陪伴黏性）、大量功能 WIP/半成品、开发与深度定制门槛高、依赖云端 LLM。
- 若目标是"开箱即用的陪伴角色"：已可用且体验独特；
  若看重稳定成熟度或长期记忆：需等待记忆模块发布或自行补齐。

*（本报告基于本地源码与官方文档，未联网核实 Star 数与最新发布版。）*
