# STARTUP_CODE.md — 全部启动命令 / All Launch Commands / すべての起動コマンド

> 本文件集中存放**所有启动命令**（从 README 三语版和 LLAMA_TUNING.md 抽出）。
> README 只讲"什么硬件跑什么模型"；调校原理见 [LLAMA_TUNING.md](LLAMA_TUNING.md)。
> All launch commands live here. The READMEs only document hardware ↔ model pairing.

## 硬件 → 命令索引 (index)

| 显存 | 内存 | 模型 | 引擎 / 端口 | 小节 |
|-|-|-|-|-|
| 8 GB | **16 GB** | DeepSeek-V4-Pro-Qwen3.5-9B heretic Q4_K_M（权重全上卡，内存只放 2 GB `--cache-ram`） | llama.cpp :9931 | §1 |
| 6–8 GB | **32 GB 起** | Hermes3.6-35B Genesis **Final MTP APEX**（`--cpu-moe`：24.9 GB 专家常驻内存） | llama.cpp :9931 | §3 |
| 8 GB | **32 GB** | Ternary-Bonsai-2-27B PTQ1_0（legacy，已被 §1 取代） | llama.cpp :9931 | §4 |
| 24 GB | **32 GB 起** | Qwen3.8-27B Ultimate Heretic Q4_K_M（权重全上卡，内存只放 20 GB `--cache-ram`） | llama.cpp :9931 | §2 |
| **8 GB 起步**（24 GB = 全量上卡 + 131K） | **64 GB 起** | Qwen3.8-Flash-Next 125B MoE（IQ3_S 两分卷共 83.8 GB，全专家常驻内存） | **Strata** :8080 | §5 |

> 📏 **显存与内存是两笔独立预算**：稠密模型的权重几乎全在显存，内存只需覆盖 `--cache-ram` 前缀缓存 + 系统；MoE 的专家权重只能进内存（或退化到 SSD），所以 **MoE 卡的是内存**——`--cpu-moe` / Strata 都是如此。参考机：RTX 5070 Laptop 8 GB + 32 GB DDR5（§1 / §3）。

通用变量（各小节命令都引用它们）：

```powershell
$exe = "...\llama-server.exe"                            # llama.cpp 构建
$tpl = "E:\AI_Girlfriend\chat_template.jinja"            # 修正版模板，覆盖全部 Qwen/DeepSeek 构建
```

> ⚠️ **PowerShell 数组每一对参数必须用逗号分隔**——行尾缺逗号会在重排成单行时把两个 token 悄悄粘连。
> 💡 `-rea` 未指定时，由聊天模板默认给 `medium` 推理深度（不注入思考 token，保持 KV 缓存一致性）。

---

## 1. DeepSeek-V4-Pro-Qwen3.5-9B heretic（Q4_K_M）— 8 GB VRAM 全量装载 🔥

当前 8 GB 卡主力。磁盘 6.12 GB / ~5.7 GiB，`-c 120000` + KV q4_0 + `--cache-ram 2000` 实测可装入 8 GB。
模型下载：HF 仓库 `llm/DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic-Q4_K_M.gguf`（TAOTAO777/ai-girlfriend-natsume）。

```powershell
$model = "...\DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic-Q4_K_M.gguf"
Start-Process -FilePath $exe -ArgumentList @(
"-m", $model,
"-c", "120000",
"--flash-attn", "on",
"--temp", "0.8",
"--top-p", "0.95",
"--top-k", "20",
"--min-p", "0.01",
"--repeat-penalty", "1.02",
"--presence-penalty", "0.0",
"-ctk", "q4_0", "-ctv", "q4_0",
"--batch-size", "1000",
"--ubatch-size", "500",
"--threads", "16",
"--threads-batch", "16",
"-rea", "on",
"--jinja",
"--api-key", "123",
"--cache-ram", "2000",
"--parallel", "1",
"--no-warmup",
"--kv-unified",
"--chat-template-file", $tpl,
"--reasoning-preserve",
"--reasoning-effort",  "xultra"
)
```

