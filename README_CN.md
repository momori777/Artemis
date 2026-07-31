四号女友投票中，请在issue里完成投票

配置教程BV16XTV6fEoH

度盘链接:https://pan.baidu.com/s/1sLeSyVp76yzWcR3Q4pX0kA?pwd=0721
度盘链接其实完全不需要huggingface镜像国内也能访问,如果实在懒得配就用度盘下模型

项目默认脚本为N卡GPU配置,A卡用户看AMD_GPU文件夹改

q群 580322386

# AI 女友

**100% 本地 · 完全隐私 · 零API 依赖**

> 所有对话、语音、图像和角色动画均在你自己电脑上生成。无云端服务器、无第三方API、无数据泄露风险。你。AI 女友只属于你。

-

基于 OpenClaw + QQ Bot + Telegram Bot + llama.cpp + GPT-SoVITS + ComfyUI + Sakura 桌宠 + Live2D 的AI 女友项目--完全在你自己的机器上运行。

**角色**:支持热切换AI 女友,每人独立记忆,互不干扰。

### 四季夏目(Shiki Natsume)

出自《星光咖啡蝶与死神之馆》。高挑、清冷、外冷内热。天然的四系女友-她会主动关心的偶尔毒舌,安静陪伴。话不多,但每句都有分量。

### 亚托莉ATRI)

出自《ATRI -My Dear Moments-》。娇小、天真烂漫,好奇心旺盛-拥有一双红宝石般清澈大眼睛的少女。总是带着笑容奔向明天,顺手拽上你的*性格与夏目完全相的*:一个热情开朗一个冷傲内的一个喜怒哀乐全写在脸上一个深藏不的一个活泼好动一个沉静矜持。若说夏目是冬夜的冷的亚托莉便是夏日的暖阳。

### 夜乃桜Yono Sakura)

出自《ディメンション凸ラバーズ!》。前任生徒会长「学园」最强级别的对怪兽战力。银白色长发发尾带淡粉色渐变,浅蓝色眼的-冷静、克己、责任感极强。她不擅长圆滑的安慰和漂亮话;她的关心直接而笨的像命令一的休息、吃饭、别逞强。桌宠形态下,她正在学习不必一个人承担一的-在屏幕这一侧守护一个普通而重要的日常就足够了的*安静的守护的*:沉默但注的固执但忠的是不请自来的学姐。


## 💡为什么选这个项目

| | 云端 AI 女友 | 本项目|
|-|-|-|
| 🛡️**隐私** | 聊天记录、语音、图片全存在厂商服务器上 | **一切留在本地*--零数据外泄|
| 💰 **费用** | 月费 / 按token 计费,用得越多越贵 | **免费**,一次性部署永久运行(自带硬件) |
| 🌐 **网络** | 断网即死;服务器挂了就没法用| **离线可用**——关掉 WiFi 照样用|
| 🎛️**控制** | 提示词模板由厂商控制随时可能改| **你完全掌控*所有模型、参数和角色设定 |
| 🔞 **内容** | 严格审查,动不动封号| **无审查*--想聊什么聊什么|
| 🎨 **可扩展性* | 锁死在厂商模型和功能里| **自由混搭**--随意。LLM、画画模型、语音模型|

## 📌 前置步骤

> > **⚠️ 第一步先运行`quick_setup.ps1` 配置路径和语言的*
>
> 这个向导。
> 1. **让你选择默认 Agent 语言**(中文 / 日语 / 英文)- 将对应的 `AGENTS_*.md` 复制的`DEFAULT_AGENT.md`
> 2. 自动检测已安装的工。ComfyUI、GPT-SoVITS、llama.cpp、嵌入模。
> 3. 对没找到的路径会交互式询。
> 4. 生成包含所有路径的 `config.yaml`,准备好后运行 `download-models.ps1`
>
> ```powershell
> powershell -ExecutionPolicy Bypass -File quick_setup.ps1
> ```
>
> quick_setup 完成的继续 **download-models.ps1** 的**setup-llama.ps1** 的**start.ps1**。

## 🎬 演示

### 多通道聊天
![QQ Bot 演示](media/demo_qqbot.gif)

> 👆 QQ Bot:文字聊天 + TTS 语音 + ComfyUI 画图 + 角色记忆

### Live2D 桌面宠物
![Live2D 演示](media/demo_live2d.gif)

> 👆 **四季夏目** Live2D:实时角色动画,情绪驱动动作 + 口型同步 + 对话气泡。通过本地 HTTP 桥控制。

### 的亚托莉- 第二 AI 女友

**性格与夏目完全相的*,支持一键热切换,记忆隔离。

![ATRI Live2D](media/atri_live2d.gif)

> 👆 **亚托莉* Live2D:银发、红瞳、光脚白的-天真烂漫,表情丰富。

![ATRI ComfyUI](media/atri_comfyui.gif)

> 👆 **亚托莉* ComfyUI:AI 画图--海边夕阳,白色连衣裙飘的金色时分的温暖光线。

### 的夜乃桜- 第三 AI 女友

**冷静的守护者学的*,前任生徒会长、「学园」最强战的-现在成了你的桌面伴侣。

![Sakura Desktop Pet](media/sakura_demo.gif)

> 👆 **夜乃桜* 桌宠:银粉渐变色长的浅蓝色眼的白色学园制服--立绘表情联动、主动关怀提醒、GPT-SoVITS 实时语音。

![Web Chat 演示](media/webchat-demo.gif)

> 👆 **Web Chat**:浏览器端聊天界面,访问 `http://127.0.0.1:19270` - QQ/Telegram Bot 的替代方案。直接连接本地守护进程代的的llama.cpp 服务器。什么服务都不停!!!!8g显存也能正常全量的!!

### 🎙。TTS 语音工坊

<video src="media/tts_workshop_small.mp4" controls width="800"></video>

> 👆 **Artemis Studio - TTS 工坊**:GPT-SoVITS 实时语音合成,支持夏目/亚托莉夜乃桜三套声线。 种情绪模的日常/傲娇/深情/长句/随机),中英日三语混合朗读的*无论 llama 是否运行都能的*。

