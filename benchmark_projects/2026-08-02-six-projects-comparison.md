# AI 陪伴项目六强横向对比报告

> 分析日期：2026-08-02 | 分析对象：airi / Artemis / companion-app / neko / SillyTavern / super-agent-party
> 依据：`reports/` 下六份独立深度报告（本地源码 + 官方文档，未联网核实 Star 数）

---

## 1. 总览对比

| 维度 | airi | Artemis | companion-app | neko | SillyTavern | super-agent-party |
|---|---|---|---|---|---|---|
| **定位** | 数字生命/灵魂容器（Re-creating Neuro-sama） | 100% 本地 AI 女友 | a16z 教学模板（AI companions with memory） | 数字生命陪伴平台（赛博猫娘） | LLM 聊天前端（Power Users 工具） | AI 桌面伴侣 + Agent 全家桶 |
| **作者/组织** | Moeru AI Project AIRI Team | 个人（TAOTAO777，中文社区） | a16z-infra | Project N.E.K.O. Team | SillyTavern 社区 | heshengtao（LLM-Party 生态） |
| **Star 量级** | ~1万+ | 数十~数百（网盘分发） | 数千（教学明星项目） | 数千~万级（Steam 免费上架） | 万级+（最老牌） | 数千（Trendshift 收录） |
| **许可证** | MIT | CC BY-NC 4.0（禁商用） | MIT | Apache-2.0 | AGPL-3.0 | AGPL-3.0 |
| **维护状态** | 非常活跃（v0.11.3，日更） | 活跃（持续迭代，Windows 向） | ❌ 已停更（2023-09 后无提交） | 极其活跃（v0.8.3，日更+CI 13 workflow） | 非常活跃（v1.18.0） | 非常活跃（v0.4.2，日更级） |
| **核心语言** | TypeScript（pnpm monorepo） | Python + Node + PowerShell | TypeScript（Next.js） | Python 3.11（FastAPI） | JavaScript（Express） | Python 3.12（FastAPI） |
| **契合度评分** | 8.5/10 | 9/10 | 参考用（教学） | 9.5/10（最高） | 9/10（工具标杆） | 8/10 |

## 2. 功能能力矩阵

| 能力 | airi | Artemis | companion-app | neko | SillyTavern | super-agent-party |
|---|---|---|---|---|---|---|
| **LLM 后端** | ★★★★★ 30+ provider（xsai）+本地推理 | ★★★★★ llama.cpp 本地 + DeepSeek/Grok 云端 | ★★★☆ OpenAI/Replicate/托管 agent | ★★★★★ 14+ 商（含免费通道+实时语音 API） | ★★★★★ 26 ChatCompletion + 10 TextCompletion + WebLLM | ★★★★★ OpenAI 兼容/Ollama/Claude/Gemini/litellm |
| **记忆系统** | ★★☆ 包有雏形，产品级未发布 | ★★★★★ mem0+Qdrant 双语言+角色隔离 | ★★★☆ Redis 30 条 + 向量 top3（浅） | ★★★★★ 五维记忆（近期/事实/反思/人格/工作）+BM25+向量混合 | ★★★★☆ 世界书+总结+向量 RAG+作者注 | ★★★★☆ mem0+faiss+BM25 知识库 |
| **角色定义** | ★★★★ 角色卡全字段 | ★★★★★ SOUL/IDENTITY+harem 50+ 角色+ST 卡导入 | ★★★★ 文件驱动 preamble/seedchat/backstory | ★★★★★ 每角色独立会话管理器+角色卡 | ★★★★★ 角色卡 V2+世界书+群聊 | ★★★★ 人设+酒馆卡+多角色 |
| **语音 TTS** | ★★★★ 多 provider+lipsync | ★★★★★ GPT-SoVITS 3+声线/4情绪 | ❌ 无 | ★★★★★ 实时语音+多供应商+声音克隆 | ★★★★★ ~28 个 TTS 提供方 | ★★★★★ 多 TTS（edge/elevenlabs 等） |
| **语音 ASR** | ★★★☆ 浏览器/桌面识别（未跑通） | ★★★★★ Faster-Whisper 99 语言 | ❌ 无 | ★★★★★ ASR+端点检测+说话人识别 | ★★★☆ 仅 Extras 可选模块 | ★★★★★ sherpa-onnx 本地 ASR+silero VAD |
| **虚拟形象** | ★★★★★ Live2D/VRM/MMD/Spine/Tachie+Three.js/Godot | ★★★★☆ Live2D 情绪驱动+桌宠 | ❌ 无 | ★★★★★ Live2D/VRM/MMD/PNGTuber/桌宠五形态+VMC | ★★★★☆ Live2D/VRM 挂载+表情系统 | ★★★★★ VRM3D+THA2D+VTS/Live2D 三套 |
| **Agent 能力** | ★★★★ 游戏/屏幕视觉/MCP/HA | ★★★★★ OpenClaw+Claude Code MCP+任务看板 | ★★☆ 仅 Steamship 托管 | ★★★★☆ browser-use/电脑操作/MCP/A2A | ★★★★ 工具调用+扩展系统 | ★★★★★ 任务中心/电脑控制/CDP/MCP/A2A/Skills |
| **多模态** | ★★★☆ 视觉+文生图（部分 WIP） | ★★★★☆ 文/图/语音/动画打通 | ★★☆ 仅输出 block 预留 | ★★★★☆ 图像/屏幕理解/OCR/音乐视频 | ★★★★ SD/ComfyUI+视觉输入 | ★★★★☆ 图片/文档解析/文生图 |
| **多渠道** | ★★★★★ Web/桌面/移动/QQ/Discord/直播/游戏 | ★★★★★ QQ/Telegram/WebChat/终端 | ★★★★ Web + SMS(Twilio) | ★★★★☆ 桌面/浏览器/直播弹幕/QQ/微信/米家 | ★★★★ Web 为主（前端定位） | ★★★★★ QQ/微信/飞书/钉钉/TG/Discord/Slack/B站/直播 |
| **主动性** | ★★★☆ 待机动画/桌面常驻 | ★★★★☆ 桌宠主动关怀 | ❌ 无 | ★★★★★ proactive_chat 主动搭话/热梗/提醒 | ★★★☆ 无强主动（前端工具） | ★★★★☆ 行为引擎定时/周期触发 |

