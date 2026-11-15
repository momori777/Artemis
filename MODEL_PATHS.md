# 模型文件路径表（合并版）

> 合并自 `MODEL_PATHS.md` + `D:\model\model_path.txt`
> HF 仓库: **TAOTAO777/ai-girlfriend-natsume**
> ComfyUI 本地实例: `E:\comfyui\ComfyUI-aki-v3\ComfyUI\models\`

## LLM (llama.cpp / Strata)

> 🔴 端口布局 (2026-10): llama.cpp = **9931**；**8080 = Strata 引擎**，仅服务 Qwen3.8-Flash-Next（见 `skills/strata/SKILL.md`）。

| 文件 | 大小 | 本地路径 | HF 仓库路径 |
|------|------|---------|-------------|
| Qwen3.8-Flash-Next GSQ-RCO **abliterated** IQ3_S (**Strata 后端**，8080，不走 llama.cpp；131072 ctx；**显存 8G 起步 / 内存 ≥ 64G**，全专家常驻) | 两分卷共 83.8 GB（00001: 55.1 GB + 00002: 28.8 GB） | 新下载：`C:\Users\momori\Downloads\Qwen3.8-Flash-Next-GSQ-RCO-abliterated-IQ3_S-0000{1,2}-of-00002.gguf`（放入 `Strata-data\models\IQ3_S\` 时按 Strata 要求去掉 `-abliterated-` 改名） | 本仓库镜像 `llm/Qwen3.8-Flash-Next-GSQ-RCO-abliterated-IQ3_S-0000{1,2}-of-00002.gguf`（原始出处 SC117/Qwen3.8-Flash-Next-GSQ-RCO-abliterated-GGUF；基座 `Qwen/Qwen3.8-Flash-Next` 由 Strata 安装器自动下载，https://github.com/Niko1221/Strata） |
| Hermes3.6-35B-A3B Genesis Final MTP APEX (**带 MTP**；`--cpu-moe`，**显存 6G 起 / 内存 32G**，专家常驻内存) | 24.9GB | `llm\Hermes3.6-35B-A3B-Uncensored-Genesis-Final-MTP-APEX.gguf`（**待 `download-models.ps1` 下载**；本机现有 `D:\model2\Hermes3.6-35B-A3B-Uncensored-Genesis-Final-APEX.gguf` 24.0 GB（文件名未标 MTP）与 `llm\Hermes3.6-35B-A3B-Uncensored-Genesis-V13-APEX-Compact.gguf` 16.2 GB（旧 compact，已弃用）） | `llm/Hermes3.6-35B-A3B-Uncensored-Genesis-Final-MTP-APEX.gguf` |
| Qwen3.8-27B Ultimate Heretic Uncn Turbo Brilli 50x AGI NEO MTP (Q4_K_M, **带 MTP**，**24G 显存 + 32G 内存**，权重全上卡、20G 前缀缓存在内存) | 15.7GB | `C:\Users\momori\Downloads\Qwen3.8-27B-Ultimate-Heretic-Uncn-Turbo-Brilli-50x-AGI-NEO-MTP-Q4_K_M.gguf` | `llm/Qwen3.8-27B-Ultimate-Heretic-Uncn-Turbo-Brilli-50x-AGI-NEO-MTP-Q4_K_M.gguf` |
| DeepSeek-V4-Pro-Qwen3.5-9B UNCENSORED heretic (Q4_K_M, **当前 8G 显存主力，可全装；内存 16G 即可**；KV cache 必须 q4_0 + `--cache-ram` 卸载) | 6.1GB | `C:\Users\momori\Downloads\DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic-Q4_K_M.gguf` | `llm/DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic-Q4_K_M.gguf` |
| Ternary-Bonsai-2-27B PTQ1_0 (三值量化, legacy — 已从 HF `llm/` 移除，被上行 DeepSeek 9B 取代；**8G 显存 + 32G 内存**；KV 必须 q4_0 + ctx ≤ 75000) | 5.9GB | `E:\model3\Ternary-Bonsai-2-27B-PTQ1_0.gguf` | *(`llm/` 已移除)* |

## ComfyUI 模型

> 🔴 架构说明: **除 WAI (SDXL/Illustrious, 用 SDXL VAE) 外，其余扩散模型均为 qwen-image / anima 架构，统一使用 `qwen_image_vae.safetensors`**。
> 老版 `miaomiaoHarem_v20` (SDXL) 已从 HF 仓库删除，由 `miaomiaoHarem_29BBETA10` (anima/qwen 架构) 替代。

| 文件 | 大小 | 本地路径 | HF 仓库路径 | 架构 |
|------|------|---------|-------------|------|
| WAI-Nsfw-Illustrious-17 | 6.46GB | `E:\comfyui\ComfyUI-aki-v3\ComfyUI\models\checkpoints\WAI-Nsfw-Illustrious-17.safetensors` | `comfyui/checkpoints/WAI-Nsfw-Illustrious-17.safetensors` | SDXL/Illustrious |
| qwen-image-2.1-Q6_K | 5.47GB | `D:\model\diffusion_models\qwen-image-2.1-Q6_K.gguf` | `comfyui/diffusion_models/qwen-image-2.1-Q6_K.gguf` | qwen-image (GGUF) |
| miaomiaoHarem_29BBETA10 | 5.44GB | `E:\comfyui\ComfyUI-aki-v3\ComfyUI\models\diffusion_models\miaomiaoHarem_29BBETA10.safetensors` | `comfyui/diffusion_models/miaomiaoHarem_29BBETA10.safetensors` | anima/qwen (29B) |
| oneObsession_anima29BV1 | 5.44GB | `E:\comfyui\ComfyUI-aki-v3\ComfyUI\models\diffusion_models\oneObsession_anima29BV1.safetensors` | `comfyui/diffusion_models/oneObsession_anima29BV1.safetensors` | anima/qwen (29B) |
| qwen3vl_8b_int8_convrot (TE) | 8.71GB | `D:\model\text_encoders\qwen3vl_8b_int8_convrot.safetensors` | `comfyui/text_encoders/qwen3vl_8b_int8_convrot.safetensors` | qwen-image-2.1 文本编码器 |
| qwen_image_vae | 242MB | `E:\comfyui\ComfyUI-aki-v3\ComfyUI\models\vae\qwen_image_vae.safetensors` | `comfyui/vae/qwen_image_vae.safetensors` | qwen VAE（所有非 WAI 模型共用） |
| qwen_3_06b_base (TE) | 1.1GB | `E:\comfyui\ComfyUI-aki-v3\ComfyUI\models\text_encoders\qwen_3_06b_base.safetensors` | *(仅本地，未上传 HF)* | anima 29B 文本编码器 |

> HF 仓库 ComfyUI 目录结构（与 ComfyUI `models/` 标准子目录一一对应）:
>
> ```
> comfyui/
> ├── checkpoints/        # WAI (SDXL/Illustrious)
> ├── diffusion_models/   # qwen-image-2.1 GGUF + anima 29B safetensors
> ├── text_encoders/      # qwen3vl_8b_int8_convrot
> └── vae/                # qwen_image_vae (所有 qwen/anima 模型共用)
> ```

## GPT-SoVITS / Embedding / ASR / Live2D

| 文件 | 大小 | 放哪 | HF 仓库路径 |
|------|------|------|-------------|
| SoVITS ckpt (夏目) | 155MB | `gpt-sovits-weights\GPT_weights_v2Pro\xxx-e30.ckpt` | `gpt-sovits-weights/GPT_weights_v2Pro/xxx-e30.ckpt` |
| SoVITS pth (夏目) | 135MB | `gpt-sovits-weights\SoVITS_weights_v2Pro\xxx_e20_s6240.pth` | `gpt-sovits-weights/SoVITS_weights_v2Pro/xxx_e20_s6240.pth` |
| SoVITS ckpt (樱) | - | `gpt-sovits-weights\GPT_weights_v2Pro\sakura-e30.ckpt` | `gpt-sovits-weights/sakura/Sakura-e15.ckpt` |
| SoVITS pth (樱) | - | `gpt-sovits-weights\SoVITS_weights_v2Pro\sakura_e20_s6240.pth` | `gpt-sovits-weights/sakura/Sakura_e8_s7176.pth` |
| SoVITS ckpt (Enola) | - | `gpt-sovits-weights\GPT_weights_v2Pro\enola-e30.ckpt` | *(本地训练产物，未上传)* |
| SoVITS pth (Enola) | - | `gpt-sovits-weights\SoVITS_weights_v2Pro\enola_e20_s6240.pth` | *(本地训练产物，未上传)* |
| lid.176.bin | 125MB | `skills\sovits\GPT_SoVITS\pretrained_models\fast_langdetect\lid.176.bin` | *(HF `skills/` 目录已删除，本地自包含维护)* |
| all-MiniLM-L6-v2 | 80MB | `skills\sakura\runtime\hf-cache\` (自动下载) | `embedding/all-MiniLM-L6-v2/` |
| bge-small-zh-v1.5 | 91MB | `skills\sakura\runtime\hf-cache\` (自动下载) | `embedding/bge-small-zh-v1.5/` |
| faster-whisper-small | 461MB | `%USERPROFILE%\.cache\asr_models\` (自动下载) | *(上游 Systran/faster-whisper-small，本仓库不托管)* |
| shiki_natsume.tar.gz | 209MB | `live2d-model\shiki_natsume.tar.gz` → 解压到 `live2d\model\shiki_natsume\` | `live2d-model/shiki_natsume.tar.gz` |
| atri.tar.gz | - | `live2d-model\atri.tar.gz` → 解压到 `live2d\model\atri\` | `live2d-model/atri.tar.gz` |

## 一键下载

```powershell
.\download-models.ps1
```

## 备注

- `model_path.txt` 原写的 `qwen-image-2.1-Q4_K_M.gguf` / `qwen_image_2.1_vae_bf16.safetensors` 与本地实际文件名不符，已按实际文件（`Q6_K` / `qwen_image_vae.safetensors`）记录。
- HF 仓库 `skills/` 目录已删除（项目自包含依赖，不再从仓库分发）。
