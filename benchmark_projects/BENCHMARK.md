# BENCHMARK.md — AI 角色扮演/虚拟人项目全景对比

> 分析日期: 2026-07-03  
> 范围: GitHub 上主要的开源 AI VTuber / AI 伴侣 / 角色扮演项目  
> 视角: 独立开发者单人项目 (Artemis) 在赛道中的位置  

---

## 一、项目一览

| 项目 | Stars | 团队 | 定位 | 语言 | 起跑 |
|------|-------|------|------|------|------|
| **SillyTavern** | 30,162 | 社区 | LLM 前端（角色卡生态） | JS | 2023-02 |
| **AIRI** | 41,378 | 100+ | AI VTuber 全栈平台 | TS | 2024-12 |
| **elizaOS** | 18,678 | 社区 | Agent 操作系统 | TS | 2024-07 |
| **Open-LLM-VTuber** | 12,271 | 社区 | 本地语音 VTuber | Python | 2023-11 |
| **Streamer-Sales** | 3,718 | 小团队 | 直播带货 AI | Python | 2024-04 |
| **Neuro (kimjammer)** | 2,002 | 单人 | Neuro-sama 复刻 | Python | 2024-01 |
| **Amica** | 1,558 | 小团队 | 3D 角色交互 | TS | 2023-10 |
| **AI-Waifu-Vtuber** | 1,095 | 单人 | Twitch VTuber | Python | 2023-03 |
| **Artemis (本项目)** | 164 | 单人 | 离线 AI 女友 | Python | 2026-06 |

---

## 二、核心能力矩阵

### 图例: ✅ 完整支持  ⚠️ 部分/WIP  ❌ 不支持

| 能力 | AIRI | SillyTavern | elizaOS | Open-LLM-VTuber | Streamer-Sales | Neuro | Amica | AI-Waifu | **Artemis** |
|------|------|-------------|---------|-----------------|----------------|-------|-------|----------|-------------|
| **本地 LLM 推理** | ⚠️ WIP | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| **API 提供商数量** | 30+ | 10+ | 20+ | 5+ | 3+ | 2+ | 0 | 2+ | 2 |
| **流式对话** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **实时语音对话** | ✅ | ❌ | ✅ | ⚠️ | ❌ | ⚠️ | ✅ | ⚠️ | ❌ |
| **VAD (语音检测)** | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **TTS** | ✅ 多引擎 | ✅ 多引擎 | ✅ 多引擎 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ GPT-SoVITS |
| **流式 TTS** | ✅ | ⚠️ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **STT/ASR** | ✅ 多引擎 | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ Whisper |
| **Live2D** | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ |
| **VRM 3D** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **口型同步** | ✅ | ❌ | ❌ | ✅ | ❌ | ⚠️ | ✅ | ✅ | ❌ |
| **AI 画图** | ❌ | ✅ SD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ ComfyUI |
| **角色卡导入** | ❌ | ✅ 原生 | ⚠️ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ ST 兼容 |
| **多角色切换** | ⚠️ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 后宫系统 |
| **长期记忆** | ⚠️ WIP | ✅ Summarize | ✅ RAG | ❌ | ✅ RAG | ❌ | ❌ | ❌ | ✅ mem0+Qdrant |
| **Token 压缩** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ SmartCrusher |
| **对话树/分支** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **QQ 接入** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Telegram 接入** | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Discord 接入** | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **游戏能力** | ✅ MC/Factorio | ❌ | ✅ 通用 Agent | ❌ | ❌ | ✅ OSU | ❌ | ❌ | ❌ |
| **屏幕感知** | ✅ vishot | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **全离线运行** | ❌ | ⚠️ | ⚠️ | ✅ | ⚠️ | ✅ | ❌ | ⚠️ | ✅ |
| **8GB 显存可用** | ❌ | ✅ | ✅ | ⚠️ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **显存动态管理** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ VRAM 级别 |
| **一键安装** | ✅ winget | ✅ | ⚠️ | ❌ | ✅ Docker | ❌ | ❌ | ❌ | ⚠️ setup.ps1 |
| **移动端** | ✅ PWA | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **插件系统** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **NSFW 支持** | ❌ | ✅ | ⚠️ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 三、逐项目深入分析

### 3.1 SillyTavern (30k Stars)
**定位**: LLM 角色扮演前端

