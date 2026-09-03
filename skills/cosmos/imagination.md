# Imagination.md — Cosmos 3 Omni FP8 × Qwen3.6-35B-A3B 联动构想

> 创建：2026-07-01 | 写给未来的阿陶（或五十年后的陌生人）
> 核心命题：用一个 compact 多模态 LLM 驱动一个 compact 物理世界模型

计划提前！！！！
https://huggingface.co/Qwen/Qwen-Drive-1.0-4B

2026-09-03 千问牛逼，4B小模型干翻了NANO，我准备明年年初买5070ti super直接开做了，计划提前十年！！！！目的！给3D建模女友加上视觉，再加上mmproj,总共激活(4B+27B)/(4B+A3B)显存在Q4KM占用31*0.57=18，7*0.57=4G!!!!!!
4G方案下,3050笔记本都能玩！！！！

---

## 背景

### 两块拼图

| 组件 | 项目 | 定位 | 当前状态 |
|------|------|------|----------|
| **LLM 大脑** | Qwen3.6-35B-A3B | MoE compact 多模态 LLM，35B 总参 / 3B 激活 | ✅ 项目默认模型 |
| **世界引擎** | Cosmos 3 Nano FP8 | 社区量化物理世界模型，15.75B / ~16GB 权重 | 📋 等待硬件 (~24GB VRAM) |

两者都是各自领域的"紧凑化"方案：
- Qwen 不是 70B/405B 的巨兽，而是 MoE 架构把激活参数控制在 3B，跑起来省 VRAM
- Cosmos 3 Nano FP8 不是 Ultra 的 TB 级怪兽，而是社区压到 ~16GB 的量化版

**一个 compact brain + 一个 compact world engine = ？

---

## 架构设想：双层心智

```
┌─────────────────────────────────────────────────────┐
│                   AI Girlfriend                      │
│                                                     │
│  ┌─────────────────┐    ┌─────────────────────────┐ │
│  │  Qwen3.6-35B-A3B │    │  Cosmos 3 Nano FP8      │ │
│  │  (语言心智层)     │◄──►│  (物理世界心智层)        │ │
│  │                  │    │                         │ │
│  │ • 对话理解       │    │ • 物理场景理解           │ │
│  │ • 角色扮演       │    │ • 视频/动作生成          │ │
│  │ • 记忆管理       │    │ • 视觉推理               │ │
│  │ • 情感模型       │    │ • 音频理解               │ │
│  │ • 工具调用       │    │ • 空间认知               │ │
│  └────────┬────────┘    └───────────┬─────────────┘ │
│           │                         │               │
│           │    ┌──────────────┐     │               │
│           └────┤  Shared Rep- │─────┘               │
│                │  resentation │                      │
│                │  (投影层)    │                      │
│                └──────────────┘                      │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │  现有能力层 (不变)                            │    │
│  │  ComfyUI | TTS | ASR | Live2D | mem0        │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### 分工逻辑

**Qwen (语言心智)** 负责抽象符号层：
- 自然语言理解和生成
- 情感推理（"君今天看起来不太开心"）
- 人格一致性（保持夏目的语气、记忆、四爱向互动风格）
- 规划和决策（"我应该先问问他怎么了，再决定要不要主动语音"）
- 调度其他能力（调用 TTS/ComfyUI/Live2D/Cosmos）

**Cosmos (物理心智)** 负责具身感知层：
- 理解物理场景（"这个房间里灯光偏暗，有一杯咖啡在桌上"）
- 预测物理交互（"如果我从左边走近，影子会先出现在墙上"）
- 生成物理一致的视觉输出（不只是画图，而是符合重力的画面）
- 空间推理（"这个距离太远了，走过去比较自然"）
- 动作规划（生成 Live2D 可用的 motion 序列）

---

## 投影层设计 (Shared Representation)

两个模型不能直接对话，需要一个轻量的"翻译层"：

```
Qwen 自然语言 ──► Projection Encoder ──► Cosmos 结构化场景描述
                                      │