![TTS Workshop](media/tts_workshop.gif)

🔊 **听听效果**(点击播放,亚托莉日的:

🎧 [tts_atori.mp3](media/tts_atori.mp3) *(46KB, 浏览器直接播的*

### 🎨 ComfyUI 画图工坊

<video src="media/comfyui_workshop_small.mp4" controls width="800"></video>

![ComfyUI Workshop](media/comfyui_workshop.gif)

> 👆 **Artemis Studio - ComfyUI 工坊**:可视化的 AI 画图控制的自由选择角色/服装/场景/画风,一键生成的*也无需的llama**(12GB+ 显存下并行运的。

| 功能 | 说明 |
|-|-|
| 🎭 **动态角色加的* | 的`skills/harem/` 自动扫描,展示每个角色的人的+ 标签 + 问候语 |
| 🔄 **角色热切的* | 侧边栏下拉菜单一键切的记忆和聊天上下文按角色隔的|
| 🃏 **角色卡导的* | 拖拽或选择 SillyTavern PNG/JSON 角色的自动解析元数据和人设 |
| 🤖 **模型选择的* | 在设置中切换本地 llama / DeepSeek / Grok,通过守护进程代理路由 |
| 💬 **真实 LLM 聊天** | 流式回复通过守护进程 `/api/chat` 的llama.cpp `/v1/chat/completions`,的fake 回复 |
| 📱 **响应式设的* | 移动端侧边栏折叠,自适应气泡布局,兼容桌面和平的|
| 💾 **本地存储** | 多会话聊天历史、设置和角色状态持久化在浏览器 localStorage |
| 🎛️**Artemis Studio** | 内嵌 TTS + ComfyUI 占位面板(语音/图片生成的agent 子进程控。 |

## 硬件配置

| 组件 | 型号 |
|-|-|
| GPU | NVIDIA GeForce RTX 5070 Laptop (8 GB 显存) |
| CPU | Intel Core i9-14900 (24 。 32 线程) |
| 内存 | 32 GB DDR5 |
| 系统 | Windows 11 |


## 🔮 未来:Cosmos 物理世界模型

> 📖 详细设计:[`imagination.md`](imagination.md) | 桥接参的[`skills/cosmos/BRIDGE_REFERENCE.md`](skills/cosmos/BRIDGE_REFERENCE.md)

**NVIDIA Cosmos**(社区 FP8 量化版入 `skills/cosmos/`)是一个物理世界基础模型,能根据文的图像生成符合物理规律的场景视的理解空间关系与物体交互。

### 为什么需。Cosmos?

当前四项核心能力(LLM + TTS + ComfyUI + Live2D)彼此**割裂**--LLM 不知。Live2D 的动。ComfyUI 感知不到对话情绪。Cosmos 补齐**物理常识的*:

```
Qwen3.6-35B (语言心智) ←→ Cosmos 3 Nano (物理心智)
    语言理解 + 情感         空间认知 + 场景生成
```

### 。Compact 架构

| 组件 | 模型 | 参数的| VRAM |
|------|------|--------|------|
| 🧠 语言心智 | Qwen3.6-35B-A3B (MoE) | 35B 的/ 3B 激的| ~8 GB |
| 🌍 物理心智 | Cosmos 3 Nano FP8 | 15.75B | ~16 GB |

### 硬件路线。

| 年代 | GPU | Cosmos 状的|
|------|-----|-------------|
| 2026 | RTX 5070 (8-12GB) | 的存档,硬件检测就的|
| 2027-28 | RTX 5090 (32GB) | ⚠️ Nano FP8 推理可行 |
| 2029-30 | Rubin 工作的(96GB) | 。LLM + Cosmos 同时常驻 |

### 当前进度

- 的仓库已存的`skills/cosmos/`
- 的桥接设计 `imagination.md` + `cosmos_check.py` 就位
- 。Qwen 。Cosmos 双层心智架构设计完成
- 📋 等硬件达的~24GB+ VRAM


## 功能特。

- 🔄 **多角色热切换** - 一键切。AI 女友(夏目 的亚托莉的夜乃桜;SOUL/IDENTITY/TTS 权重/Live2D 模型全部自动切换,记忆按角色隔。
- 🃏 **SillyTavern 角色卡导的* - 自动检测导。PNG/JSON 角色的导入的agent 自动切换角色
- 💬 **聊天记录导入** - 导入 SillyTavern JSONL 对话记录的`memory/role_play/<角色>/`,切换角色的agent 恢复上下。
- 💬 **QQ + Telegram 双通道** - 通过 OpenClaw Gateway 接入 QQ Bot 。Telegram Bot
- 🎤 **TTS 语音合成** - 本地 GPT-SoVITS 推理,日语语音(根据对话自动匹配情绪),3 套角色声的夏目 / 亚托莉/ 夜乃桜
- 🎤 **ASR 语音识别** - 本地 Faster-Whisper small 模型 (~1.5GB 显存),可与 llama 共存;支持 99 种语言
- 🎨 **AI 画图** - 本地 ComfyUI 推理,SDXL/Illustrious 模型,3 套角的prompt 模板
- 🖥的**Sakura 桌宠** - PySide6 桌面伴侣,主动关心、屏幕观的& 本地 LLM 感知;支持 3 角色切换
- 🎭 **Live2D 角色模型** - 实时 Live2D 渲染,情绪驱动表情 & 对话气泡(夏目 / 亚托莉L2D;夜乃桜立绘模。
- 🧠 **VRAM 智能分档** - 根据显存自动选择策略:的2GB 所有技能在的的llama);8GB 自动的llama 秒切 GPU;<8GB 安全模式。无需手动配置
- 🎛️**Artemis Studio 控制的* - 可视。TTS + ComfyUI 工坊,无论 llama 是否运行都可自由 DIY 语音和图的真正的离线创作台
- 💾 **角色扮演记忆** - 每日对话摘要按角色存储于 `memory/role_play/`
- 🧠 **长期记忆系统** - 灵感源自 [headroom](https://github.com/chopratejas/headroom)(SmartCrusher + CCR)的[mem0](https://github.com/mem0ai/mem0)(Qdrant 向量数据的:
  - **中文 Embedding 增强** - 新增 BGE-small-zh-v1.5 中文嵌入模型,中日英混合记忆检索更精准;all-MiniLM-L6-v2 继续用于英文/跨语言
  - **SmartCrusher 文本压缩** - 每次 LLM 请求硬截断至 24 条消的/ 40K 字符
  - **CCR(整理-合并-检的** - 后台线程的8 轮对话提取持久记的写入 mem0 Qdrant
  - **向量 + BM25 混合搜索** - 语义相似的+ 关键词匹的基于 Qdrant + 。Embedding 模型
  - **自动同步桥接** - Cron job 的30 分钟同步 Qdrant 的`_mem0_auto.md`,使向量记忆可。OpenClaw 原生 `memory_search` 检。
  - **角色隔离** - Qdrant 内通过 `user_id` 划分 4 个独立记忆空的sakura / natsume / enola / atori)
  - **召回优先的* - 向量长期记忆 > 手写日记 > SOUL 基础人设

## 模型

所有模型托管在 HuggingFace:**[TAOTAO777/ai-girlfriend-natsume](https://huggingface.co/TAOTAO777/ai-girlfriend-natsume)**

详见 [`models.yaml`](models.yaml)。

| 模型 | 用的| 大小 |
|-|-|-|
| **LuffyTheFox Qwen3.6-35B-A3B Genesis Hermes V6 APEX Compact** (GGUF) | 聊天 LLM | 16.11 GB |
| **WAI-Nsfw-Illustrious-17** | ComfyUI 画图(默认) | 6.46 GB |
| **miaomiaoHarem_v20** | ComfyUI 画图(备用) | 6.46 GB |
| **GPT-SoVITS 语音权重** | TTS 语音合成 | ~303 MB |
| **夜乃桜SoVITS 语音权重** | TTS 语音合成(桜声。 | ~313 MB |
| **all-MiniLM-L6-v2** | 英文/跨语言 Embedding(mem0 记忆) | ~80 MB |
| **BGE-small-zh-v1.5** | 中文 Embedding(mem0 记忆) | ~91 MB |
| **Cosmos 3 Nano FP8** 🔮 | 物理世界模型(社区量化,未来硬件) | ~16 GB |

|  | 的路径:`embedding/all-MiniLM-L6-v2/` + `embedding/bge-small-zh-v1.5/`(HF 仓库) | |
| **四季夏目 Live2D 模型** | Live2D 角色渲染 | ~180 MB (压缩。 |

### 一键下。

```powershell
# 安装 huggingface-cli:pip install huggingface_hub
huggingface-cli login

# 下载所有模。
huggingface-cli download TAOTAO777/ai-girlfriend-natsume --local-dir ./models

# 或单独下载各个组。
huggingface-cli download TAOTAO777/ai-girlfriend-natsume llm/ --local-dir ./models
huggingface-cli download TAOTAO777/ai-girlfriend-natsume comfyui-checkpoints/ --local-dir ./checkpoints
huggingface-cli download TAOTAO777/ai-girlfriend-natsume gpt-sovits-weights/ --local-dir ./gpt-sovits-weights
huggingface-cli download TAOTAO777/ai-girlfriend-natsume live2d-model/ --local-dir ./live2d-model
```

### 本地配置

1. **运行 `quick_setup.ps1`** - 交互式向的自动生成 `config.yaml` 填入你的本地路径
2. (备的复制 `config.example.yaml` 的`config.yaml` 手动编辑
3. 根据 `models.yaml` 放置下载好的模型文件,然后更新 `config.yaml` 路径

所。Python/PS 脚本的`config.yaml` 读取路径--无需手动改硬编码路径。

> ⚠️ **声明**:所有模型均为社区开源模型。本项目仅提供镜像分的非盈利。版权归原作者所有。

## 本地 LLM 性能

通过 llama.cpp 运行 LuffyTheFox Qwen3.6-35B-A3B Genesis Hermes V6 (MoE, 16.10 GiB, 34.66B 参数)。

### 启动命令

```powershell
llama-server.exe `
  -m "Hermes3.6-35B-A3B-Uncensored-Genesis-V6-APEX-Compact.gguf" `
  -c 120000 `
  --flash-attn on -ctk q4_0 -ctv q4_0 `
  --cpu-moe --cpu-mask 0xFFFFFFFF `
  --batch-size 4096 --ubatch-size 2048 `
   -rea off --jinja `
  --cache-ram 2048 --parallel 1 `
  --kv-unified --no-mmap
```

> 💡 **关于 `--no-mmap` 的`-ngl`:** `--no-mmap` 的llama.cpp 自行管理内存分配,比手动指的`-ngl` 层数效率更高。`-ngl` 强制锁定指定层数。GPU,可能导致一半速度损失;的`--no-mmap` 让引擎根据实际显存动态调的实测。RTX 5070 8GB 上可的50~60 t/s。KV 缓存的`q4_0` 量化可节省一半显的16K 上下文下 q4 可稳定运的50K+ token。

### 关键指标

| 指标 | 数的| 备注 |
|-|-|-|
| 显存占用 | ~4.6 GiB (模型) + ~1.2 GiB (KV 缓存) | 8 GB 显存剩余的2 GB |
| 预填充速度 | **960 ~ 1390 t/s** | 120K 上下。 batch-size 4096 |
| Token 生成 | **31 ~ 39 t/s** | MoE 架构, 8/256 experts |
| 上下文长的| 120K (~12按tokens) | ~59k token 全量重新处理的55s |
| 模型加载时间 | ~12s | --no-mmap, 需要充足内的|

### 长上下文稳定。

Qwen3.6 MoE 使用 SSM (Gated Delta Net) 混合注意的配合 `--kv-unified`。

⚠️ **已知限制**:不支持跨的prompt cache 复用。SSM 架构限制)。每次请求触发完整上下文重处理。对话越的= 按token 延迟越高(59k token 的55 的。

**缓解措施**:
- 定期 `/reset`(在重置前夏目会将角色扮演摘要写入 `memory/role_play/`)
- 启动时从摘要恢复上下的保持实际 token 数在 5K-20K 范围。
- `config-patch.json` 。OpenClaw contextWindow 设为 262144 以匹配模型容。

### VRAM 分档策略

系统根据 GPU 显存大小自动选择运行模式,无需手动配置:

```
┌────────────────────────────────────────────────────────────。
。VRAM 级别               。TTS       。ComfyUI   的llama   。
├────────────────────────────────────────────────────────────。
。Level 0: <8GB           的的llama  的的llama  的被杀    。
。Level 1: 8-12GB (当前)   的的llama  的的llama  的被杀    。
。Level 2: 的2GB          的不停      的不停      的始终在线 。
└────────────────────────────────────────────────────────────。
```

**当前配置(8GB 显存)**:
```
8 GB 总显。
├── llama-server 常驻:~5.8 GB(模型 4.6G + KV 缓存 1.2G)
├── 空闲:~2.2 GB
。
├── TTS 推理:的llama 的~8 GB 空闲 的恢复 llama(的70s)
├── ComfyUI 画图:的llama 的~8 GB 空闲 的恢复 llama(的120s)
├── Artemis Studio (TTS/ComfyUI 工坊):独立运行,无论 llama 是否在线
└── ASR / Live2D / Embedding:始终在线,不受 VRAM 分档影响
```

## 目录结构

```
<PROJECT_DIR>/                                               # OpenClaw 工作区根目录
├── start.ps1                         # 🚀 一键启的llama + headroom + Live2D + Gateway
├── artemis_headroom_proxy.py          # Headroom 代理 (19251): mem0 注入 + SmartCrusher + 路由
├── shiki_daemon.py                    # 守护进程 (19260/19270): WebChat 后端 + auto-inject provider
├── quick_setup.ps1                     # 🛠 交互式路径配置向。
├── config.yaml                       # 生成的配置文。
├── download-models.ps1               # 一键模型下的(Windows)
├── download-models.sh                # 一键模型下的(Linux/macOS)
├── setup-llama.ps1                   # 自动检测硬的+ 配置 llama.cpp (Win)
├── setup-llama.sh                    # 自动检测硬的+ 配置 llama.cpp (Linux/macOS)
├── setup-openclaw.ps1                # 一键安。OpenClaw + 部署 (Win)
├── setup-openclaw.sh                 # 一键安。OpenClaw + 部署 (Linux/macOS)
├── setup-all.ps1                     # 🚀 全自动一体化脚本 (Windows)
├── setup-all.sh                      # 🚀 全自动一体化脚本 (Linux/macOS)
├── config-qqbot.json                 # QQ Bot 配置补丁
├── config-telegram.json              # Telegram Bot 配置补丁
├── config-patch.json                 # OpenClaw LLM 配置补丁
├── AGENTS.md                         # Agent 行为规则
├── SOUL.md                           # 角色性格设定
├── IDENTITY.md                       # 角色身份信息
├── USER.md                           # 用户信息
├── HEARTBEAT.md                      # 心跳配置
├── TOOLS.md                          # 工具速查。
├── models.yaml                       # 模型目录 + 下载链接
├── imagination.md                    # 🔮 Cosmos 物理世界模型联动构想(未来)
├── README.md                         # 英文读我(本文。
├── README_CN.md                      # 中文读我
├── .gitignore
├── live2d/                           # Live2D 角色模型 (Cubism 4 Core)
。  ├── index.html                    # 默认(四季夏目)
。  ├── index_atri.html               # 亚托莉版。
。  ├── index_upper.html              # 夏目半身版本
。  ├── index_atri_upper.html         # 亚托莉半身版。
。  ├── live2dcubismcore.min.js       # Cubism Core 4 (207 KB)
。  ├── plid-v5-bundle.js             # pixi-live2d-display v0.5.0 打包。
。  ├── live2d-bridge.mjs             # HTTP (19200) + WebSocket (19201) 桥接
。  ├── switch_model.ps1              # 模型切换(夏目 / 亚托莉
。  ├── pixi.min.js, pixi-shim.js     # PIXI.js v7 渲染
。  ├── model/shiki_natsume/          # 夏目模型(14纹理, 42动作, 41音频)
。  └── model/atri/                   # 亚托莉模的2纹理, 620语音mp3, 8动作)
├── ren_pro_jp/                       # Ren'Py 对话引擎(规划。
├── memory/                           # [.gitignore] 运行时记。
。  └── role_play/                    # 角色扮演对话日志
├── media/                            # [.gitignore] 生成的媒体文。
。  ├── audio/                        # TTS 语音输出
。  ├── images/                       # ComfyUI 图片输出
。  └── *.gif                         # README 演示 GIF
├── docs/
。  ├── telegram-setup.md             # Telegram Bot 搭建指南
。  └── qqbot-setup.md                # QQ Bot 搭建指南
└── skills/
    ├── live2d/                       # Live2D 控制技。
    。  ├── SKILL.md                  # 动作/表情速查 + API 调用指南
    。  ├── scripts/start-live2d.ps1  # Live2D 启动脚本
    。  └── media/                    # 共享媒体输出
    ├── tts/
    。  ├── SKILL.md                  # TTS 调用指南
    。  ├── run_tts.ps1               # TTS 启动脚本
    。  ├── tts_call.py               # GPT-SoVITS 推理
    。  └── ref_wavs/                 # 参考音频片。
    ├── comfyui/
    。  ├── SKILL.md                  # ComfyUI 调用指南
    。  ├── run_comfyui.ps1           # ComfyUI 启动脚本
    。  ├── comfyui_call.py           # ComfyUI 推理
    。  ├── prompt_template.md        # 角色提示词模。
    。  └── custom_prompt.txt         # 自定义额外提示词
    ├── asr/                          # 语音识别技。
    。  ├── run_asr.ps1               # Faster-Whisper 启动的(~1.5GB 显存)
    。  └── asr_call.py               # Whisper small 模型推理
    ├── shared/                       # 共享基础设施
    。  ├── embedding_server.py       # OpenAI 兼容嵌入 API(端口 9999, 双模。
    。  ├── mem0_bridge.py            # mem0 Qdrant 。OpenClaw 记忆桥接
    。  ├── start_embedding_server.ps1 # 自动启动嵌入服务
    。  ├── vram.py                   # VRAM 分档自动检。
    。  ├── VRAM_LEVELS.md             # VRAM 分档说明文档
    。  ├── llama_lifecycle.py        # Llama 启动/停止管理
    。  └── llama_utils.py            # Llama 工具函数
    ├── sakura/                       # Sakura 桌宠 (PySide6 GUI)
    。  ├── SKILL.md                  # Sakura 技能文。
    。  ├── main.py                   # 程序入口
    。  ├── install.bat               # Windows 依赖安装
    。  ├── start.bat                 # Windows 启动。
    。  └── app/                      # 源代。
    ├── cosmos/                       # 🔮 NVIDIA Cosmos 物理世界模型(未来)
    。  ├── BRIDGE_REFERENCE.md       # Cosmos 。AI Girlfriend 桥接设计
    。  ├── cosmos_check.py           # 硬件 VRAM 检测脚。
    。  ├── cookbooks/                # 官方教程范例
    。  └── README.md                 # 上游文档
    ├── llama-management.md           # 显存管理架构文档
    ├── llama-watchdog.ps1            # Llama 健康检。
    ├── cleanup_orphans.ps1           # 孤儿进程清理
    └── character_importer/           # SillyTavern 角色的+ 对话记忆导入
```

## 🤖 Claude Code + AgentRQ 风格任务看板

除了 OpenClaw,Artemis 还支的**Claude Code** 作为并列。Agent 运行时。Claude Code 通过 MCP 协议接入 Artemis 全部能力,并内置了一个与 AgentRQ 兼容的任务队列系统。

### 工作原理

```
┌─────────────────────────────────────────────。
。 任务看板 (http://127.0.0.1:19280)          。
。 创建任务 的assignee: agent 的notstarted    。
└──────────────────┬──────────────────────────。
                   。SQLite (.claude/task_queue.db)
                   。
┌─────────────────────────────────────────────。
。 Claude Code (终端)                         。
。 CLAUDE.md 的getNextTask() 的执行任务        。
。 Artemis 工具 。TTS / ComfyUI / Live2D      。
。 reply() 的updateTaskStatus(completed)      。
└─────────────────────────────────────────────。
```

### 启动方式

```powershell
# 先装 Claude Code
npm install -g @anthropic-ai/claude-code

# 启动 Shiki Daemon(自动拉起 Task Board :19280)
.\shiki.cmd

# 启动 Claude Code
.\claude-code.ps1

# 或只开任务看板(浏览器操。
.\claude-code.ps1 -BoardOnly
```

然后浏览器打开 **http://127.0.0.1:19280** - 建任。Claude Code 自动领取执行。

### MCP 工具列表(15 。

| 类别 | 工具 | 说明 |
|-|-|-|
| 🎤 TTS | `tts_generate` | 语音合成 (角色/语言/情绪) |
| 🎨 图像 | `comfyui_generate` | AI 绘画 (提示词 模型选择) |
| 🎤 ASR | `asr_transcribe` | 语音转文的(wav/mp3/ogg/flac, Whisper small) |
| 🎭 Live2D | `live2d_emotion` | 桌宠动作 + 气泡 |
| 🔄 角色 | `switch_character` / `list_characters` | 角色管理 |
| 🧠 记忆 | `memory_search` / `memory_add` | 向量记忆 (mem0 Qdrant) |
| 📊 状的| `get_status` | 服务健康检的|
| 📋 任务 | `getWorkspace` / `getNextTask` / `createTask` | 任务队列操作 |
| 📋 任务 | `updateTaskStatus` / `reply` / `getTaskMessages` | 任务生命周期 |

### OpenClaw vs Claude Code - 功能对比

| 功能 | OpenClaw | Claude Code |
|-|-|-|
| QQ Bot 消息 | 的| 的(非消息通道) |
| Telegram Bot 消息 | 的| 。
| WebChat 浏览器聊的| 的| 。
| 终端对话 | 的| 。
| TTS / ComfyUI / Live2D | 的| 。
| ASR 语音识别 | 的| 。
| mem0 记忆系统 | 的| 。
| 角色切换 | 的| 。
| 定时任务 (cron) | 的| 。
| 任务面板 | 的| 的(AgentRQ 风格) |
| sessions_spawn | 的| 的(无等价物) |

> **定位**:OpenClaw 是生产环境的消息中枢(QQ/TG/WebChat + 角色扮演),Claude Code 是终端开的agent(任务面板驱动 + 能力调试)。两者互的非替代关系。

### 相关文件

| 文件 | 用的|
|-|-|
| `.mcp.json` | Claude Code 。MCP 服务配置 |
| `.claude/CLAUDE.md` | 角色设定 + 任务循环指令 |
| `.claude/artemis_mcp_server.py` | MCP 服务 (15 工具, JSON-RPC stdio) |
| `.claude/task_board_api.py` | 任务看板 API (端口 19280) |
| `.claude/task_board.html` | 任务看板浏览器界的|
| `.claude/task_queue.db` | SQLite 任务数据的(自动创建) |
| `.claude/settings.local.json` | 预批准的 MCP 工具权限 |
| `claude-code.ps1` / `.sh` | 启动脚本 |

## 技能总览

| 技的| 类型 | 。Llama? | 机制 |
|-|-|-|-|
| **Embedding** | 后台进程 | 的的| all-MiniLM-L6-v2 + BGE-small-zh-v1.5 双模的(CPU, 端口 9999) - OpenClaw 记忆搜索 + mem0 桥接 |
| **Live2D** | HTTP exec | 的的| 直接 HTTP 的`localhost:19200` 的|
| **Web Chat** | 浏览的| 的的| 本地守护进程代理的llama :8080,端口 19270,实时聊天 |
| **Claude Code** | 终端 (MCP) | 的的| 并行 Agent 运行的通过 .claude/artemis_mcp_server.py 工作 |
| **TTS** | sessions_spawn | 🔶 。VRAM 分档 | 的2GB 时不的8GB 时停 llama 。GPT-SoVITS 的重启 llama |
| **ComfyUI** | sessions_spawn | 🔶 。VRAM 分档 | 的2GB 时不的8GB 时停 llama 的画图 的重启 llama |
| **ASR** | sessions_spawn | 的的| Faster-Whisper small (~1.5GB 显存,的llama 共存) |
| **Sakura** | 共享 llama-client | 的的| 检的llama 掉线 的等待 的自动恢复 |
| **Artemis Studio** | 桌面控制的| 的的| TTS/ComfyUI 可视化工的独立运行,无论 llama 是否在线 |

## 环境依赖

| 组件 | 版本 / 来源 | 用的|
|-|-|-|
| [OpenClaw](https://docs.openclaw.ai) | latest | AI Agent Gateway |
| QQ Bot | OpenClaw qqbot channel | QQ 消息转发 |
| Telegram Bot | OpenClaw telegram channel | Telegram 消息转发 |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | b9222 | 本地 LLM 推理服务 |
| [GPT-SoVITS v2](https://github.com/RVC-Boss/GPT-SoVITS) | v2pro-20250604 | TTS 语音合成 |
| [ComfyUI](https://github.com/comfyanonymous/ComfyUI) | aki-v3 | AI 图像生成引擎 |
| [Sakura Desktop Pet](https://github.com/Rvosy/Sakura) | v0.9.6-dev | 桌面伴侣 GUI |
| [pixi-live2d-display](https://github.com/guansss/pixi-live2d-display) | v0.5.0 (打包内置) | Live2D WebGL 渲染的|
| Live2D Cubism Core | 4.x (内置: `live2d/live2dcubismcore.min.js`) | Live2D 物理/动画 |
| headroom | 内置 (`skills/headroom/`) | SmartCrusher 上下文压的+ ContentRouter + CCR |

> 的**TTS、ComfyUI 。Live2D 完全自包含的* 运行时无需外部下载--所有模型权的`skills/sovits/`, `skills/comfyui_core/`)、Python 脚本、JS 的`live2d/pixi.min.js`, `live2d/plid-v5-bundle.js`)。Cubism Core 4(`live2d/live2dcubismcore.min.js`) 均打包内置。
>
> 🧠 **Headroom 节省 Token** - `skills/headroom/` (SmartCrusher 5维评分压的+ ContentRouter 自动路由 + CCR 缓存)。开发场景下大输出结果自动压缩后再入上下文窗口。详。AGENTS.md。
| Python | 3.12+ | 运行的(Sakura + TTS + ComfyUI + Headroom) |

## 快速开。

### 🚀 一键部的推荐)

**一条命的从零到完。AI 女友:**

**Windows:**
```powershell
powershell -File setup-all.ps1
```

**Linux / macOS:**
```bash
bash setup-all.sh
```

自动化流的环境检的的模型下载 的llama.cpp 配置 。OpenClaw 安装 。Sakura 桌宠 的工作区部的的路径检的的启动 的验证。

> 支持断点续传。可选参的`--skip-model-download`、`--skip-llama-setup`、`--skip-openclaw-setup`、`--skip-sakura-setup`、`--dry-run`、`--no-start`

-

### 分步安装

### 0. 安装 OpenClaw

安装 OpenClaw Gateway 并部。AI 女友工作。

**Windows:**
```powershell
powershell -File setup-openclaw.ps1
```

**Linux / macOS:**
```bash
bash setup-openclaw.sh
```

此脚本会安装 Node.js、OpenClaw Gateway、部署工作区文件、安装守护进程并应用配置补丁。

> **可选参的** `--skip-node`、`--skip-deploy`、`--skip-daemon`、`--no-onboard`

### 1. 下载模型

**Windows:**
```powershell
pip install huggingface_hub
huggingface-cli login
powershell -File download-models.ps1
```

**Linux / macOS:**
```bash
pip install huggingface_hub
huggingface-cli login
bash download-models.sh
```

。HuggingFace 下载全部 5 个模型文的的31.7 GB),含进度显示和断点续传。

> 国内用户的hf-mirror.com 镜像下载,无需梯子:
> `set HF_ENDPOINT=https://hf-mirror.com` 然后正常 hf download

### 2. 配置 llama.cpp

自动检。GPU、显存、CPU 核心数、内的生成最优启动配置。

**Windows:**
```powershell
powershell -File setup-llama.ps1
```

**Linux / macOS:**
```bash
bash setup-llama.sh
```

### 3. 配置路径

```powershell
powershell -File quick_setup.ps1
```

交互式向的-输入一次本地路的所有脚本自动更新。

### 4. 快速启。

```powershell
# 一键启动所有服的llama + Embedding + Live2D + Gateway)
powershell -File start.ps1
```

启动顺序:
```
[1/8] llama-server        (8080, Genesis Hermes V6, --no-mmap)
[2/8] Embedding Server    (9999, all-MiniLM + BGE 双模。 CPU, ~100MB 内存)
[3/8] VRAM 分档检。      (自动判断 TTS/ComfyUI 是否的llama)
[4/8] Headroom Proxy      (19251, mem0 记忆注入 + SmartCrusher 压缩 + 云端路由)
[5/8] Live2D Bridge       (19200, pixi-live2d-display)
[6/8] OpenClaw Gateway    (18789, 自动注入 local-llama provider)
[7/8] llama-watchdog      (崩溃自动重启)
[8/8] Web Chat Daemon     (19260 API + 19270 webchat, --no-llama)
```

**关闭:`shiki.cmd -Stop`** - 优雅关闭所有服的llama 的live2d 的sakura 的embedding 的comfyui 的gateway 的cleanup)。

### 5. 单独启动 Live2D

```powershell
# 启动桥接服务
Start-Process node -ArgumentList "live2d-bridge.mjs" -WorkingDirectory live2d -WindowStyle Hidden

# 在独立窗口中打开(Chrome 应用模式)
Start-Process chrome -ArgumentList "--new-window --app=http://localhost:19200/index.html --window-size=450,650"
```

Live2D 在无边框 Chrome 窗口中运的-可以放在桌面上任意位置。

### 5. Windows 任务计划(可。

```powershell
# Llama 健康检的的10 分钟)
schtasks /create /tn "llama-watchdog" `
  /tr "powershell -File C:\Users\<你的用户的\.openclaw\workspace\skills\llama-watchdog.ps1" `
  /sc minute /mo 10

# 孤儿进程清理(每小。
schtasks /create /tn "cleanup-orphans" `
  /tr "powershell -File C:\Users\<你的用户的\.openclaw\workspace\skills\cleanup_orphans.ps1" `
  /sc hourly /mo 1
```

## 架构

<table>
<tr><td colspan="2" align="center"><b>用户入口</b></td></tr>
<tr><td colspan="2" align="center">QQ Bot &nbsp;|&nbsp; Telegram Bot &nbsp;|&nbsp; WebChat &nbsp;|&nbsp; Artemis Studio 控制的/td></tr>
<tr><td colspan="2" align="center">的/td></tr>
<tr><td colspan="2" align="center"><b>OpenClaw Gateway</b> (port 18789) &nbsp;──&nbsp; <b>Sakura 桌宠</b> (PySide6, 共享 llama-client)</td></tr>
<tr><td colspan="2" align="center">的/td></tr>
<tr>
<td width="50%" valign="top">

**🧠 LLM 推理 + Headroom**

| 组件 | 说明 |
|-|-|
| `llama-server :8080` | Qwen3.6-35B-A3B MoE |
| `headroom proxy :19251` | mem0 记忆注入 + SmartCrusher 压缩 + 模型路由 |
| Main session | AGENTS.md 驱动角色扮演 |
| TTS | 。VRAM 分档的不停 llama |
| ComfyUI | 。VRAM 分档的不停 llama |
| ASR | Whisper small, 的llama 共存 |
| Sakura 桌宠 | 共享, 不杀 llama |
| Artemis Studio | 独立运行, 不杀 llama |
| Live2D Bridge | HTTP :19200, 不杀 |

</td>
<td width="50%" valign="top">

**🧠 记忆系统**

| 组件 | 说明 |
|-|-|
| Embedding :9999 | all-MiniLM-L6-v2 + BGE-small-zh-v1.5 (CPU, 双模。 |
| memory_search | OpenClaw 原生混合搜索 (向量+BM25) |
| mem0_bridge | Qdrant 读写桥接 |
| Qdrant 向量的| collection: sakura_memories, 4 角色 user_id 隔离 |
| CCR | 的8 轮提取事的。Qdrant |
| SmartCrusher | 24 消息/40K 字符硬截的|
| mem0_sync_cron | 的30min 同步 Qdrant 的_mem0_auto.md |
| headroom_routes.json | sidecar: model_id 的真实后端 baseUrl 映射 |

</td>
</tr>
</table>

### Headroom + Mem0 管线 (port 19251)

```
OpenClaw Gateway (18789)
  ├─ <provider>/<model-id>           的直连原始后端（不的headroom。
  ├─ local-llama/llama-local          的19251 的llama-server:8080
  └─ local-llama/<model-id>           的19251 的原始后端（走 headroom+mem0。
         。
         。
  headroom proxy (19251)
    ├─ [1] mem0 角色记忆注入（Qdrant 向量搜索。
    ├─ [2] SmartCrusher 5维压缩对话历。
    └─ [3] 路由到真实后。
         ├─ llama-local 的llama-server:8080
         └─ 云端模型    的sidecar 查找真实 baseUrl
```

**只加不改原则的* `start.ps1` 启动时自动扫的`~/.openclaw/openclaw.json`，新的`local-llama` provider（复制现有云端模型），原的provider 原封不动。原的baseUrl 存入 `~/.openclaw/headroom_routes.json` sidecar 文件。clone 后零配置。

### Agent 中枢

角色切换不改的能力指的+ 记忆层隔。

| 层级 | 文件 | 作用 | 切换的|
|-|-|-|-|
| **能力中枢** | `AGENTS.md` | ComfyUI/TTS/Live2D 指令 | 🛡️不动 |
| **速查索引** | `TOOLS.md` | 工具调用速查 | 🛡️不动 |
| **角色人格** | `SOUL.md` | 当前角色的性格/语气 | 🔄 热替的|
| **角色数据** | `IDENTITY.md` | 角色的设定 | 🔄 热替的|
| **用户档案** | `USER.md` | 男友名称/偏好 | 🛡️不动 |
| **后宫归档** | `skills/harem/<角色>/` | 角色卡真相来的| 📦 只读 |
| **短期记忆** | `memory/role_play/<角色>/` | 每日对话 YYYY-MM-DD.md | 🔀 按角色隔的|
| **长期记忆** | Qdrant `user_id=<角色>` | 向量长期记忆 | 🔀 按角色隔的|
| **同步缓存** | `_mem0_auto.md` | Qdrant 的markdown (30min) | 🔀 按角色隔的|

> 召回优先的向量长期记忆 > 手写日记 > SOUL 基础人设

### WebChat - 内置浏览器客户端

的shiki daemon 驱动的完整网。AI 女友聊天界面,本地运行的`http://127.0.0.1:19270`。

| 功能 | 说明 |
|-|-|
| **多角色标签页** | 在四季夏目、亚托莉、夜乃桜之间自由切换 - 每人独立对话历史、SOUL.md 人设和长期记的|
| **流式对话** | 实时 token 流式输出,自动注入角色专属 system prompt(角色人格 + 用户档案) |
| **AI 画图** 🎨 | 聊天输入区一键按的- LLM 根据对话上下文自动生。ComfyUI 提示词触发本地画图,图片直接显示在聊天流的|
| **Live2D 联动** | 直接在界面控。Live2D 桌面宠物:摸头、戳戳、待机动的|
| **TTS 语音** | 将聊天文本生成角色语音回。GPT-SoVITS) |
| **工坊面板** | 侧边栏手。TTS 合成。ComfyUI 画图,支持全参数调的提示词、负向、尺寸、步数、CFG、模。 |
| **仪表的* | 服务健康面板,显示 llama-server、Embedding、Live2D Bridge、Artemis Bridge、OpenClaw Gateway、WebChat 状的- 每项独立的的重启 |
| **显存管理开的* | 控制画图前是否停 llama-server 释放显存(8GB 显卡默认开的12GB+ 可关闭保持对话不中断) |
| **双模型支的* | 本地 llama-server 或远。DeepSeek 模型自由切换 - 设置中修的配置持久的|

> WebChat 直接的shiki daemon (:19260) 通信,daemon 代理请求的llama-server 。OpenAI 兼容 API。角色切换即时生的- 每个标签页加载对应角色的 SOUL.md + IDENTITY.md + USER.md 作为 system prompt。

### 技能详。

| 技的| 位置 | Llama 交互 | 备注 |
|-|-|-|-|
| **WebChat** | `web-chat/` | 。HTTP 代理 | 端口 19270, daemon 后端, 多角的|
| **Headroom Proxy** | `artemis_headroom_proxy.py` | 的独立进程 | 端口 19251, mem0+压缩+路由 |
| **Shiki Daemon** | `shiki_daemon.py` | 的共享 client | 端口 19260/19270, auto-inject |
| **Embedding** | `skills/shared/` | 的不碰 GPU | 双模。CPU, 端口 9999 |
| **Live2D** | `skills/live2d/` | 的。HTTP | 桥接 :19200, 独立进程 |
| **TTS** | `skills/tts/` | 🔶 。VRAM 分档 | Level 2 不杀, Level 0/1 的llama |
| **ComfyUI** | `skills/comfyui/` | 🔶 。VRAM 分档 | 同上 |
| **ASR** | `skills/asr/` | 的共存 (1.5GB) | Faster-Whisper small |
| **Sakura** | `skills/sakura/` | 的共享 client | 内置 CCR + mem0 |
| **Artemis Studio** | `artemis_studio.py` | 的独立运行 | 桌面控制。 TTS+ComfyUI 工坊 |
| **SmartCrusher** | `skills/shared/context_trimming.py` | - | 24 消息/40K 截断 |
| **Headroom Proxy** | `artemis_headroom_proxy.py` | - | mem0 注入 + 压缩 + 路由 :19251 |
| **Shiki Daemon** | `shiki_daemon.py` | - | WebChat 后端 + auto-inject provider |
| **CCR** | `skills/sakura/app/agent/memory_curator.py` | - | 的8 轮事实提的|
| **mem0 Bridge** | `skills/shared/mem0_bridge.py` | - | CLI 搜索/添加/同步 |
| **自动同步** | `skills/shared/mem0_sync_cron.py` | - | 30min Qdrant 的md |
| **角色导入** | `skills/character_importer/` | - | PNG/JSON 角色卡导的|

**VRAM 调度流程**:
1. 启动时自动检。GPU 显存 的确定 VRAM 级别(Level 0/1/2)
2. 的session 收到用户请求 的组装指令
3. `sessions_spawn(mode="run")` 创建的session
4. Level 0/1:`stop_llama()` 释放显存 。TTS/ComfyUI 推理 的`start_llama()` 恢复
5. Level 2 (的2GB):直接推理,llama 始终在线
6. 整个过程。Artemis Studio、Live2D、Embedding 保持运行--不受影响
7. 的session 写入 `.task_flags` 的通知回主 session
8. 的session 读取媒体文件 的通过 `<qqmedia>` / `MEDIA:` 发。
9. 后台:CCR 每约 8 轮运行一的提取长期记忆写入 Qdrant
10. Cron job 的30 分钟同步 Qdrant 的`_mem0_auto.md` 供原的`memory_search` 检。
11. Headroom proxy (19251) 透明拦截 `local-llama/*` 请求 的注入 mem0 的压缩上下的的路由到真实后。

## ⚠️ 重要说明

- **RTX 50xx (Blackwell) + CUDA 13.x = `munmap_chunk(): invalid pointer` 崩溃** - CUDA 13.x 。Blackwell 架构上与 llama.cpp 存在已知内存管理不兼容问题的*解决方案:使用 CUDA 12.x 预编译的 llama.cpp binary**(不要。CUDA 13.x 自行编译)。从 [llama.cpp Releases](https://github.com/ggml-org/llama.cpp/releases) 下载 `cudart-llama-bin-win-cuda-12.4-x64.zip`。RTX 5070 Ti 完全兼容 CUDA 12.x 驱动。
- TTS/ComfyUI 推理期间 llama-server 离线的60~120 的-对话暂停,。Live2D 继续运行
- 的session 使用 **local 模型**(与主 session 相同),DeepSeek 作为可的fallback
- Llama-server 不支持跨的prompt cache 复用(SSM 限制)--请使用定的`/reset`
- **Live2D 必须使用 Cubism Core 4**(的5 的6)--pixi-live2d-display v0.5.0 基于 Cubism 4 框架;Core 5+ 会导致裁的图层错误
- 所有模型文件受 `.gitignore` 保护,不上传到 GitHub
- GPT-SoVITS 权重为自训练,不公开发布--请用自己的语音数据训。

## 🙏 致谢

- [@Rvosy](https://github.com/Rvosy) - [Sakura Desktop Pet](https://github.com/Rvosy/Sakura) 作的已授权收。Issue #38)
- [@guansss](https://github.com/guansss) - [pixi-live2d-display](https://github.com/guansss/pixi-live2d-display) 作。
- [Live2D Inc.](https://www.live2d.com) - Cubism SDK(非商业用。
- [AgentRQ](https://github.com/agentrq/agentrq) - AgentRQ 兼容任务队列 + MCP 工具接口设计灵感来源
- [headroom](https://github.com/chopratejas/headroom) - SmartCrusher 上下文压的+ CCR(整理-合并-检的记忆管线灵感来源
- [mem0](https://github.com/mem0ai/mem0) - Qdrant 向量记忆架构 + 混合搜索设计灵感来源
- [NVIDIA Cosmos](https://github.com/NVIDIA/cosmos) - 物理世界基础模型,[社区 FP8 量化版](https://huggingface.co/benjiaiplayground/Cosmos3-Nano_fp8) 已存的`skills/cosmos/`