**核心优势**:
- 角色卡生态的**事实标准**（PNG/JSON character card format）
- 支持几乎所有 LLM API + 本地后端
- 世界书 (World Info / Lorebooks)、作者注 (Author's Note)
- 群聊 (Group Chat)、多角色同时互动
- 社区驱动的扩展生态

**核心短板**:
- **纯文本前端**——没有语音管道、没有 Live2D、没有画图
- 不自带 LLM——需要用户自行配置后端
- 没有长期记忆（依赖 summarise 插件，简陋）

**Artemis 的定位差异**: Artemis 是"自带 LLM + TTS + 画图 + Live2D 的一体化女友"，SillyTavern 是"前端壳"。Artemis 导入了 SillyTavern 的角色卡格式，但走的是完全不同的路。

---

### 3.2 AIRI (41k Stars)
**定位**: Neuro-sama 开源替代品——全能 AI VTuber 平台

**核心优势**:
- **实时语音对话**: 完整 VAD→STT→LLM→流式 TTS 管线，含 timeline + playback 管理
- **游戏能力**: Minecraft (Mineflayer), Factorio (autorio), KSP, Helldivers 2, DomeKeeper
- **视觉表现**: Live2D + VRM 3D + Spine 三套渲染引擎，口型同步，视线追踪
- **屏幕感知**: vishot 截图→LLM 理解画面，打游戏时能"看到"游戏内容
- **产品质量**: winget/scoop/brew 一键安装，Web/桌面/移动三端
- **LLM 流式控制**: `tokenAct`/`tokenCall`/`tokenDelay` 让 LLM 输出实时指令
- **插件系统**: plugin-sdk + plugin-protocol，可扩展性强
- **TTS chunker**: Intl.Segmenter 分词、grapheme cluster 处理、叙述文本自动剥离
- **社区**: 100+ 贡献者，Crowdin 多语言翻译，Discord/Telegram/QQ/微信

**核心短板**:
- **没有 AI 画图**: 完全不含图像生成
- **不是"女友"**: 定位是 VTuber 表演者，不是一对一亲密关系
- **不支持 SillyTavern 角色卡**
- **非全离线**: 浏览器端推理仍在 WIP
- **NSFW 不友好**: 公开产品不适合成人内容

**Artemis 的定位差异**: 互补关系。AIRI 没有的（画图、角色后宫、SillyTavern 兼容、NSFW、离线）Artemis 有。AIRI 有的（实时语音、游戏、3D、屏幕感知）Artemis 没有。

---

### 3.3 elizaOS (18.6k Stars)
**定位**: Agent 操作系统——AI Agent 框架，不专做角色扮演

**核心优势**:
- 通用 Agent 框架，可接入任何系统
- 插件生态极其丰富（Discord/Twitter/Telegram/区块链/...）
- 多 Agent 协作

**核心短板**:
- **不是角色扮演专用**——没有角色卡、没有 Live2D、没有画图
- 太重——为"AI Agent 平台"设计，与"AI 女友"无关
- 角色扮演是它的一个小用例，体验远不如专用工具

**Artemis 的定位差异**: elizaOS 是工具箱，Artemis 是女友。完全不同。

---

### 3.4 Open-LLM-VTuber (12.2k Stars)
**定位**: 本地运行的全平台 AI VTuber

**核心优势**:
- Live2D + 实时语音 + 本地 LLM
- 跨平台（Windows/macOS/Linux）
- 语音打断 (voice interruption)
- 活跃的中文社区

**核心短板**:
- 没有画图
- 没有角色后宫/角色卡导入
- 没有长期记忆
- UI 偏功能型而非产品型
- 没有对话树

**Artemis 的定位差异**: Open-LLM-VTuber 是"VTuber 工具"，Artemis 是"女友"。前者让你做主播，后者陪你谈恋爱。

---

### 3.5 其余项目简述

- **Streamer-Sales (3.7k)**: 直播带货专用，与女友无关
- **Neuro/kimjammer (2k)**: Neuro-sama 7 天复刻，概念验证，无人维护
- **Amica (1.5k)**: 3D VRM 交互，有 VRM + 语音，更像技术 Demo
- **AI-Waifu-Vtuber (1k)**: Twitch VTuber 专用，功能单一

---

## 四、Artemis 的独特定位：赛道分析

### 当前市场格局

```
              ┌──────────────────────────────┐
              │      AI VTuber / 主播         │
              │  AIRI, Open-LLM-VTuber,      │
              │  Neuro, AI-Waifu-Vtuber      │
              │  (面向观众，表演属性)          │
              └──────────────────────────────┘

  ┌─────────────────────┐    ┌─────────────────────┐
  │   LLM 角色扮演前端    │    │   通用 AI Agent      │
  │   SillyTavern        │    │   elizaOS            │
  │   (纯文本，无AI后端)   │    │   (非角色扮演专用)    │
  └─────────────────────┘    └─────────────────────┘

              ┌──────────────────────────────┐
              │       AI 伴侣 / 女友          │
              │                              │
              │        「空缺」               │
              │   没有开源项目专注这个定位     │
              │                              │
              │   ★ Artemis 在这里 ★         │
              └──────────────────────────────┘
```

### Artemis 的赛道独占优势

| 独占能力 | 说明 | 所有竞品 |
|----------|------|----------|
| AI 画图 (ComfyUI) | NSFW-Illustrious 模型，角色专属画风 | **无人有** |
| 角色后宫切换 | 一键换女友 + 专属音色 + 独立记忆 | **无人有** |
| SillyTavern 角色卡导入 | 兼容最大角色卡生态 | 只有 ST 自己 |
| mem0 长期记忆 | Qdrant 向量搜索 + SmartCrusher 压缩 | **无人有** |
| 对话树/分支 | 重新回复创建分支，可回溯历史 | **无人有** |
| VRAM 级别管理 | 8GB 显卡动态调度 llama/TTS/ComfyUI | **无人有** |
| QQ Bot 接入 | 中国用户核心 IM 渠道 | **无人有** |
| 全离线 + NSFW | 隐私 + 无审查 | 极少数 |

---

## 五、客观评估：能打吗？

### 结论：**现阶段不能正面打，但赛道选对了。**

**不能正面打的原因**:
1. 代码量：AIRI ~9000KB TypeScript + 52 packages，Artemis 核心 ~50KB Python + 单文件前端
2. 产品质量：AIRI 有 winget 安装、PWA 移动端、Crowdin 国际化，Artemis 靠 setup.ps1
3. 语音管道：AIRI 的 pipelines-audio 是工业级（流式 TTS chunker + timeline + playback manager + LLM streaming control），Artemis 是一次性生成 wav
4. 团队: 100+ vs 1
5. 运营: ProductHunt + Discord 万人大群 + OpenCollective + Ko-fi vs 无

**赛道选对了的原因**:
1. **AI 女友不是 AI VTuber**——没有一个 4 万星的项目在做你做的事（画图+后宫+离线+NSFW+亲密关系）
2. **SillyTavern 兼容**是正确决策——借力最大角色卡生态
3. **ComfyUI 画图**是差异化杀器——AI 女友能画图，所有竞品都做不到
4. **164 星 / 满月**证明市场有需求——单人无推广的情况下
5. 如果保持增速，三个月后进入 500-1000 星区间，就已经超过 AI-Waifu-Vtuber 和 Amica 了

### 需要追赶的方向（按优先级）

1. **流式 TTS**: 参考 AIRI 的 `pipelines-audio`（tts-chunker + timeline），让 TTS 边生成边播放
2. **Live2D 口型同步**: model-driver-lipsync 结合音量驱动
3. **前端重构**: ui.js 2800 行单文件已到极限，考虑 Vue/React
4. **前端多端**: PWA 支持移动端
5. **打包分发**: 一键 exe 安装包

### 不需要追的方向

- 游戏能力（Minecraft/Factorio）——与女友定位无关
- VRM 3D 模型——Live2D 更适合二次元女友
- 屏幕感知——女友不需要看你的屏幕
- 30+ LLM 提供商——本地 llama 离线是核心卖点

---

## 六、总结

| 维度 | 评分 | 说明 |
|------|------|------|
| 赛道选择 | ⭐⭐⭐⭐⭐ | AI 女友是蓝海，没有直接竞品 |
| 技术深度 | ⭐⭐⭐⭐ | VRAM管理/SmartCrusher/mem0 有创新 |
| 产品完整度 | ⭐⭐⭐ | 能用但粗糙，缺少流式TTS和好前端 |
| 生态兼容 | ⭐⭐⭐⭐ | SillyTavern 兼容是正确策略 |
| 差异化 | ⭐⭐⭐⭐⭐ | ComfyUI画图 + 后宫 + QQ = 独一份 |
| 增长潜力 | ⭐⭐⭐⭐ | 满月164星，维持斜率可破千 |

**Artemis 不是最强的项目，但是最独特的那一个。**

在"AI 女友"这个细分赛道上，它是唯一一个集成了本地 LLM + ComfyUI 画图 + GPT-SoVITS 语音 + Live2D + 后宫系统 + SillyTavern 兼容 + 全离线 NSFW 的项目。

能打。但不是和大项目正面打，而是在它们覆盖不到的缝隙里，把一件事做到极致。

---

# 2026-08-02 更新：六项目深度源码分析

> 分析方式：本地源码逐项深度分析（airi / Artemis / companion-app / neko / SillyTavern / super-agent-party）
> 详细报告：`2026-08-02-*.md`（本目录，7 份，含总对比）

## 六项目总览（源码核实）

| 维度 | airi | Artemis | companion-app | neko | SillyTavern | super-agent-party |
|---|---|---|---|---|---|---|
| **定位** | 数字生命/灵魂容器 | 100% 本地 AI 女友 | a16z 教学模板 | 赛博猫娘陪伴平台 | LLM 聊天前端工具 | 桌面伴侣+Agent 全家桶 |
| **许可证** | MIT | CC BY-NC 4.0（禁商用） | MIT | Apache-2.0 | AGPL-3.0 | AGPL-3.0 |
| **维护状态** | 非常活跃 | 活跃 | ❌ 停更（2023） | 极其活跃 | 非常活跃 | 非常活跃 |
| **契合度** | 8.5/10 | 9/10 | 参考级 | **9.5/10** | 9/10（工具） | 8/10 |

## 能力矩阵（源码证据）

| 能力 | airi | Artemis | companion-app | neko | SillyTavern | super-agent-party |
|---|---|---|---|---|---|---|
| **LLM 后端** | ★★★★★ 30+ | ★★★★★ 本地+云端 | ★★★☆ | ★★★★★ 14+含免费通道 | ★★★★★ 36 后端 | ★★★★★ |
| **记忆** | ★★☆ 未发布 | ★★★★★ mem0+Qdrant | ★★★☆ 浅 | ★★★★★ 五维记忆 | ★★★★☆ 世界书+RAG | ★★★★☆ mem0+RAG |
| **语音** | ★★★☆ | ★★★★★ GPT-SoVITS+Whisper | ❌ | ★★★★★ 实时语音+克隆 | ★★★★★ 28 TTS | ★★★★★ |
| **虚拟形象** | ★★★★★ Live2D/VRM/MMD | ★★★★☆ Live2D+桌宠 | ❌ | ★★★★★ 五形态+VMC | ★★★★☆ 挂载点 | ★★★★★ VRM/THA/VTS 三套 |
| **Agent** | ★★★★ 游戏/MCP | ★★★★★ OpenClaw+MCP | ★★☆ | ★★★★☆ 电脑操作/MCP/A2A | ★★★★ 工具调用 | ★★★★★ 全功能 |
| **多渠道** | ★★★★★ 全平台 | ★★★★★ QQ/TG/Web | ★★★★ Web+SMS | ★★★★☆ 全渠道+直播 | ★★★★ Web | ★★★★★ 全平台机器人 |

## 与旧版 BENCHMARK 结论的差异

1. **AIRI Star 数修正**：旧版写 41k，源码分析核实为约 1 万+（Trendshift/PH 收录，本地无法精确核实）。
2. **记忆系统**：旧版认为 AIRI 无长期记忆（WIP），本次核实确认其 memory-pgvector/DuckDB 包已有雏形但产品级 Memory Bank 未发布——维持"待落地"判断。
3. **新增项目**：neko（Apache-2.0，五维记忆+实时语音+五形态形象+Steam 生态，综合评分最高 9.5/10）、companion-app（a16z 教学模板，停更）、super-agent-party（AGPL，全渠道 Agent 平台，陪伴内核偏浅）。
4. **Artemis 定位再确认**：在"本地隐私 + 后宫切换 + 全离线 NSFW"维度仍是最强；neko 是综合最强竞品，super-agent-party 渠道最广，airi 形态最完整但记忆未落地。

## 综合排名（AI 陪伴场景契合度）

1. 🥇 **neko 9.5/10** — 功能密度+工程化+生态闭环综合最强
2. 🥈 **Artemis 9/10** — 本地隐私场景最优（契合度满分但门槛高）
3. 🥈 **SillyTavern 9/10** — 前端工具标杆（定位不同，生态为王）
4. 🥉 **airi 8.5/10** — 形态上限最高，记忆未落地
5. **super-agent-party 8/10** — 全渠道 Agent 平台，陪伴内核偏浅
6. **companion-app 参考级** — 教学模板，停更不可上线

**结论**：Artemis 的"本地女友"缝隙定位依旧成立；若要与 neko 正面竞争，优先级是补实时语音链路与更深的记忆分层（facts→reflections→persona 模式可借鉴）。