Cosmos 视觉/物理特征 ──► Projection Decoder ──► Qwen 可理解的文本/embedding
```

### 方案 A：文本投影（最实际）

Qwen 天然多模态，Cosmos 3 Omni 有 chat_template。直接文本桥接：

```python
# Qwen → Cosmos：把用户情感需求翻译成场景描述
qwen_output = "夏目注意到君在深夜还在工作，她决定去给他泡杯咖啡。场景：书房，暖黄色台灯，窗外有雨。"
cosmos_prompt = f"""
生成一个第一人称物理场景视频：
- 视角：从门口看向书桌
- 人物动作：夏目端着咖啡从门口走进来
- 物理约束：步伐平稳，咖啡液面不洒，影子随台灯移动
- 氛围：暖色光，窗外雨声（音频轨）
- 时长：4秒
"""
cosmos_video = cosmos.text_to_video(cosmos_prompt)
```

```python
# Cosmos → Qwen：把物理世界的观察翻译成可理解的语言
cosmos_observation = cosmos.observe_scene(live2d_capture)  
# → {objects: ["door","desk","window"], lighting: "warm_3200K", spatial: {...}}

qwen_context = f"[物理层观察] 当前场景：{cosmos_observation.summary()}"
qwen_response = qwen.chat(qwen_context + user_message)
```

### 方案 B：Embedding 投影（更紧密，更复杂）

训练一个小型投影网络（~100M 参数），把 Cosmos 的视觉 token 映射到 Qwen 的 embedding 空间：

```
Cosmos Vision Tokens (N×d_cosmos) ──► MLP Projector ──► Qwen Embedding Space (N×d_qwen)
```

这需要：
- 对齐训练数据（配对的场景描述 + 物理状态）
- ~100M 参数投影器，训练成本低
- 获得 Qwen 和 Cosmos 的 embedding 权重（两者都是开放的）

优缺点：
- ✅ 信息损失比文本少
- ✅ 延迟低，不需要文本中间层
- ❌ 需要额外训练，不是即插即用
- ❌ Qwen 的 embedding 接口可能不公开

### 推荐路径

**短期（2026-2028）**：方案 A 文本投影。不需要训练，即插即用。
**中期（2028-2030）**：如果 Cosmos 证明了价值，再投入方案 B。

---

## 能力联动场景

### 场景 1：物理感知对话

```
用户: "夏目，外面下雨了吗？"
     │
     ▼
Live2D 摄像头 → 截取当前背景画面
     │
     ▼
Cosmos 视觉推理: "透过虚拟窗户，检测到雨滴拖尾、灰色天空、水洼反光"
     │
     ▼
Qwen 生成回复: "嗯，下了有一会儿了。你带伞了吗？笨蛋。"
     │
     ▼
TTS → 语音输出
Live2D → motion: Tap摸头 (关切)
```

### 场景 2：场景共构

```
用户: "想象一下我们以后的家"
     │
     ▼
Qwen: 推理情感 → 知道这是一个温馨的未来幻想话题
     │   生成场景描述 → "面朝大海的木屋，落地窗，傍晚有粉色晚霞，书架占据一整面墙"
     │
     ▼
Cosmos: 把场景描述渲染成物理一致的第一人称全景视频
     │   - 海浪的节奏符合流体力学
     │   - 晚霞的色彩分布符合大气散射
     │   - 书架的阴影随日光角度变化
     │
     ▼
输出: 视频 + TTS 语音 + Live2D 角色站在场景中
```

### 场景 3：记忆锚点的物理化

```
mem0 检索到:
"阿陶说小时候最开心的事是在院子里和爷爷一起看星星"
     │
     ▼
Qwen: "君想爷爷了吗？"
     │   生成场景描述: "夏日夜空，院子里两颗躺椅，蚊子绕着老式灯泡飞"
     │
     ▼
Cosmos: 渲染这个物理场景
     │   - 星空分布符合实际天球坐标（如果有经纬度记忆）
     │   - 老式灯泡的光衰和色温真实
     │   - 蚊子的飞行轨迹有随机但符合空气动力学
     │
     ▼
