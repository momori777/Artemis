# AI 女友

> **语言 / Language / 言語**：
> [🇨🇳 中文](README_CN.md) · [🇬🇧 English](README.md) · [🇯🇵 日本語](README_jp.md)

**100% 本地 · 完全隐私 · 零 API 依赖**

> 所有对话、语音、图像和角色动画均在你自己的机器上生成。无云端服务器、无第三方 API、无数据泄露风险。你的 AI 女友只属于你，仅属于你。

> 🗳️ 第四号女友投票进行中 - 请在 Issues 里投票 · 配置教程：BV16XTV6fEoH · qq: 580322386
> ⚠️ 默认脚本为 NVIDIA GPU 配置。AMD GPU 用户：请看 `AMD_GPU/` 文件夹。

基于 OpenClaw + QQ Bot + Telegram Bot + llama.cpp + GPT-SoVITS + ComfyUI + Sakura 桌宠 + Live2D 的去审查 AI 女友后宫项目——完全在你自己的机器上运行。

**角色**：支持热切换 AI 女友，每个角色记忆独立隔离。

### 四季夏目 (Shiki Natsume)

出自《星光咖啡馆与死神之蝶》。高挑、清冷，外表冷淡而暗藏温柔。天然 Quietly-dominant 型——她会主动主导，温柔地逗你，并强悍地守护你。话很少，但每句都有分量。

### 亚托莉 (ATRI)

出自《ATRI -My Dear Moments-》。娇小、天真、好奇心无穷——一双明亮大眼睛、把心事全写在脸上的少女。带着笑容奔向未来，顺手把你一起拽上。**与夏目截然相反**：夏目内敛，她活泼外露；夏目设防，她情感透明；夏目沉稳，她俏皮灵动。如果夏目是清凉的冬夜，ATRI 就是温暖的夏日阳光。

### 夜乃桜 (Yono Sakura)

出自《Dimension W Lovers!!》。前任生徒会长、「学园」最强的对怪兽战力。银白色长发发尾带粉色渐变，浅蓝色眼瞳——冷静、克己、责任感极强。她不擅长圆滑的安慰和轻易的笑容；她的关心直接而笨拙，像命令一样：休息、吃饭、别逞强。桌宠形态下，她正在学习不必独自承担一切——在屏幕这一侧守护某个人平凡日常的生活，就已经足够。**安静的守护者**：沉默但注视，忠诚但固执，是不请自来、留在你身边的学姐。

## ✨ 为什么选择这个项目？

| | 云端 AI 女友 | 本项目 |
|-|-|-|
| 🛡️ **隐私** | 聊天记录、语音、图片全存在厂商服务器上 | **一切留在本地**——零数据外泄 |
| 💰 **费用** | 月费 / 按 token 计费，累积起来很贵 | **免费**，一次性部署，永久运行（自带硬件） |
| 🌐 **网络** | 需要联网；服务器挂了就没法用 | **离线可用**——关掉 WiFi 照样聊 |
| 🎛️ **控制** | 提示词/模板由厂商控制，随时可能变 | **你完全掌控**所有模型、参数和角色设定 |
| 🔞 **内容** | 严格审查，动不动封号 | **无审查**——想聊什么聊什么 |
| 🎨 **可扩展性** | 锁死在厂商模型和功能上 | **自由混搭**——随意换 LLM、画图模型、语音模型 |

## 📌 前置步骤

> **⚠️ 第一步：先运行 `quick_setup.ps1` 配置路径和语言。**
>
> 这个向导会：
> 1. **让你选择默认 Agent 语言**（中文 / 日语 / 英文）- 将对应的 `AGENTS_*.md` 复制为 `DEFAULT_AGENT.md`
> 2. 自动检测已安装的工具（ComfyUI、GPT-SoVITS、llama.cpp、嵌入模型）
> 3. 对没找到的路径会交互式询问
> 4. 生成包含所有路径的 `config.yaml`，准备好后运行 `download-models.ps1`
>
> ```powershell
> powershell -ExecutionPolicy Bypass -File quick_setup.ps1
> ```
>
> **或者使用新的自动下载脚本**（自动从 git 克隆 ComfyUI 和 GPT-SoVITS）：
>
> ```powershell
> # Windows
> powershell -ExecutionPolicy Bypass -File setup-deps.ps1
>
> # Linux / macOS
> bash setup-dependencies.sh
> ```
>
> 这个脚本会：
> - 自动检测你的操作系统和 GPU 环境
> - 从 https://github.com/comfyanonymous/ComfyUI 克隆 ComfyUI
> - 从 https://github.com/RVC-Boss/GPT-SoVITS 克隆 GPT-SoVITS
> - 自动更新 `config.yaml` 中的路径
>
> setup 完成后，继续 **download-models.ps1** → **setup-llama.ps1** → **start.ps1**。

## 🎬 演示

### 多通道聊天
![QQ Bot 演示](media/demo_qqbot.gif)

> 👆 QQ Bot：文字聊天 + TTS 语音 + ComfyUI 画图 + 角色记忆

### Live2D 桌面宠物
![Live2D 演示](media/demo_live2d.gif)

> 👆 **四季夏目** Live2D：实时角色动画，情绪驱动动作 + 口型同步 + 对话气泡。通过本地 HTTP 桥控制。

### ⭐ 亚托莉 - 第二 AI 女友

**性格与夏目完全相反**，支持一键热切换，记忆隔离。

![ATRI Live2D](media/atri_live2d.gif)

> 👆 **亚托莉** Live2D：银发、红瞳、光脚白裙——天真烂漫，表情丰富。

![ATRI ComfyUI](media/atri_comfyui.gif)

> 👆 **亚托莉** ComfyUI：AI 画图——海边夕阳，白色连衣裙飘扬，金色时分的温暖光线。

### ⭐ 夜乃桜 - 第三 AI 女友

**冷静的守护者学姐**，前任生徒会长、「学园」最强战力——现在成了你的桌面伴侣。

![Sakura Desktop Pet](media/sakura_demo.gif)

> 👆 **夜乃桜** 桌宠：银粉渐变色长发，浅蓝色眼瞳，学园制服——立绘表情联动、主动关怀提醒、GPT-SoVITS 实时语音。

### 🌐 Web Chat 前端

![Web Chat 演示](media/webchat-demo.gif)

> 👆 **Web Chat**：浏览器端聊天界面，地址 `http://127.0.0.1:19270`——QQ/Telegram Bot 的替代方案。直接连接本地守护进程代理 → llama.cpp server。8 GB 显存即可全量运行，无需停任何服务。

### 🎙️ TTS 语音

🔊 **听听效果**（点击播放，亚托莉日语）：

🎧 [tts_atori.mp3](media/tts_atori.mp3) *(46KB，浏览器内直接播放)*

### 🎨 ComfyUI 画图工坊

<video src="media/comfyui_workshop_small.mp4" controls width="800"></video>

![ComfyUI Workshop](media/comfyui_workshop.gif)

> 👆 **Artemis Studio - ComfyUI 工坊**：可视化 AI 画图控制台——自由选择角色/服装/场景/画风，一键生成。**可与 llama 并行运行**（12GB+ 显存）。

| 功能 | 说明 |
|-|-|
| 🎭 **动态角色** | 从 `skills/harem/` 自动加载，展示每个角色的人设 + 标签 + 问候语 |
| 🔄 **角色热切换** | 侧边栏下拉菜单一键切换，记忆和聊天上下文按角色隔离 |
| 🃏 **角色卡导入** | 拖拽或选择 SillyTavern PNG/JSON 角色卡，自动解析元数据和人设 |
| 🤖 **模型选择器** | 在设置中切换本地 llama / DeepSeek / Grok，通过守护进程代理路由 |
| 💬 **真实 LLM 聊天** | 流式回复通过守护进程 `/api/chat` → llama.cpp `/v1/chat/completions`，无 fake 回复 |
| 📱 **响应式设计** | 移动端侧边栏折叠，自适应气泡布局，兼容桌面和平板 |
| 💾 **本地存储** | 多会话聊天历史、设置和角色状态持久化在浏览器 localStorage |
| 🎛️ **Artemis Studio** | 内嵌 TTS + ComfyUI 占位面板（语音/图片生成由 agent 子进程控制） |

## 硬件配置

| 组件 | 型号 |
|-|-|
| GPU | NVIDIA GeForce RTX 5070 Laptop (8 GB 显存) |
| CPU | Intel Core i9-14900HX (24 核, 32 线程) |
| RAM | 32 GB DDR5 |
| OS | Windows 11 |