> 📝 `-ngl` 未指定——llama.cpp 自动按显存预算全量卸载（模型 5.7 GiB < 8 GB，可全上卡）。
> 📝 本条已补齐参考机原始粘贴中缺失的两处行尾逗号（`"0.0"` 与 `"2000"` 行尾），参数值未改动。

## 2. Qwen3.8-27B（Q4_K_M）— 24 GB VRAM（RTX PRO 4000 / 5090 DV2 / 4090 / 3090ti / 5090 Laptop）

```powershell
$model = "Qwen3.8-27B-Ultimate-Heretic-Uncn-Turbo-Brilli-50x-AGI-NEO-MTP-Q4_K_M.gguf"
Start-Process -FilePath $exe -ArgumentList @(
"-m", $model,
"-c", "130000",
"--flash-attn", "on",
"--temp", "0.9",
"--top-p", "0.95",
"--top-k", "40",
"--min-p", "0.01",
"--repeat-penalty", "1.02",
"--presence-penalty", "0.0",
"-ctk", "q8_0", "-ctv", "q8_0",
"--batch-size", "3000",
"--ubatch-size", "1500",
"--threads", "16",
"--threads-batch", "16",
"-rea", "on",
"--jinja",
"--api-key", "123",
"--cache-ram", "20000",
"--parallel", "1",
"--no-warmup",
"--kv-unified",
"--chat-template-file", $tpl,
"--reasoning-preserve",
"--spec-type", "draft-mtp",
"--spec-draft-n-max", "4",
"--spec-draft-p-min", "0.52",
"--spec-draft-type-k", "q8_0", 
"--spec-draft-type-v", "q8_0"
)
```

> 实测（5090 Laptop 24 GB）：decode ~35 t/s，prefill ~1300 t/s。

## 3. Hermes3.6-35B Genesis Final MTP APEX — 6 GB 显存起 + 32 GB 内存（`--cpu-moe`）

```powershell
$model = "E:\AI_Girlfriend\llm\Hermes3.6-35B-A3B-Uncensored-Genesis-Final-MTP-APEX.gguf"
Start-Process -FilePath $exe -ArgumentList @(
"-m", $model,
"-c", "120000",
"--cpu-moe",
"--flash-attn", "on",
"--temp", "0.6",
"--top-k", "40",
"--min-p", "0.01",
"--repeat-penalty", "1.02",
"--presence-penalty", "0.0",
"-ctk", "q4_0", "-ctv", "q4_0",
"--batch-size", "400",
"--ubatch-size", "200",
"--threads", "24",
"--api-key", "123456",
"-rea", "on",
"--jinja",
"--cache-ram", "5000",
"--parallel", "1",
"--kv-unified",
"--no-warmup",
"--spec-type", "draft-mtp",
"--spec-draft-n-max", "3",
"--spec-draft-p-min", "0.84",
"--spec-draft-type-k", "q4_0", 
"--spec-draft-type-v", "q4_0", 
"--chat-template-file", $tpl,
"--load-mode", "none",
"--reasoning-preserve",
"--reasoning-format", "deepseek"
)
```

> 实测：prefill ~250 t/s，decode ~34.88 t/s。
>
> 📁 模型文件：`Hermes3.6-35B-A3B-Uncensored-Genesis-**Final**-MTP-APEX.gguf`（24.9 GB，HF `llm/` 镜像，`download-models.ps1` 自动下载）。**旧 V13 / APEX Compact（16.2 GB）已被 Final 取代**；若手上的文件名未标 MTP（如 `...-Genesis-Final-APEX.gguf`），`--spec-type draft-mtp` 拿不到 MTP 头，请换成 MTP 版。

## 4. Ternary-Bonsai-2-27B PTQ1_0 — 8 GB VRAM（legacy；已被 §1 取代）