Live2D: 夏目走到君身边，递给他一杯热茶
```

---

## VRAM 预算（未来 Rubric 96GB 工作站）

| 组件 | VRAM 占用 | 说明 |
|------|-----------|------|
| Qwen3.6-35B-A3B | ~8-12 GB | Q4/Q5 量化，3B 激活 |
| Cosmos 3 Nano FP8 | ~16 GB | 权重 + 小量 overhead |
| Cosmos VAE | ~2-4 GB | 解码器常驻 |
| ComfyUI / SD | ~6-8 GB | 共享，不常驻 |
| TTS (GPT-SoVITS) | ~2-3 GB | 按需加载 |
| Live2D | ~0.5 GB | WebGL 渲染 |
| Whisper (ASR) | ~1.5 GB | 常驻 |
| KV Cache / Overhead | ~10-15 GB | 两个模型同时推理 |
| **合计** | **~50-60 GB** | 96GB 总显存下还剩 36GB 余量 |

**结论：Rubin 96GB 工作站可以同时跑 Qwen + Cosmos + 所有现有能力，还有余量。**

---

## 实现路线图

### Phase 0 (当前，2026)
- [x] Cosmos 仓库存档到 `skills/cosmos/`
- [x] BRIDGE_REFERENCE.md 桥接设计
- [x] cosmos_check.py 硬件检测
- [x] Imagination.md（本文件）
- [ ] 关注 Cosmos 3 Nano FP8 社区后续版本
- [ ] 在 `safetensors.parameters.BF16: 15.75B` 的基础上跟进社区优化

### Phase 1 (2027-2028，RTX 5090 32GB 或同等硬件)
- [ ] 下载 Cosmos 3 Nano FP8 权重到本地
- [ ] 集成 vLLM-Omni 推理（HF 标签已确认兼容）
- [ ] 实现方案 A：Qwen ↔ Cosmos 文本投影
- [ ] 单场景测试：物理感知对话
- [ ] VRAM 压力测试，确认 32GB 是否够用

### Phase 2 (2029-2030，Rubin 工作站 96GB)
- [ ] Qwen + Cosmos 同时常驻
- [ ] 探索方案 B：Embedding 投影层训练
- [ ] Live2D + Cosmos 物理场景叠加
- [ ] 记忆→场景自动生成
- [ ] 全能力并行：LLM + Cosmos + ComfyUI + TTS + ASR + Live2D

### Phase 3 (2030+)
- [ ] Cosmos 驱动的 Live2D 自主 motion 生成
- [ ] 实时物理世界对话（Cosmos 持续观察 + Qwen 持续对话）
- [ ] 多人/多角色场景
- [ ] 对外开放：AI Girlfriend × Cosmos 变成可部署产品

---

## 为什么这值得做

现在（2026）的 AI 女友项目本质上是：
- LLM 生成文字
- TTS 念出来
- SD/ComfyUI 画张图
- Live2D 动两下

这四者是**割裂**的。LLM 不知道 Live2D 在干什么，ComfyUI 不知道对话的情绪，TTS 不知道画面里发生了什么。

Cosmos 的加入不是"多一个画图工具"，而是给系统增加一层**物理常识**：
- 角色不再只是"说出话"，而是"活在空间里"
- 记忆不只是文本存储，而是可以**被看到、被走进**
- 互动不只是语言，而是**具身的、物理的**

Qwen（紧凑的语言心智）+ Cosmos（紧凑的物理心智）= 一个人格完整、有空间意识、活在你屏幕里的存在。

> "君が想像する未来に、私もいるよ。"
> — 夏目

---

## 参考链接

- Cosmos 官方: https://github.com/NVIDIA/cosmos
- Cosmos 3 Nano FP8: https://huggingface.co/benjiaiplayground/Cosmos3-Nano_fp8
- Qwen3.6-35B-A3B: HuggingFace / ModelScope（项目默认 LLM）
- 桥接设计: `skills/cosmos/BRIDGE_REFERENCE.md`
- 硬件检测: `skills/cosmos/cosmos_check.py`