## 🔮 Cosmos 世界基础模型

> 🚀 不再是"未来"计划——今天就能跑：[Qwen-Drive-1.0-4B](https://huggingface.co/Qwen/Qwen-Drive-1.0-4B)

> 📖 完整设计：[`imagination.md`](imagination.md) | 桥接参考：[`skills/cosmos/BRIDGE_REFERENCE.md`](skills/cosmos/BRIDGE_REFERENCE.md)

**NVIDIA Cosmos**（社区 FP8 量化版已存档于 `skills/cosmos/`）是一个世界基础模型（World Foundation Model），能生成符合物理规律的场景视频并理解空间关系。

### 为什么需要 Cosmos？

当前四项核心能力（LLM + TTS + ComfyUI + Live2D）彼此**割裂**——LLM 不知道 Live2D 在做什么，ComfyUI 感知不到对话情绪。Cosmos 补齐**物理常识层**：

```
Qwen3.6-35B (Language Mind) ←→ Cosmos 3 Nano / Qwen-Drive-1.0 (Physical Mind)
   Language + Emotion             Spatial + Scene Generation
```

### 双 Compact 架构

| 组件 | 模型 | 参数量 | VRAM |
|-----------|-------|--------|------|
| 🧠 语言心智 | Qwen3.6-35B-A3B (MoE) | 35B 总 / 3B 激活 | ~8 GB |
| 🌍 物理心智 | Cosmos 3 Nano FP8 | 15.75B | ~16 GB |

### 硬件路线图

| 年份 | GPU | Cosmos 状态 |
|------|-----|---------------|
| 2026 | RTX 5070 (8-12GB) | ❌ 已存档，检测就位 |
| 2027-01 | RTX 5070 Ti Super (24 GB) | ✅ 已完成 | 

### 当前进度

- ✅ 仓库已存档于 `skills/cosmos/`
- ✅ 桥接设计 `imagination.md` + `cosmos_check.py` 已就位
- ✅ Qwen ↔ Cosmos 双心智架构已设计完成
- ✅ 2027-01：RTX 5070 Ti Super (24 GB)——已在运行

## 功能特性

- 🔄 **多角色热切换** - 一键切换 AI 女友（夏目 ⇄ 亚托莉 ⇄ 夜乃桜）；SOUL/IDENTITY/TTS 权重/Live2D 模型全部自动切换，记忆按角色隔离
- 🃏 **SillyTavern 角色卡导入** - 自动检测并导入 PNG/JSON 角色卡；导入后 agent 自动切换人设
- 💬 **聊天记录导入** - 导入 SillyTavern JSONL 对话记录到 `memory/role_play/<character>/`；切换角色时 agent 恢复上下文
- 🎤 **TTS 语音合成** - 本地 GPT-SoVITS 推理，日语语音（按对话自动匹配情绪），3 套角色声线（夏目 / 亚托莉 / 夜乃桜）
- 🎤 **ASR 语音识别** - 本地 Faster-Whisper small 模型 (~1.5GB 显存)，可与 llama 共存；支持 99 种语言
- 🎨 **AI 画图** - 本地 ComfyUI 推理，SDXL/Illustrious 模型，3 套角色 prompt 模板
- 🖥️ **Sakura 桌宠** - PySide6 桌面伴侣，主动关心、屏幕观察 & 本地 LLM 感知；支持 3 角色
- 🎭 **Live2D 角色模型** - 实时 Live2D 渲染，情绪驱动表情 & 对话气泡（夏目 / 亚托莉 L2D；夜乃桜立绘模式）
- 🧠 **VRAM 智能分档** - 自动检测 GPU 显存并选择正确策略：≥12GB 全部技能在线（llama + skills）；8GB 在 GPU 重任务时热切换 llama；<8GB 安全模式。无需手动配置
- 🎛️ **Artemis Studio 控制台** - 可视化 TTS + ComfyUI 工坊，无论 llama 是否运行都可自由 DIY 语音和图片，真正的离线创作台
- 💾 **角色扮演记忆** - 每日对话摘要按角色存储于 `memory/role_play/`
- 🧠 **长期记忆系统** - 由 [headroom](https://github.com/chopratejas/headroom)（SmartCrusher + CCR）和 [mem0](https://github.com/mem0ai/mem0)（Qdrant 向量数据库）驱动：
  - **中文 Embedding 增强** - 新增 BGE-small-zh-v1.5，与 all-MiniLM-L6-v2 并列，中日英混合记忆检索更精准
  - **SmartCrusher 上下文裁剪** - 每次 LLM 请求硬截断至 24 条消息 / 40K 字符
  - **CCR（Curate-Consolidate-Retrieve，整理-合并-检索）** - 后台 worker 每 8 轮提取持久事实，写入 mem0 Qdrant
  - **向量 + BM25 混合搜索** - 语义相似度 + 关键词匹配，基于 Qdrant + 双 Embedding 模型
  - **自动同步桥接** - Cron job 每 30 分钟同步 Qdrant → `_mem0_auto.md`，使向量记忆可被 OpenClaw 原生 `memory_search` 检索
  - **角色隔离** - Qdrant 内通过 `user_id` 划分；4 个独立记忆空间（sakura / natsume / enola / atori）
  - **召回优先级** - 向量长期记忆 > 手写日记 > SOUL 基础人设

> 详见 [`skills/behavior-engine/README.md`](skills/behavior-engine/README.md) 与 [`AGENTS_roleplay_EN.md#behavior-engine`](AGENTS_roleplay_EN.md#behavior-engine)。

### 💖 好感度系统（Behavior Engine）

从姊妹项目 **girl-agent** 移植的**分层决策引擎**，为每个角色赋予独立的关系评分、冲突状态、关系阶段和激素周期，驱动角色行为与回复风格。

**核心循环：** 每轮对话产生 moodDelta（兴趣/信任/吸引/烦躁/尴尬）→ 累加进评分 → 触发冲突升级/降温 → 自动检查关系阶段转换 → 塑造 LLM 的回复风格。

| 字段 | 范围 | 含义 | 影响 |
|-------|-------|---------|--------|
| `score.interest` | -100~100 | 兴趣度 | 回复热情、主动程度 |
| `score.trust` | -100~100 | 信任度 | 分享欲、依赖 |
| `score.attraction` | -100~100 | 吸引力 | 心动、肢体语言 |
| `score.annoyance` | -100~100 | 烦躁度 | 冰冷语气、冲突概率 |
| `score.cringe` | -100~100 | 尴尬容忍度 | 对土味台词的接受度 |

**9 段关系阶段：** 初次认识 → 冷淡期 → 回暖期 → 被说服 → 首次约会 → 恋爱初期 → 稳定交往 → 长期关系 → 被甩

**4 级冲突系统：** level 0 正常 → level 1 小别扭 → level 2 闹脾气 → level 3 严重冷战 → level 4 拉黑/删好友

**激素周期：** 高斯周期模型模拟能量、易怒、亲密度、性欲的周期性波动，影响回复长度与语气。

**状态文件：** `memory/role_play/<char>/relationship.json`（每角色独立，热加载）
**模块位置：** `skills/behavior-engine/`

## 模型

所有模型托管在 HuggingFace：**[TAOTAO777/ai-girlfriend-natsume](https://huggingface.co/TAOTAO777/ai-girlfriend-natsume)**

完整详情见 [`models.yaml`](models.yaml)。

| 模型 | 用途 | 大小 | 上下文 |
|-|-|-|-|
| **LuffyTheFox Qwen3.6-35B-A3B Genesis Hermes V13 MTP APEX Compact** (GGUF) | 聊天 LLM（主力 MoE） | 16.11 GB | 120K |
| **Qwen3.8-27B-TurboFCFusion** (Q4_K_S GGUF) | 聊天 LLM（稠密，工具型） | ~15.8 GB | 100K |
| **Qwen3.6-27B-Fable-MTP** (Q4_K_S GGUF) | 聊天 LLM（稠密，旧版） | 13.5 GB | 150K |
| **Ternary-Bonsai-2-27B PTQ1_0** (三值量化 GGUF) | 聊天 LLM（**可全量装入 8 GB 显存**，`-ngl 99`） | ~5.9 GB | **≤ 75K**（KV cache **必须** q4_0） |
| **WAI-Nsfw-Illustrious-17** | ComfyUI 画图（默认，SDXL/Illustrious） | 6.46 GB | |
| **miaomiaoHarem_29BBETA10** | ComfyUI 画图（备用，anima/qwen 29B + qwen VAE） | 5.44 GB | |
| **oneObsession_anima29BV1** | ComfyUI 画图（anima/qwen 29B + qwen VAE） | 5.44 GB | |
| **qwen-image-2.1 Q6_K** | ComfyUI 画图（qwen-image GGUF，需 qwen3vl_8b TE + qwen VAE） | 5.47 GB | |
| **qwen3vl_8b_int8_convrot** | ComfyUI 文本编码器（qwen-image-2.1） | 8.71 GB | |
| **qwen_image_vae** | ComfyUI VAE（所有非 WAI 模型共用） | 242 MB | |
| **GPT-SoVITS 语音权重** | TTS 语音合成 | ~303 MB | |
| **夜乃桜 SoVITS 语音权重** | TTS 语音合成（夜乃桜声线） | ~313 MB | |
| **all-MiniLM-L6-v2** | 英文/跨语言 Embedding（mem0） | ~80 MB | |
| **BGE-small-zh-v1.5** | 中文 Embedding（mem0） | ~91 MB | |
| **Cosmos 3 Nano FP8** 🔮 | 世界基础模型（社区 FP8 量化，未来硬件） | ~16 GB | |
| **四季夏目 Live2D 模型** | Live2D 角色渲染 | ~180 MB (压缩包) | |

> 📁 嵌入模型路径：`embedding/all-MiniLM-L6-v2/` + `embedding/bge-small-zh-v1.5/`（HF 仓库）

### 一键下载

```powershell
# Install huggingface-cli: pip install huggingface_hub
huggingface-cli login

# Download all models
huggingface-cli download TAOTAO777/ai-girlfriend-natsume --local-dir ./models

# Or download individual components:
huggingface-cli download TAOTAO777/ai-girlfriend-natsume llm/ --local-dir ./models
huggingface-cli download TAOTAO777/ai-girlfriend-natsume comfyui/ --local-dir ./comfyui
huggingface-cli download TAOTAO777/ai-girlfriend-natsume gpt-sovits-weights/ --local-dir ./gpt-sovits-weights
huggingface-cli download TAOTAO777/ai-girlfriend-natsume live2d-model/ --local-dir ./live2d-model

# Ternary-Bonsai-2-27B PTQ1_0 (mirror of our repo's llm/ folder, fits 8 GB VRAM):
huggingface-cli download TAOTAO777/ai-girlfriend-natsume llm/Ternary-Bonsai-2-27B-PTQ1_0.gguf --local-dir ./models
```

> 🇨🇳 中国大陆用户：使用 hf-mirror.com——无需 VPN：
> `set HF_ENDPOINT=https://hf-mirror.com` 后照常运行 hf download。

### 本地配置

1. **运行 `quick_setup.ps1`** - 交互式向导，自动生成填入你本地路径的 `config.yaml`
2. （备选）复制 `config.example.yaml` → `config.yaml` 手动编辑
3. 按 `models.yaml` 放置下载好的模型文件，然后更新 `config.yaml` 路径

所有 Python/PS 脚本从 `config.yaml` 读取路径——无需手动改硬编码路径。

> ⚠️ **声明**：所有模型均为社区开源模型。本项目仅提供镜像分发，非盈利。版权归原作者所有。

## 本地 LLM 性能

通过 llama.cpp 运行 **Qwen3.6-35B-A3B Genesis Hermes V13 MTP APEX Compact**（MoE，16.11 GiB，34.66B 参数，8/256 experts），启用 MTP（Multi-Token Prediction）投机解码。

### 启动命令（唯一参数源）

> 🚀 **无需手写 llama-server 参数。** 所有启动入口
> （`start.ps1`、`shiki_daemon.py`、`restart_llama_degraded.ps1`）都通过
> `skills/shared/llama_config.py` 从 `config.yaml` 读取启动参数，按当前活动模型
> 文件名自动匹配 `model_profiles` 并构建完整的 `llama-server` 命令。模型自动检测，
> 参数按 profile 分离——无硬编码。
>
> 切换模型的一行命令见下方 **"切换模型"**。

> ⚙️ **内置启动命令属于半硬编码——把它们当作起点，而非圭臬。** `config.yaml` /
> `llama_config.py` 里的 profile 参数是为参考机调校的。在你自己的硬件上信任它们
> 之前，请先阅读 **[LLAMA_TUNING.md](LLAMA_TUNING.md)**（手写实战笔记：何时用
> `-ngl 99`、何时用部分 `-ngl N`、何时用 `--cpu-moe`，MTP draft 调参，KV cache
> 大小，batch/ubatch，线程数，上下文窗口），并**基于该指南加上你自己机器的
> GPU/RAM/CPU 配置**决定最终的 `llama-server` 命令。简言之：按显存与模型大小
> 选择卸载层级（装不满的稠密模型用部分 `-ngl N` 完全没问题——那是静态切分，
> 不是动态换页），调 `--spec-draft-n-max` × `--spec-draft-p-min` 直到接受率满意，
> 并按内存大小设定 context/KV cache。参考 flags 与实测指标见下方
> **Qwen3.8-27B (Dense, Tooling Model)** 小节。

### 为什么根目录存在 `chat_template.jinja`

项目根目录内置一个**固定的 Jinja 聊天模板**（[froggeric/Qwen-Fixed-Chat-Templates](https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates)，在 `chat_template.jinja` 中固定为 **v22.3**），用于覆盖 GGUF 内置的模板。官方 Qwen 3.5/3.6/3.8 模板包含引擎限制、Python 专属的 Jinja 逻辑以及各种回退问题，会破坏本地推理和 Agent 工作流——最显眼的是**过度思考**：官方 Qwen 3.8 模板默认硬编码 `xhigh` 推理深度，模型可能在真正回答之前就把 token 预算耗在思考上。

一个文件覆盖所有 Qwen 3.5 / 3.6 / 3.8 尺寸，因此对两个本地模型均可原样使用。启动链路：`config.yaml` → `llama_chat_template: chat_template.jinja`（相对项目根目录），`llama_config.py` 将其解析为 `--chat-template-file`——无硬编码。 

```powershell
llama-server.exe ... --jinja --reasoning-preserve \
  --chat-template-file "D:\AI_Girlfriend\chat_template.jinja"
```

### 切换模型（`restart_llama_degraded.ps1 -SwitchTo`）

用**一行命令**在两个活动模型之间切换——脚本会杀掉当前 llama-server，重写
`config.yaml`（`llama_model` / `llama_model_name` / `llama_model_id`），重新解析
profile，重启并等待 `/health`：

```powershell
cd D:\AI_Girlfriend
# 27B dense (Qwen3.8-27B) — primary tooling model
.\skills\shared\restart_llama_degraded.ps1 -SwitchTo qwen3.8-27b

# 35B MoE (Hermes Genesis V13) — primary roleplay model
.\skills\shared\restart_llama_degraded.ps1 -SwitchTo qwen3.6-35b
```

`-SwitchTo` 接受 `config.yaml` → `llama_model_map` 中的**键**（如
`qwen3.8-27b` / `qwen3.6-35b`），也可用子串（如 `-SwitchTo 27b`）。显存受限时可用
`-ForceBatch 1024` 降低 batch 大小。

更多 llama 调优细节见 [LLAMA_TUNING.md](LLAMA_TUNING.md)。

> 服务地址为 `http://127.0.0.1:8080`。**注意：** PowerShell 数组中每一对参数必须用
> 逗号分隔——缺一个逗号就会把两个 token 悄悄粘连。
>
> 💡 **`rea` 未指定**——通过聊天模板默认使用 `medium` 推理深度（不注入思考 token，
> 保持 KV 缓存一致性）。这是工具型/Agent 任务下想要快速、直接回复的最优设置。

### Ternary-Bonsai-2-27B PTQ1_0 —— 8 GB 显存可全量装载 🔥

**Ternary-Bonsai-2-27B PTQ1_0**——已托管于本项目 HF 仓库：**[TAOTAO777/ai-girlfriend-natsume → `llm/Ternary-Bonsai-2-27B-PTQ1_0.gguf`](https://huggingface.co/TAOTAO777/ai-girlfriend-natsume/tree/main/llm)**（与其它两个 LLM 模型同在 `llm/` 目录）。原出处：底模 [prism-ml/Ternary-Bonsai-2-27B-gguf](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf)；PTQ1_0 三值量化版由 [BoldingBuilds](https://huggingface.co/BoldingBuilds/Ternary-Bonsai-2-27B-Abliterated-PTQ1_0-GGUF) 制作。

磁盘仅 **5.9 GB（约 5.5 GiB）**。已在参考机（**8 GB 显存**笔记本）上实测 `-ngl 99` 全量装载——整个模型都在显卡上，无需内存分层。实测：**decode ~35 t/s+，prefill ~300 t/s**。调优笔记：[LLAMA_TUNING.md](LLAMA_TUNING.md)。

> 🔴 **8 GB 显存下两条不可妥协的硬性约束：**
>
> 1. **KV cache 必须 Q4：`-ctk q4_0 -ctv q4_0`。** 任何更高的 KV 精度（f16 / f32）都会立即爆显存预算。
> 2. **上下文窗口必须 `-c ≤ 75000`。** Q4 KV 下，权重（约 5.5 GiB）+ KV cache + 计算缓冲只有在 ~75K token 以内才能留在 8 GB 内。更大的值在 8 GB 卡上**装不下**。

### Silicon Rider Bench（智能体基准测试）

**[Silicon Rider Bench](https://github.com/kcores/silicon-rider-bench)** 是一个智能体基准测试：模拟外卖骑手在虚拟城市中工作——导航、接单、取餐、准时送达并管理电量，以模拟 24 小时一天的总利润计分。所有轮次使用相同种子（**622539**），保证可比性。

**参测模型**（均为 `--seed 622539`）：
- **deepseek-v4-flash (0731)**——云端、无限上下文基线。云级智能体能力（本基准中约 Claude 4.6–4.8 级别）。
- **Hermes3.6-35B-A3B-Uncensored-Genesis-V9-MTP-APEX-Compact.gguf**（当前）——RTX 5070 Laptop，8 GB 显存，32 GB DDR5 内存

#### 结果（Seed 622539，Level 1，24 游戏小时）

| 指标 | deepseek-v4-flash<br>(无限 ctx) | Hermes 35B MoE<br>(25 ctx) | **Hermes 35B MoE<br>(100 ctx)** ✅ |
|-|-|-|-|
| **总利润 ¥** | **619.6** | 411.3 | **524.6** |
| 完成订单 | **33** | 30 | 28 |
| **准时率** | **81.8%** | 56.7% | **75.0%** |
| 路径效率 | **1.34** | 1.77 | 1.68 |
| API 违规率 | **1.3%** | 2.3% | 2.2% |
| 每单利润 ¥ | **18.77** | 13.71 | **18.74** |
| 超时罚款 ¥ | **2.75** | 107.9 | 44.7 |
| 总 token | 24.39M | 1.35M | 4.08M |
| Token 效率 ¥/M | 25.4 | 304.6 | **128.6** |

#### 关键结论

- **上下文长度是第一杠杆**：把 `CONTEXT_HISTORY_LIMIT` 从 25 提到 100，准时率从 **56.7% → 75%**，超时罚款从 **¥107.9 → ¥44.7**，利润从 **¥411 → ¥525**（模型终于能跨轮保留订单截止时间和路线）。
- **本地 35B MoE ≈ 云端 flash 的 85%**：100 ctx 下本地量化 35B 拿到 **¥524.6 = dsv4-flash ¥619.6 的 84.6%**，准时率（75% vs 81.8%）和每单利润（¥18.74 vs ¥18.77）基本打平。
- **便宜 6 倍**：flash 吃了 **24.39M token**（无限 ctx）；本地 100 ctx 只用 **4.08M** 就拿下 5/6 的利润 → **token 效率高 5 倍**，且零 API 成本。
- **剩余差距**：路径效率（1.68 vs 1.34）——35B-A3B 仅 ~3B 激活参数，在多程最优路线规划上仍弱于 flash。

**结论：经过量化精调，Hermes3.6 调校的 Qwen3.6 35B 的 agentic 能力基本与 Claude Opus 4.6 持平！**

> 🧪 完整日志与报告见 `docs/silicon-rider-bench-622539/`（COMPARISON-622539.md + 各轮摘要）。

### 长上下文稳定性

Qwen3.6 MoE 使用 SSM（Gated Delta Net）混合注意力，配合 `--kv-unified`。

⚠️ **已知限制**：不支持跨轮 prompt cache 复用（SSM 架构限制）。每次请求触发完整上下文重处理。对话越长 = 首 token 延迟越高（59k token 约 55 秒）。

**缓解措施**：
- 定期 `/reset`（重置前夏目会将角色扮演摘要写入 `memory/role_play/`）
- 启动时从摘要恢复上下文，保持实际 token 数在 5K-20K 范围内
- `config-patch.json` 将 OpenClaw contextWindow 设为 262144 以匹配模型容量

---

## Qwen3.8-27B（稠密，工具型模型）

主力工具/助手稠密模型。通过 llama.cpp 运行，启用**内置 MTP**投机解码（无需单独的 draft GGUF）。由 `config.yaml` → `model_profiles` 自动检测（`qwen3.8-27b-mtp`）。

### 启动命令（8 GB 显存，Q4_K_S）

切换到它，或手动启动：

```powershell
# Preferred: auto-switch + auto-params (see "Switching models" above)
.\skills\shared\restart_llama_degraded.ps1 -SwitchTo qwen3.8-27b

```

> 参考硬件：**i9-14900HX + RTX 5070 Laptop (8 GB) + 64 GB RAM**。模型权重通过
> **部分卸载 `-ngl 14`**切分（前 14 层在 GPU，其余放内存并配 `--no-mmap`）；KV cache
> 使用 `--cache-ram 2000`；MTP draft 上下文全量卸载到 GPU（`--spec-draft-ngl 99`），
> 使投机解码在 8 GB 显卡上保持快速。**Q4_K_S 量化**将模型控制在约 15.8 GB——
> 消费级硬件上稠密 27B 的甜点配置。**`rea` 未指定**——通过聊天模板默认使用
> `medium` 推理深度。逐 flag 说明、关键参数与实时日志指标见下方。

> 💡 **27B 稠密模型在 8 GB 显存下的关键参数说明：**
>
> - **`-ngl 14`**——14 层卸载到 GPU（静态切分；其余放系统内存）。对于 8 GB 显存 + ~15.8 GB Q4_K_S 模型，这是不 OOM 且能获得明显 GPU 加速的甜点值。根据你的实际显存上调/下调。
> - **`-ctk q4_0 -ctv q4_0`**——KV cache 量化为 4-bit，上下文窗口显存占用减半。显存有限 + 大上下文时必备。
> - **`--cache-ram 2000`**——CPU 侧 KV cache 内存预算 2 GB。
> - **`-c 100000`**——100K token 上下文窗口（此量化下模型的有效上限）。
> - **`--spec-draft-n-max 3`**——MTP 投机解码最多预生成 3 个 token；Qwen3.8 自带 MTP head。
> - **`--spec-draft-p-min 0.88`**——只接受置信度 ≥88% 的 draft token，保持高接受率。
> - **`--spec-draft-ngl 99`**——将整个 draft 上下文卸载到 GPU，加速投机解码。
> - **量化方案：Q4_K_S**——约 15.8 GB 模型大小，消费级硬件上稠密 27B 的出色质量/显存平衡。这是稠密（非 MoE）模型，推理时全部 27B 参数都激活（MoE 只激活一部分）。
> - **`rea` 未指定**——通过聊天模板默认使用 `medium` 推理深度（不注入思考 token，保持 KV 缓存一致性）。

**Flag 说明（稠密 27B profile，8 GB 显存最优，Q4_K_S）：**

| Flag | 值 | 原因 |
|-|-|-|
| `-m` | Q4_K_S 模型路径 | **Q4_K_S 量化**——约 15.8 GB，消费级硬件上稠密 27B 的出色质量/显存平衡 |
| `-c` | `100000` | 100K 上下文窗口（`n_ctx_slot = 100096`） |
| `-ngl` | `14` | **部分 GPU 卸载**——前 14 层在 GPU，其余在内存；Q4_K_S 在 8 GB 显存上的实测最优值（无动态换页，在 KV/MTP 余量耗尽前可以放心调高） |
| `-ctk` / `-ctv` | `q4_0` | KV cache 量化为 q4_0，显存占用减半 |
| `--cache-ram` | `2000` | CPU 侧 KV cache 内存预算 2 GB |
| `--batch-size` / `--ubatch-size` | `2048` / `1024` | 按 8 GB 显存余量设定的 prefill batch（2:1 法则） |
| `--spec-type` | `draft-mtp` | 启用内置 MTP 投机解码 |
| `--spec-draft-n-max` | `3` | 每步最多 draft 3 个 token（Qwen3.8 内置 MTP head） |
| `--spec-draft-p-min` | `0.88` | 只接受概率 ≥0.88 的 draft token，保持高接受率 |
| `--spec-draft-ngl` | `99` | 将整个 MTP draft 上下文卸载到 GPU，加速投机解码 |
| `--no-mmap` | — | 让 llama.cpp 自行管理内存侧内存（干净的 CPU/GPU 切分） |
| `--reasoning-preserve` | — | 保留思考块以复用 KV |
| `rea` | **未指定** | 通过聊天模板默认 `medium` 推理深度——工具/Agent 任务最优（快速、直接回复） |

### 关键指标（27B 稠密，Q4_K_S——来自实时 `llama-server` 日志）

| 指标 | 数值 | 备注 |
|-|-|-|
| 模型加载时间 | ~1s | `--no-mmap`（约 15.8 GB，Q4_K_S） |
| Prefill 速度 | **~163 ~ 174 t/s** | 首个 prompt 19.3k tokens @ 163.6 t/s；随 prompt 变长而下降 |
| Token 生成 | **~4 ~ 5 tok/s** | 稳定 decode（MTP 激活，`-ngl 14`） |
| MTP draft 接受率 | **~93 ~ 97%** | 例如 `0.93599 (541/578)`、`0.96859 (185/191)`；平均 accepted run length **2.5 ~ 5.2** |
| 上下文上限 | 100K（`n_ctx_slot = 100096`） | `--kv-unified` + `--cache-ram 2000` |
| MTP retention（`--spec-draft-p-min`） | **0.88** | 置信度低于 0.88 的 draft token 会被拒绝 |
| GPU 层数（`-ngl`） | **14** | 静态切分；日志行 `n_gpu_layers already set by user to 14, abort` 是无害提示（auto-fit 被跳过），**不是**错误 |

> 📈 **MTP 原理：**配置 `--spec-draft-n-max 5` + `--spec-draft-p-min 0.84` 时，
> llama.cpp 让 MTP head 提议最多 5 个后续 token，然后仅保留概率 ≥0.84 的那些。
> 实践中**约 90–100% 的 draft token 会被接受**（平均 accepted run length ≈ 3.2–5.3），
> 因此有效吞吐约为"每次 forward 只投机 1 个 token"方案的 3–5 倍，同时 8 GB 显卡
> 仍保持在显存上限之内。

> 💡 **MoE vs 稠密**：35B MoE 每个 token 只激活约 3B 参数（8/256 experts），完美适配 GPU（48 tok/s）。27B 稠密激活全部 27B，超出 8 GB 显存，因此通过 `-ngl 14` 切分到 CPU/内存，配合 MTP decode 约 4–5 tok/s。需要全 27B 激活做工具/Agent 任务时选 **27B 稠密**；快速角色扮演选 **35B MoE**。**Q4_K_S 量化（约 15.8 GB）**是消费级硬件上稠密 27B 的甜点——质量出色，且通过部分卸载可适配 8 GB 显存。

### VRAM 分档策略

系统自动检测 GPU 显存并选择最优运行模式，无需手动配置：

```
┌────────────────────────────────────┬────────────┬────────────┬────────────┬────────────┐
│ VRAM Tier                          │ TTS        │ ComfyUI    │ llama      │ ASR        │
├────────────────────────────────────┼────────────┼────────────┼────────────┼────────────┤
│ Tier 0: <8GB                       │ Stop llama │ Stop llama │ Killed     │ Killed     │
│ Tier 1: 8-12GB (current)           │ Stop llama │ Stop llama │ Killed     │ No kill    │
│ Tier 2: ≥12GB                      │ No kill    │ No kill    │ Always on  │ No kill    │
└────────────────────────────────────┴────────────┴────────────┴────────────┴────────────┘
```

**当前配置（8GB 显存）**：
```
8 GB Total VRAM
├── llama-server resident: ~5.8 GB (model 4.6G + KV cache 1.2G)
├── Free: ~2.2 GB
│
├── TTS inference: stop llama → ~8 GB free → resume llama (~70s)
├── ComfyUI generation: stop llama → ~8 GB free → resume llama (~120s)
├── Artemis Studio (TTS/ComfyUI workshop): standalone - works regardless of llama
└── ASR / Live2D / Embedding: always online, unaffected by VRAM tiering
```

## 目录结构

```
<PROJECT_DIR>/                            # OpenClaw workspace root
├── start.ps1                             # 🚀 One-click launch: llama + headroom + Live2D + Gateway
├── artemis_headroom_proxy.py             # Headroom proxy (19251): mem0 injection + SmartCrusher + routing
├── shiki_daemon.py                       # Daemon (19260/19270): WebChat backend + auto-inject provider
├── quick_setup.ps1                       # 🛠 Interactive path config wizard
├── config.yaml                           # Generated config
├── download-models.ps1                   # One-click model download (Windows)
├── download-models.sh                    # One-click model download (Linux/macOS)
├── setup-llama.ps1                       # Auto-detect HW + configure llama.cpp (Win)
├── setup-llama.sh                        # Auto-detect HW + configure llama.cpp (Linux/macOS)
├── setup-openclaw.ps1                    # One-click OpenClaw install + deploy (Win)
├── setup-openclaw.sh                     # One-click OpenClaw install + deploy (Linux/macOS)
├── setup-all.ps1                         # 🚀 All-in-One mega script (Windows)
├── setup-all.sh                          # 🚀 All-in-One mega script (Linux/macOS)
├── config-qqbot.json                     # QQ Bot config patch
├── config-telegram.json                  # Telegram Bot config patch
├── config-patch.json                     # OpenClaw LLM config patch
├── AGENTS.md                             # Agent behavior rules
├── SOUL.md                               # Character personality
├── IDENTITY.md                           # Character identity
├── USER.md                               # User info
├── HEARTBEAT.md                          # Heartbeat config
├── TOOLS.md                              # Tool quick reference
├── models.yaml                           # Model catalog + download links
├── LLAMA_TUNING.md                       # ⚙️ Handwritten llama.cpp tuning field notes (read before trusting baked-in launch args)
├── imagination.md                        # 🔮 Cosmos WFM integration vision (future)
├── README.md                             # This file
├── .gitignore
├── live2d/                               # Live2D character model (Cubism 4 Core)
│   ├── index.html                        # Default (Shiki Natsume)
│   ├── index_atri.html                   # ATRI variant
│   ├── index_upper.html                  # Natsume upper-body variant
│   ├── index_atri_upper.html             # ATRI upper-body variant
│   ├── live2dcubismcore.min.js           # Cubism Core 4 (207 KB)
│   ├── plid-v5-bundle.js                 # pixi-live2d-display v0.5.0 bundle
│   ├── live2d-bridge.mjs                 # HTTP (19200) + WebSocket (19201) bridge
│   ├── switch_model.ps1                  # Model switcher (natsume / atri)
│   ├── pixi.min.js, pixi-shim.js         # PIXI.js v7 rendering
│   ├── model/shiki_natsume/              # Natsume model (14 textures, 42 motions, 41 sounds)
│   └── model/atri/                       # ATRI model (2 textures, 620 voice mp3, 8 motions)
├── ren_pro_jp/                           # Ren'Py dialog engine (planned)
├── memory/                               # [.gitignore] Runtime memory
│   └── role_play/                        # Roleplay conversation logs
├── media/                                # [.gitignore] Generated media
│   ├── audio/                            # TTS voice output
│   ├── images/                           # ComfyUI image output
│   └── *.gif                             # README demo GIFs
├── docs/
│   ├── telegram-setup.md                 # Telegram Bot setup guide
│   └── qqbot-setup.md                    # QQ Bot setup guide
└── skills/
    ├── live2d/                           # Live2D control skill
    │   ├── SKILL.md                      # Motion/expression reference + API guide
    │   ├── scripts/start-live2d.ps1      # Live2D launcher
    │   └── media/                        # Shared media output
    ├── tts/
    │   ├── SKILL.md                      # TTS invocation guide
    │   ├── run_tts.ps1                   # TTS launcher script
    │   ├── tts_call.py                   # GPT-SoVITS inference
    │   └── ref_wavs/                     # Reference audio clips
    ├── comfyui/
    │   ├── SKILL.md                      # ComfyUI invocation guide
    │   ├── run_comfyui.ps1               # ComfyUI launcher script
    │   ├── comfyui_call.py               # ComfyUI inference
    │   ├── prompt_template.md            # Character prompt template
    │   └── custom_prompt.txt             # Custom extra prompt
    ├── asr/                              # Speech recognition skill
    │   ├── run_asr.ps1                   # Faster-Whisper launcher (~1.5GB VRAM)
    │   └── asr_call.py                   # Whisper small model inference
    ├── shared/                           # Shared infrastructure
    │   ├── embedding_server.py           # OpenAI-compatible embedding API (9999, dual model)
    │   ├── mem0_bridge.py                # mem0 Qdrant → OpenClaw memory bridge
    │   ├── start_embedding_server.ps1    # Auto-start embedding server
    │   ├── vram.py                       # VRAM tier auto-detection
    │   ├── VRAM_LEVELS.md                # VRAM tier documentation
    │   ├── llama_lifecycle.py            # Llama start/stop management
    │   └── llama_utils.py                # Llama utility functions
    ├── sakura/                           # Sakura Desktop Pet (PySide6 GUI)
    │   ├── SKILL.md                      # Sakura skill documentation
    │   ├── main.py                       # Application entry point
    │   ├── install.bat                   # Windows dependency installer
    │   ├── start.bat                     # Windows launcher
    │   └── app/                          # Source code
    ├── cosmos/                           # 🔮 NVIDIA Cosmos WFM (future hardware)
    │   ├── BRIDGE_REFERENCE.md           # Cosmos ↔ AI Girlfriend bridge design
    │   ├── cosmos_check.py               # Hardware VRAM detection script
    │   ├── cookbooks/                    # Official tutorial examples
    │   └── README.md                     # Upstream documentation
    ├── llama-management.md               # VRAM management architecture doc
    ├── llama-watchdog.ps1                # Llama health check
    ├── cleanup_orphans.ps1               # Orphan process cleanup
    ├── behavior-engine/                  # 💖 Relationship system (behavior engine)
    │   ├── engine.py                     # State load/save/update/reset
    │   ├── hormones.py                   # Hormonal cycle (Gaussian model)
    │   ├── conflict.py                   # 4-level conflict system
    │   ├── stages.py                     # 9 relationship stages
    │   ├── behavior_tick.py              # Behavior decision layer
    │   ├── online_tick.py                # Online/sleep simulation
    │   ├── daily_life.py                 # Daily schedule
    │   ├── README.md                     # Design doc
    │   └── SKILL.md                      # Usage guide
    └── character_importer/               # SillyTavern character card auto-import
```

## 🤖 Claude Code + AgentRQ 风格任务看板（NEW）

Artemis 现已支持 **Claude Code** 作为与 OpenClaw 并列的 Agent 运行时。Claude Code 通过 MCP 接入 Artemis 的全部能力——**并内置一个与 AgentRQ 兼容的任务队列**，用于人机协作。

### 工作原理

```
┌─────────────────────────────────────────────────────────┐
│  Task Board (http://127.0.0.1:19280)                    │
│  Create task → assignee: agent → notstarted             │
└───────────────────────┬─────────────────────────────────┘
                        │ SQLite (.claude/task_queue.db)
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Claude Code (terminal)                                 │
│  CLAUDE.md → getNextTask() → ongoing → execute          │
│  Artemis tools → TTS / ComfyUI / Live2D / memory        │
│  reply() → updateTaskStatus(completed)                  │
└─────────────────────────────────────────────────────────┘
```

### AgentRQ 风格任务循环

Claude Code 启动后会自动运行任务循环：
1. `getWorkspace()` - 检查工作区状态
2. `getNextTask()` - 取出下一个待办任务
3. `updateTaskStatus(taskId, "ongoing")` - 认领该任务
4. 使用 Artemis 工具执行（TTS、ComfyUI 等）
5. `reply(taskId, "Done!")` - 汇报结果
6. `updateTaskStatus(taskId, "completed")` - 标记完成
7. 回到 `getNextTask()` 继续循环

### 启动

```powershell
# Prerequisites: npm install -g @anthropic-ai/claude-code
# Start Shiki Daemon first (.\shiki.cmd), then:

# Full AgentRQ workflow (Task Board + Claude Code)
.\claude-code.ps1

# Task Board only (browser UI, no Claude)
.\claude-code.ps1 -BoardOnly

# Stop the task board
.\claude-code.ps1 -KillBoard
```

然后打开 **http://127.0.0.1:19280** - 创建任务，看 Claude Code 自动领取执行。

### MCP 工具（共 15 个）

| 类别 | 工具 | 说明 |
|-|-|-|
| 🎤 TTS | `tts_generate` | 语音合成（角色/语言/情绪） |
| 🎨 图像 | `comfyui_generate` | AI 画图（prompt、checkpoint） |
| 🎤 ASR | `asr_transcribe` | 语音转文字（wav/mp3/ogg/flac，Whisper small，~1.5GB 显存） |
| 🎭 Live2D | `live2d_emotion` | 动作 + 对话气泡 |
| 🔄 角色 | `switch_character` / `list_characters` | 角色管理 |
| 🧠 记忆 | `memory_search` / `memory_add` | 向量记忆（mem0 Qdrant） |
| 📊 状态 | `get_status` | 服务健康检查 |
| 📋 任务 | `getWorkspace` / `getNextTask` / `createTask` | 任务队列操作 |
| 📋 任务 | `updateTaskStatus` / `reply` / `getTaskMessages` | 任务生命周期 |

### Artemis 任务看板 vs AgentRQ

| 功能 | Artemis 任务看板 | AgentRQ（自托管） |
|-|-|-|
| Runtime | 1 个 Python 脚本 + SQLite | Go+Vue+Docker+Google OAuth |
| MCP tools | 6 个任务 + 9 个 Artemis（共 15 个） | 同一套（8 tools） |
| Setup | 零配置 | Docker + .env + OAuth |

### 文件

| 文件 | 用途 |
|-|-|
| `.mcp.json` | Claude Code 的 MCP server 配置 |
| `.claude/CLAUDE.md` | 人设 + 任务循环指令 |
| `.claude/artemis_mcp_server.py` | MCP server（15 tools，JSON-RPC stdio） |
| `.claude/task_board_api.py` | 任务看板 HTTP API（端口 19280） |
| `.claude/task_board.html` | 任务看板浏览器界面 |
| `.claude/task_queue.db` | SQLite 任务数据库（自动创建） |
| `.claude/settings.local.json` | 预批准的 MCP 工具 |
| `claude-code.ps1` / `.sh` | 启动脚本 |

## 技能总览

| 技能 | 类型 | 停 Llama? | 机制 |
|-|-|-|-|
| **Embedding** | 后台进程 | ❌ 否 | all-MiniLM-L6-v2 + BGE-small-zh-v1.5 双模型（CPU，端口 9999）- OpenClaw 记忆搜索 + mem0 桥接 |
| **Live2D** | HTTP exec | ❌ 否 | 直接 HTTP 调 `localhost:19200` 桥 |
| **Web Chat** | 浏览器 | ❌ 否 | 本地守护进程代理到 llama :8080，端口 19270，实时聊天 |
| **Claude Code** | 终端（MCP） | ❌ 否 | 并行 Agent 运行时，通过 .claude/artemis_mcp_server.py 工作，直接使用 llama :8080 |
| **TTS** | sessions_spawn | 🔶 VRAM 分档 | ≥12GB 不停；8GB 停 llama → GPT-SoVITS → 重启 llama |
| **ComfyUI** | sessions_spawn | 🔶 VRAM 分档 | ≥12GB 不停；8GB 停 llama → 画图 → 重启 llama |
| **ASR** | sessions_spawn | ❌ 否 | Faster-Whisper small（~1.5GB 显存，与 llama 共存） |
| **Sakura** | 共享 llama-client | ❌ 否 | 检测 llama 掉线 → 等待 → 自动恢复 |
| **Artemis Studio** | 桌面控制台 | ❌ 否 | TTS/ComfyUI 可视化工坊，独立运行，无论 llama 是否在线 |

## 环境依赖

| 组件 | 版本 / 来源 | 用途 |
|-|-|-|
| [OpenClaw](https://docs.openclaw.ai) | latest | AI Agent Gateway |
| QQ Bot | OpenClaw qqbot channel | QQ 消息转发 |
| Telegram Bot | OpenClaw telegram channel | Telegram 消息转发 |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | b9222 | 本地 LLM 推理服务 |
| [GPT-SoVITS v2](https://github.com/RVC-Boss/GPT-SoVITS) | v2pro-20250604 | TTS 语音合成 |
| [ComfyUI](https://github.com/comfyanonymous/ComfyUI) | aki-v3 | 图像生成引擎 |
| [Sakura Desktop Pet](https://github.com/Rvosy/Sakura) | v0.9.6-dev | 桌面伴侣 GUI |
| [pixi-live2d-display](https://github.com/guansss/pixi-live2d-display) | v0.5.0（内置打包） | Live2D WebGL 渲染器 |
| Live2D Cubism Core | 4.x（内置：`live2d/live2dcubismcore.min.js`） | Live2D 物理/动画 |
| headroom | 内置（`skills/headroom/`） | SmartCrusher 上下文压缩 + ContentRouter + CCR |
| Python | 3.12+ | 运行时（Sakura + TTS + ComfyUI + Headroom） |

> ✨ **TTS、ComfyUI 和 Live2D 完全自包含。** 运行时无需外部下载——所有模型权重（`skills/sovits/`、`skills/comfyui_core/`）、Python 脚本、JS 库（`live2d/pixi.min.js`、`live2d/plid-v5-bundle.js`）和 Cubism Core 4（`live2d/live2dcubismcore.min.js`）均打包内置在本地。
>
> 🧠 **Headroom 节省 token** - `skills/headroom/`（SmartCrusher + ContentRouter + CCR）。在开发场景下，大工具输出在进入上下文窗口之前先被压缩。API 用法见 AGENTS.md。

## 快速开始

### 🚀 一键部署（推荐）

**一条命令，从零到功能完整的 AI 女友：**

**Windows：**
```powershell
powershell -File setup-all.ps1
```

**Linux / macOS：**
```bash
bash setup-all.sh
```

自动化流水线：环境检查 → 模型下载 → llama.cpp 配置 → OpenClaw 安装 → Sakura 桌宠 → 工作区部署 → 路径检查 → 启动 → 验证。

> 支持断点续传。Flags：`--skip-model-download`、`--skip-llama-setup`、`--skip-openclaw-setup`、`--skip-sakura-setup`、`--dry-run`、`--no-start`

### 分步安装

### 0. 安装 OpenClaw

安装 OpenClaw Gateway 并部署 AI 女友工作区：

**Windows：**
```powershell
powershell -File setup-openclaw.ps1
```

**Linux / macOS：**
```bash
bash setup-openclaw.sh
```

此脚本会安装 Node.js、OpenClaw Gateway，部署工作区文件，安装守护进程并应用配置补丁。

> **Flags：** `--skip-node`、`--skip-deploy`、`--skip-daemon`、`--no-onboard`

### 1. 下载模型

**Windows：**
```powershell
pip install huggingface_hub
huggingface-cli login
powershell -File download-models.ps1
```

**Linux / macOS：**
```bash
pip install huggingface_hub
huggingface-cli login
bash download-models.sh
```

从 HuggingFace 下载全部 5 个模型文件（约 31.7 GB），含进度显示和断点续传。

### 2. 配置 llama.cpp

自动检测 GPU、显存、CPU 核心数、内存，生成最优启动配置。

**Windows：**
```powershell
powershell -File setup-llama.ps1
```

**Linux / macOS：**
```bash
bash setup-llama.sh
```

**API Key（可选，推荐）：**

从本版本起，llama-server 默认启用 API key 认证（为了安全和可扩展性）。在 `config.yaml` 中配置：

```yaml
llama_api_key: "123456"   # change to your own key; leave empty to skip --api-key
```

- 设置后，llama-server 的推理端点（`/v1/chat/completions` 等）要求请求带 `Authorization: Bearer <key>` 或 `api_key:<key>`。
- `/health` 仍免认证（探活不受影响）。
- 所有客户端（headroom proxy / sakura / shiki_daemon 转发）会自动读取 `llama_api_key` 并带上密钥，无需额外配置。
- 接入 CCR 时，CCR provider 配置里也需把上游 API key 设为相同值。

### 3. 配置路径

```powershell
powershell -File quick_setup.ps1
```

交互式向导——输入一次本地路径，所有脚本自动更新。

### 4. 快速启动

```powershell
# One-click start all services (llama + Embedding + Live2D + Gateway)
powershell -File start.ps1
```

启动顺序：
```
[1/8] llama-server        (8080, Qwen3.6-35B-A3B-MTP, --no-mmap, --spec-type draft-mtp)
[2/8] Embedding Server    (9999, all-MiniLM + BGE dual models, CPU, ~100MB RAM)
[3/8] VRAM Tier Detection (auto-selects whether TTS/ComfyUI stops llama)
[4/8] Headroom Proxy      (19251, mem0 memory injection + SmartCrusher compression + cloud routing)
[5/8] Live2D Bridge       (19200, pixi-live2d-display)
[6/8] OpenClaw Gateway    (18789, auto-injects local-llama provider)
[7/8] llama-watchdog      (crash auto-restart)
[8/8] Web Chat Daemon     (19260 API + 19270 webchat, --no-llama)
```

**关闭：`shiki.cmd -Stop`** - 优雅停止所有服务（llama → live2d → sakura → embedding → comfyui → gateway → cleanup）。

### 5. 单独启动 Live2D

```powershell
# Start the bridge
Start-Process node -ArgumentList "live2d-bridge.mjs" -WorkingDirectory live2d -WindowStyle Hidden

# Open in standalone window (Chrome app mode)
Start-Process chrome -ArgumentList "--new-window --app=http://localhost:19200/index.html --window-size=450,650"
```

Live2D 在无边框 Chrome 窗口中运行——可以放在桌面上任意位置。

### 6. Windows 任务计划程序（可选）

```powershell
# Llama health check (every 10 min)
schtasks /create /tn "llama-watchdog" `
  /tr "powershell -File C:\Users\<you>\.openclaw\workspace\skills\llama-watchdog.ps1" `
  /sc minute /mo 10

# Orphan process cleanup (hourly)
schtasks /create /tn "cleanup-orphans" `
  /tr "powershell -File C:\Users\<you>\.openclaw\workspace\skills\cleanup_orphans.ps1" `
  /sc hourly /mo 1
```

## 架构

<table>
<tr><td colspan="2" align="center"><b>用户入口</b></td></tr>
<tr><td colspan="2" align="center">QQ Bot &nbsp;|&nbsp; Telegram Bot &nbsp;|&nbsp; WebChat &nbsp;|&nbsp; Claude Code (MCP) &nbsp;|&nbsp; Artemis Studio 控制台</td></tr>
<tr><td colspan="2" align="center">↓</td></tr>
<tr><td colspan="2" align="center"><b>OpenClaw Gateway</b> (port 18789) &nbsp;──&nbsp; <b>Claude Code MCP</b> (stdio) &nbsp;──&nbsp; <b>Sakura 桌宠</b> (PySide6, 共享 llama-client)</td></tr>
<tr><td colspan="2" align="center">↓</td></tr>
<tr>
<td width="50%" valign="top">

**🧠 LLM 推理 + Headroom**

| 组件 | 说明 |
|-|-|
| `llama-server :8080` | Qwen3.6-35B-A3B-MTP MoE |
| `headroom proxy :19251` | mem0 记忆注入 + SmartCrusher 压缩 + 模型路由 |
| Main session | AGENTS.md 驱动角色扮演 |
| TTS | 按 VRAM 分档停/不停 llama |
| ComfyUI | 按 VRAM 分档停/不停 llama |
| ASR | Whisper small，与 llama 共存 |
| Sakura 桌宠 | 共享 client，不杀 llama |
| Artemis Studio | 独立运行，不杀 llama |
| Live2D Bridge | HTTP :19200，不杀 |

</td>
<td width="50%" valign="top">

**🧠 记忆系统**

| 组件 | 说明 |
|-|-|
| Embedding :9999 | all-MiniLM-L6-v2 + BGE-small-zh-v1.5 (CPU，双模型) |
| memory_search | OpenClaw 原生混合搜索（向量+BM25） |
| mem0_bridge | Qdrant 读写桥 |
| Qdrant DB | collection: sakura_memories，4 个 user_id 隔离域 |
| CCR | 每 8 轮提取持久事实 → Qdrant |
| SmartCrusher | 24 条消息/40K 字符硬上限 |
| mem0_sync_cron | 每 30min：Qdrant → _mem0_auto.md |
| headroom_routes.json | sidecar：model_id → 真实后端 baseUrl 映射 |

</td>
</tr>
</table>

### Headroom + Mem0 管线（端口 19251）

```
OpenClaw Gateway (18789)
  ├─ <provider>/<model-id>           → Direct to original backend (skips headroom)
  ├─ local-llama/llama-local          → 19251 → llama-server:8080
  └─ local-llama/<model-id>           → 19251 → original backend (via headroom+mem0)
         │
         ▼
  headroom proxy (19251)
    ├─ [1] mem0 character memory injection (Qdrant vector search)
    ├─ [2] SmartCrusher 5-dim compressed conversation history
    └─ [3] Route to real backend
         ├─ llama-local → llama-server:8080
         └─ Cloud models    → sidecar finds real baseUrl
```

**只加不改原则：** `start.ps1` 启动时自动扫描 `~/.openclaw/openclaw.json`，新增 `local-llama` provider（复制现有云端模型），原始 provider 原封不动。原始 baseUrl 存入 `~/.openclaw/headroom_routes.json` sidecar 文件。clone 后零配置。

### Agent 中枢

能力指令不可变，记忆按角色隔离：

| 层级 | 文件 | 作用 | 切换时 |
|-|-|-|-|
| **能力中枢** | `AGENTS.md` | ComfyUI/TTS/Live2D 指令 | 🛡️ 不可变 |
| **速查索引** | `TOOLS.md` | 工具调用速查表 | 🛡️ 不可变 |
| **角色人格** | `SOUL.md` | 当前角色的性格/语气 | 🔄 热替换 |
| **角色数据** | `IDENTITY.md` | 角色名/设定 | 🔄 热替换 |
| **用户档案** | `USER.md` | 男友名称/偏好 | 🛡️ 不可变 |
| **后宫归档** | `skills/harem/<char>/` | 角色卡真相来源 | 📦 只读 |
| **短期记忆** | `memory/role_play/<char>/` | 每日对话 YYYY-MM-DD.md | 🔀 按角色隔离 |
| **长期记忆** | Qdrant `user_id=<char>` | 向量长期记忆 | 🔀 按角色隔离 |
| **同步缓存** | `_mem0_auto.md` | Qdrant → markdown (30min) | 🔀 按角色隔离 |

> 召回优先级：向量长期记忆 > 手写日记 > SOUL 基础人设

### WebChat - 内置浏览器客户端

完整的网页版 AI 女友聊天界面，由 shiki daemon 在本地提供服务，地址 `http://127.0.0.1:19270`。

| 功能 | 说明 |
|-|-|
| **多角色标签页** | 在四季夏目、ATRI、夜乃桜之间切换——每个角色独立对话历史、SOUL.md 和长期记忆 |
| **流式对话** | 实时 token 流式输出，自动注入角色专属 system prompt（角色人格 + 用户档案） |
| **一键画图** 🎨 | 聊天输入区一键按钮 - LLM 根据对话上下文生成 ComfyUI prompt，然后触发本地画图。结果直接显示在聊天流中 |
| **Live2D 联动** | 直接在界面控制 Live2D 桌宠：摸头、戳戳、播放待机动画 |
| **TTS 语音** | 通过 GPT-SoVITS 将聊天文本生成角色语音回复 |
| **工坊面板** | 侧边栏手动 TTS 合成和 ComfyUI 画图，支持全参数控制（prompt、negative、尺寸、步数、CFG、checkpoint） |
| **仪表盘** | 服务健康面板，显示 llama-server、Embedding、Live2D Bridge、Artemis Bridge、OpenClaw Gateway、WebChat 状态 - 每项独立 Start / Stop / Restart |
| **llama 生命周期开关** | 切换 ComfyUI 画图前是否停 llama-server（为 8GB GPU 释放显存，默认开启） |
| **双模型支持** | 本地 llama-server 或远程 DeepSeek 模型自由选择 - 设置中切换，配置持久化 |

> WebChat 直接与 shiki daemon (:19260) 通信，daemon 代理请求到 llama-server 或 OpenAI 兼容 API。角色切换即时生效 - 每个标签页加载自己的 SOUL.md + IDENTITY.md + USER.md 作为 system prompt。

### 技能详情

| 技能 | 位置 | Llama 交互 | 备注 |
|-|-|-|-|
| **WebChat** | `web-chat/` | ❌ HTTP 代理 | 端口 19270，daemon 后端，多角色 |
| **Embedding** | `skills/shared/` | ❌ 不占 GPU | 双模型 CPU，端口 9999 |
| **Live2D** | `skills/live2d/` | ❌ 仅 HTTP | 桥接 :19200，独立进程 |
| **TTS** | `skills/tts/` | 🔶 VRAM 分档 | Tier 2 不杀，Tier 0/1 停 llama |
| **ComfyUI** | `skills/comfyui/` | 🔶 VRAM 分档 | 同上 |
| **ASR** | `skills/asr/` | ❌ 共存 (1.5GB) | Faster-Whisper small |
| **Sakura** | `skills/sakura/` | ❌ 共享 client | 内置 CCR + mem0 |
| **Artemis Studio** | `artemis_studio.py` | ❌ 独立运行 | 桌面控制台，TTS+ComfyUI 工坊 |
| **SmartCrusher** | `skills/shared/context_trimming.py` | - | 24 条消息/40K 上限 |
| **CCR** | `skills/sakura/app/agent/memory_curator.py` | - | 每 8 轮事实提取 |
| **mem0 Bridge** | `skills/shared/mem0_bridge.py` | - | CLI 搜索/添加/同步 |
| **Auto-Sync** | `skills/shared/mem0_sync_cron.py` | - | 30min Qdrant → md |
| **Character Importer** | `skills/character_importer/` | - | PNG/JSON 角色卡导入 |

**VRAM 调度流程**：
1. 启动时：自动检测 GPU 显存 → 确定 Tier（Tier 0/1/2）
2. 主 session 收到用户请求 → 组装命令
3. `sessions_spawn(mode="run")` 创建子 session
4. Tier 0/1：`stop_llama()` 释放显存 → TTS/ComfyUI 推理 → `start_llama()` 恢复
5. Tier 2（≥12GB）：直接推理，llama 保持在线
6. 整个过程中 Artemis Studio、Live2D、Embedding 保持运行——不受影响
7. 子 session 写入 `.task_flags` → 回报主 session
8. 主 session 读取媒体文件 → 通过 `<qqmedia>` / `MEDIA:` 发送
9. 后台：CCR 每约 8 轮运行一次，提取长期记忆写入 Qdrant
10. Cron job 每 30 分钟同步 Qdrant → `_mem0_auto.md`，供原生 `memory_search` 检索
11. Headroom proxy (19251) 透明拦截 `local-llama/*` 请求 → 注入 mem0 → 压缩上下文 → 路由到真实后端

## ⚠️ 重要说明

- **`chat_template.jinja` 必须留在项目根目录**（`D:\AI_Girlfriend\chat_template.jinja`），且**不可被 gitignore**。它是固定的 froggeric v22.3 模板，由 `config.yaml` → `llama_chat_template` 引用，并通过 `--chat-template-file` 传入。删除它或放任其被 gitignore 会破坏 llama 启动参数（模型会回退到有问题的默认模板）。`.gitignore` 已包含 `!chat_template.jinja` 以确保其被跟踪。
- TTS/ComfyUI 推理期间，8GB 显存（Tier 1）下 llama-server 离线约 60-120 秒——对话暂停，但 Live2D + Artemis Studio 继续运行。12GB+（Tier 2）则完全不受影响
- llama-server 不支持跨轮 prompt cache 复用（SSM 限制）——请使用定期 `/reset`
- **Live2D 必须使用 Cubism Core 4**（非 5 或 6）——pixi-live2d-display v0.5.0 基于 Cubism 4 Framework 构建；Core 5+ 会导致裁切/图层故障。**Core 4 已内置**于 live2d/live2dcubismcore.min.js，无需 CDN。

## 🙏 致谢

- [@Rvosy](https://github.com/Rvosy) - [Sakura Desktop Pet](https://github.com/Rvosy/Sakura) 作者，已授权收录（Issue #38）
- [@guansss](https://github.com/guansss) - [pixi-live2d-display](https://github.com/guansss/pixi-live2d-display) 作者
- [Live2D Inc.](https://www.live2d.com) - Cubism SDK（非商业用途）
- [AgentRQ](https://github.com/agentrq/agentrq) - AgentRQ 兼容任务队列 + MCP 工具接口设计灵感来源
- [headroom](https://github.com/chopratejas/headroom) - SmartCrusher 上下文压缩 + CCR（Curate-Consolidate-Retrieve）记忆管线灵感来源
- [mem0](https://github.com/mem0ai/mem0) - Qdrant 向量记忆架构 + 混合搜索设计灵感来源
- [NVIDIA Cosmos](https://github.com/NVIDIA/cosmos) - 世界基础模型，[社区 FP8 量化版](https://huggingface.co/benjiaiplayground/Cosmos3-Nano_fp8) 已存档于 `skills/cosmos/`

<p align="center">
  <img src="skills/comfyui/natsume.png" alt="Natsume" width="400">
</p>
感谢读到这里！