## 3. 部署与上手难度

| 项目 | 终端用户难度 | 开发者难度 | 硬件/依赖门槛 |
|---|---|---|---|
| **airi** | 极易（安装包/winget/scoop） | 高（巨型 monorepo） | 需 LLM API Key；可选后端 docker-compose |
| **Artemis** | 中（一键脚本+向导） | 高（8 个常驻服务） | 8GB+ 显存、32GB 内存、~32GB 模型下载 |
| **companion-app** | 中（教程详尽） | 中 | 6+ 付费第三方（Clerk/OpenAI/Pinecone/Upstash/Twilio） |
| **neko** | 极低（解压即用+免费 LLM 通道） | 中高（多进程+uv 依赖面大） | 低配可跑，高级功能需 GPU/模型 |
| **SillyTavern** | 中（配置项极多） | 中 | 自备 API Key 或本地模型 |
| **super-agent-party** | 极易（便携版双击） | 中（630KB 单体+60 模块） | 需 LLM API Key 或 Ollama；桌面需 Win10/11 |

## 4. 各自最强项 & 短板

| 项目 | 最强项 | 最大短板 |
|---|---|---|
| **airi** | 数字生命形态最完整（形象+多端+游戏陪伴），工程与社区顶级 | 记忆系统未发布，大量功能 WIP/半成品 |
| **Artemis** | 全本地隐私+功能密度（多角色/记忆/TTS/Live2D 全栈） | CC BY-NC 禁商用、硬件门槛高、架构复杂 |
| **companion-app** | 教学价值（最小闭环示范：角色文件化→记忆→LLM→多渠道） | 已停更、依赖全过时、陪伴体验简陋（无语音无形象） |
| **neko** | 综合最强：五维记忆+实时语音+五形态形象+插件生态+Steam | 依赖面大、源码部署复杂、免费通道质量待验证 |
| **SillyTavern** | 生态最成熟：角色卡/世界书/后端兼容/插件最多 | 仅前端工具、AGPL 传染性、新手门槛高 |
| **super-agent-party** | 开放性与渠道最广：OpenAI 兼容 API+MCP+A2A+全平台机器人 | 陪伴内核浅（好感度靠标签解析）、AGPL、单体难维护 |

## 5. 选型建议

- **想要"开箱即用的完整陪伴"** → **neko**（免费通道+Steam 生态+综合最强）或 **super-agent-party**（便携版+全渠道）
- **追求隐私/离线/本地运行** → **Artemis**（全本地零 API，需 8GB+ 显存）
- **追求"数字生命"形态与多端常驻** → **airi**（形态最完整，等记忆模块落地）
- **追求角色卡生态与模型兼容性** → **SillyTavern**（最强前端工具，需自备模型）
- **学习架构/快速搭建原型** → **companion-app**（教学蓝本，勿直接上线）
- **混合方案（推荐）**：**Artemis/neko 做陪伴主引擎 + SillyTavern 做角色卡/世界书生态**，airi/super-agent-party 按渠道需求补充

## 6. 综合排名（AI 陪伴场景契合度）

1. 🥇 **neko 9.5/10** — 功能密度+工程化+生态闭环综合最强
2. 🥈 **Artemis 9/10** — 本地隐私场景最优，契合度满分但门槛高
3. 🥈 **SillyTavern 9/10** — 前端工具标杆（定位不同，生态为王）
4. 🥉 **airi 8.5/10** — 形态上限最高，记忆未落地
5. **super-agent-party 8/10** — 全渠道 Agent 平台，陪伴内核偏浅
6. **companion-app 参考级** — 教学模板，停更不可上线