```powershell
$model = "...\Ternary-Bonsai-2-27B-PTQ1_0.gguf"
Start-Process -FilePath $exe -ArgumentList @(
"-m", $model,
"-c", "75000",
"--flash-attn", "on",
"--temp", "0.6",
"--top-p", "0.95",
"--top-k", "40",
"--min-p", "0.01",
"--repeat-penalty", "1.02",
"--presence-penalty", "0.0",
"-ctk", "q4_0", "-ctv", "q4_0",
"--batch-size", "400",
"--ubatch-size", "200",
"--threads", "24",
"--api-key", "123456",
"-rea", "on",
"--jinja",
"--cache-ram", "10000",
"--parallel", "1",
"--kv-unified",
"--no-warmup",
"--spec-type", 
"--chat-template-file", $tpl,
"--load-mode", "none",
"--reasoning-preserve",
"--reasoning-format", "deepseek",
"-ngl", "99",
"--reasoning-effort",  "medium",
)
```

> 实测：decode ~35 t/s+，prefill ~300 t/s。行间缺失的逗号已统一补全；`"--spec-type",` 悬空值按原文保留（照抄时留意）。
> 注：该 GGUF 已从 HF `llm/` 目录移除，被 DeepSeek-V4 9B（§1）取代。

## 5. Qwen3.8-Flash-Next 125B MoE — Strata 引擎（:8080，**不是 llama.cpp**，24 GB 级）

```powershell
# 一次性安装（clone 原始仓库，勿放进本项目 skills/）
git clone https://github.com/Niko1221/Strata
cd Strata
START-HERE.bat   # 首次运行：询问模型/量化/上下文，下载全部文件，生成启动 bat

# 之后每次启动 LLM（跑其他大模型前先停掉 Strata，显存/内存冲突）
.\run-iq3_s.bat
```

> Uncensored 版本替换与重命名步骤见 README「Qwen3.8-Flash-Next」小节；测速记录见 LLAMA_TUNING.md。

## 6. 模型切换一行命令（llama.cpp :9931，config.yaml 自动配参）

```powershell
cd E:\AI_Girlfriend   # 按你的项目根目录调整
# 27B dense (Qwen3.8-27B) — primary tooling model
.\skills\shared\restart_llama_degraded.ps1 -SwitchTo qwen3.8-27b

# 35B MoE (Hermes Genesis Final MTP APEX) — primary roleplay model
.\skills\shared\restart_llama_degraded.ps1 -SwitchTo qwen3.6-35b
```

> `-SwitchTo` 接受 `config.yaml` → `llama_model_map` 中的键或子串；显存受限时加 `-ForceBatch 1024`。

## 7. 聊天模板启动配管（所有 llama.cpp 模型通用）

```powershell
llama-server.exe ... --jinja --reasoning-preserve `
  --chat-template-file "E:\AI_Girlfriend\chat_template.jinja"
```

## 8. Reasoning 控制（Qwen 系）

```powershell
"--chat-template-kwargs", '{"reasoning_effort":"low"}'   # low | medium | xhigh
```

- `-rea off` 关闭推理；DeepSeek-V4 9B 用 `--reasoning-effort xultra`（见 §1）。

## 9. Claude Code / Task Board 启动

```powershell
# 前置：npm install -g @anthropic-ai/claude-code
# 先启动 Shiki Daemon（.\shiki.cmd），然后：

.\claude-code.ps1              # 完整 AgentRQ 工作流（Task Board + Claude Code）
.\claude-code.ps1 -BoardOnly   # 只要 Task Board（浏览器 UI，不起 Claude）
.\claude-code.ps1 -KillBoard   # 停掉 Task Board
```

## 10. 视觉扩展（mmproj）

```powershell
"--mmproj", "mmproj-(model-id).gguf"
```

- 更大/更小尺寸的同族模型：
  [LuffyTheFox/Qwen3.6-35B-A3B-Uncensored-Genesis-Hermes-Final-GGUF](https://huggingface.co/LuffyTheFox/Qwen3.6-35B-A3B-Uncensored-Genesis-Hermes-Final-GGUF) ·
  [DavidAU](https://huggingface.co/DavidAU)（Qwen3.8-27B 融合系列作者页）
