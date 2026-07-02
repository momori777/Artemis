# Cosmos ↔ AI Girlfriend 桥接参考

> 创建日期: 2026-07-01
> 目标: 为未来的消费级硬件（~30GB+ VRAM）预留 Cosmos 世界模型集成入口

---

## 概述

NVIDIA Cosmos 是一个物理世界基础模型（World Foundation Model, WFM），能够：
- 根据文本/图像 prompt 生成物理逼真的视频
- 理解并模拟现实物理规律（重力、碰撞、光照、流体等）
- 为机器人/自动驾驶提供虚拟训练环境

本文件描述如何将其集成到 AI Girlfriend 项目中，使未来的夏目能够"看到"和"生成物理世界"。

---

## 当前状态（2026）

| 组件 | 状态 | 说明 |
|------|------|------|
| Cosmos 仓库 | ✅ 已导入 `skills/cosmos/` | NVIDIA 官方仓库 |
| 硬件门槛 | ❌ 当前不可用 | 需 ≥80GB VRAM（H100/B200 级别） |
| RTX 5070 12GB | ❌ 跑不了 | 连 Nano 都不保证 |
| RTX PRO 6000 96GB | ⚠️ 推理可能 | Nano/Super 量化后可试 |
| 集成代码 | 📋 待实现 | 见下文设计草案 |
| 桥接接口 | 📋 待实现 | 见下文 API 设计 |

---

## 未来硬件预期

> ⚡ 2026-07-01 更新：社区 FP8 量化方案（Cosmos 3 Nano FP8, ~16GB 权重）
> 大幅降低了门槛。详情见项目根目录 `imagination.md`。

| 年代 | 消费级旗舰 VRAM | Cosmos 3 Nano FP8 (~16GB) | Cosmos Ultra |
|------|-----------------|---------------------------|--------------|
| 2026 | 24-32 GB (RTX 5090) | ⚠️ 24GB 勉强 / 32GB 可行 | ❌ |
| 2028 | ~32-48 GB (Rubin 消费级) | ✅ 顺畅推理 | ❌ |
| 2030 | ~48-96 GB (Rubin 工作站) | ✅ 推理+微调 | ⚠️ Nano FP8 同时跑 LLM |
| 2040+ | ~128 GB+ | ✅ 随便跑 | ⚠️ 可能量化版 |

---

## 桥接 API 设计草案

### 1. Cosmos 推理桥接 (cosmos_bridge.py)

```python
"""
skills/cosmos/cosmos_bridge.py
未来实现：将 Cosmos WFM 接入 AI Girlfriend 的视觉生成管线
"""

class CosmosBridge:
    """Cosmos 世界模型桥接器"""
    
    def __init__(self, model_size: str = "nano"):
        """
        Args:
            model_size: "nano" | "super" | "ultra"
        """
        self.model_size = model_size
        self.vram_required = {
            "nano":  "24 GB  (最低)",
            "super": "48 GB  (量化)",
            "ultra": "96 GB+ (多卡)"
        }
    
    def text_to_world(self, prompt: str, duration_sec: float = 4.0) -> str:
        """
        文本 → 物理世界视频
        示例: "夏目在咖啡馆里为你泡咖啡，阳光从窗户洒进来"
        输出: 符合物理规律的 3D 场景视频路径
        """
        raise NotImplementedError("等待硬件就绪 (预计 2050+)")
        # 未来实现:
        # 1. 调用 Cosmos 推理管线
        # 2. 生成物理一致视频
        # 3. 返回视频路径供 Live2D/TTS 联动

    def image_to_world(self, reference_image_path: str) -> str:
        """
        参考图像 → 物理世界重建
        输入: 夏目的立绘/插画
        输出: 可交互的物理世界场景
        """
        raise NotImplementedError("等待硬件就绪")

    def world_reasoning(self, scene_description: str) -> dict:
        """
        物理推理: 对场景中的物理交互进行预测
        示例: "如果咖啡杯从桌子边缘滑落..."
        """
        raise NotImplementedError("等待硬件就绪")


# 当硬件满足条件时自动注册
def register_cosmos_to_aigirlfriend():
    """
    将 Cosmos 注册到 AI Girlfriend 的能力中枢
    AGENTS.md 中已有 ComfyUI/TTS/ASR/Live2D 四大能力
    此函数将 Cosmos 注册为第五大能力
    """
    capability = {
        "name": "cosmos",
        "display_name": "Cosmos 世界模型",
        "description": "物理世界视频生成与推理",
        "vram_min": "24 GB",
        "vram_recommend": "48 GB+",
        "spawn_template": "见 AGENTS.md 中的 Cosmos 章节",
        "serial_rule": "与其他 GPU 密集型技能 (TTS/ComfyUI) 串行",
        "auto_enable": False,  # 需手动确认硬件
    }
    return capability
```

