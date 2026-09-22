# 模型文件路径表

> 根目录 = git clone 后 `cd` 进去的那个目录

## 模型文件

| 文件 | 大小 | 放哪（相对根目录） |
|------|------|-------------------|
| Hermes3.6-35B-A3B Genesis Final MTP APEX (**带 MTP**) | 24.9GB | `E:\model3\Hermes3.6-35B-A3B-Uncensored-Genesis-Final-MTP-APEX.gguf` |
| Qwen3.8-27B TTURBO Fable C-Fusion MTP (Q4_K_M, **带 MTP**) | 15.7GB | `C:\model2\Qwen3.8-27B-TTURBO-Fable-C-Fusion-709-L-Uncen-NM-DAU-NEO-MTP-Q4_K_M.gguf` |
| Ternary-Bonsai-2-27B PTQ1_0 (三值量化, **8G 显存可全装**; KV cache 必须 q4_0 + ctx ≤ 75000) | 5.9GB | `E:\model3\Ternary-Bonsai-2-27B-PTQ1_0.gguf` |
| WAI-Nsfw-Illustrious-17 | 6.5GB | `comfyui-checkpoints\WAI-Nsfw-Illustrious-17.safetensors` |
| miaomiaoHarem_v20 | 6.5GB | `comfyui-checkpoints\miaomiaoHarem_v20.safetensors` |
| SoVITS ckpt (夏目) | 155MB | `gpt-sovits-weights\GPT_weights_v2Pro\xxx-e30.ckpt` |
| SoVITS pth (夏目) | 135MB | `gpt-sovits-weights\SoVITS_weights_v2Pro\xxx_e20_s6240.pth` |
| SoVITS ckpt (樱) | - | `gpt-sovits-weights\GPT_weights_v2Pro\sakura-e30.ckpt` |
| SoVITS pth (樱) | - | `gpt-sovits-weights\SoVITS_weights_v2Pro\sakura_e20_s6240.pth` |
| SoVITS ckpt (Enola) | - | `gpt-sovits-weights\GPT_weights_v2Pro\enola-e30.ckpt` |
| SoVITS pth (Enola) | - | `gpt-sovits-weights\SoVITS_weights_v2Pro\enola_e20_s6240.pth` |
| lid.176.bin | 125MB | `skills\sovits\GPT_SoVITS\pretrained_models\fast_langdetect\lid.176.bin` |
| all-MiniLM-L6-v2 | 80MB | `skills\sakura\runtime\hf-cache\` (自动下载) |
| faster-whisper-small | 461MB |'%USERPROFILE%\\.cache\\asr_models')"` |
| shiki_natsume.tar.gz | 209MB | `live2d-model\shiki_natsume.tar.gz` → 解压到 `live2d\model\shiki_natsume\` |
| atri.tar.gz | - | `live2d-model\atri.tar.gz` → 解压到 `live2d\model\atri\` |

## 一键下载

```powershell
.\download-models.ps1
```