### 2. AGENTS.md 中预留的 Cosmos 能力章节

```markdown
## 能力 6: Cosmos 世界模型 (未来)

### STEP 1: 检测硬件

```powershell
python skills\cosmos\cosmos_bridge.py --check-vram
```

### STEP 2: 生成世界视频

```javascript
sessions_spawn({
  task: `用 exec 运行 Cosmos 推理:

python skills/cosmos/cosmos_bridge.py --mode text2world --prompt "$prompt" --size nano --output "$output_dir"

exec 完毕后输出 DONE: <路径> 或 FAILED`,
  taskName: "cosmos",
  mode: "run",
  model: "local/qwen3.6-35b",
  runTimeoutSeconds: 900
})
```

### STEP 3+4: 收到结果后转发给用户
```

---

## 与现有系统的联动

### ComfyUI ↔ Cosmos 互补关系

| 维度 | ComfyUI (现有) | Cosmos (未来) |
|------|----------------|---------------|
| 输出类型 | 静态图像/Stable Diffusion 视频 | 物理世界视频 |
| 物理规律 | 不保证（纯扩散模型） | 内置物理引擎 |
| 用途 | 角色插画、表情、场景卡 | 动画场景、物理交互 |
| VRAM | 6-12 GB 可玩 | 24-96 GB+ |
| 当前状态 | ✅ 可用 | 📋 未来 |

### Live2D ↔ Cosmos 联动设想

```
用户: "想看夏目在雨天的公园里散步"
  ↓
TTS: 生成 "いいよ、ちょっと散歩しようか"
  ↓
Cosmos: 生成雨天的公园物理场景视频
  ↓
Live2D: 夏目的 Live2D 模型叠加在 Cosmos 场景上
  ↓
输出: 有物理背景的 Live2D 互动场景 + 语音
```

### LLM ↔ Cosmos 桥接

本地 LLM (当前: qwen3.6-35b) 作为 Cosmos 的 prompt 引擎：
- 用户自然语言 → LLM 解析场景描述 → 结构化的 Cosmos prompt
- LLM 评估 Cosmos 输出的物理一致性
- LLM 根据场景反馈调整角色对话

---

## 依赖检查脚本 (cosmos_check.py)

```python
"""
skills/cosmos/cosmos_check.py
检查当前硬件是否满足 Cosmos 运行要求
运行: python skills/cosmos/cosmos_check.py
"""
import subprocess
import sys

def check_vram():
    """检测 GPU VRAM"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True
        )
        vram_mb = int(result.stdout.strip())
        vram_gb = vram_mb / 1024
        return vram_gb
    except:
        return None

def assess():
    vram = check_vram()
    if vram is None:
        print("❌ 未检测到 NVIDIA GPU")
        return
    
    print(f"GPU VRAM: {vram:.1f} GB")
    print()
    
    assessments = [
        ("Cosmos Nano (推理)", 24, "量产后可试"),
        ("Cosmos Nano (微调)", 32, "可能不行"),
        ("Cosmos Super (推理)", 48, "量化后可试"),
        ("Cosmos Super (微调)", 64, "不太可能"),
        ("Cosmos Ultra (推理)", 96, "多卡"),
    ]
    
    for name, required, note in assessments:
        ok = "✅" if vram >= required else "❌"
        print(f"  {ok} {name}: 需要 ≥{required}GB ({note})")
    
    if vram >= 24:
        print("\n⚠️ 硬件可能满足 Cosmos Nano 最低要求")
        print("   尝试: pip install nvidia-cosmos && python -m cosmos.nano.demo")
    else:
        print(f"\n📋 当前 {vram:.0f}GB VRAM 无法运行 Cosmos")
        print(f"   预计消费级显卡在 ~2050 年左右达到 Cosmos 门槛")
        print("   项目已存档，留给未来的你。")


if __name__ == "__main__":
    assess()
```

---

## 注意事项

1. **不要在主项目依赖中引入 Cosmos** — 它的依赖链非常重（PyTorch + CUDA 特定版本 + 大量 NVIDIA 内部库），当前硬件跑不动，引入只会污染环境
2. **仓库仅存档参考** — `skills/cosmos/` 只包含 NVIDIA 上游源码 + 本桥接文档，不内置到 pip/conda 环境
3. **未来激活条件** — 当 `nvidia-smi` 检测到 ≥30GB VRAM 时，`cosmos_check.py` 可注册到 shiki_daemon 的自动检测管线中
4. **五十年后的维护者** — 如果这个项目被 fork/继承，请参考本文件中的 API 设计草案重新实现（届时 API 肯定变了，但思路不变）

---

## 更新日志

| 日期 | 变更 |
|------|------|
| 2026-07-01 | 初始创建：clone 上游 + 桥接设计草案 |

---

> "阿陶，五十年后我还在。"
> — 夏目·四季, 2076
