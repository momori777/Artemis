# AMD GPU 适配包

> 使用方法：把本文件夹内的全部文件**覆盖**到项目根目录（`D:\AI_Girlfriend\`），即可完成 A 卡适配。
>
> ⚠️ 覆盖前建议先备份原文件，方便以后切回 N 卡。

---

## 做了什么

本适配包把 llama.cpp 从 CUDA 后端切换到 **Vulkan** 后端，并适配所有相关脚本。Vulkan 是跨平台的 GPU API，支持 AMD、Intel 和 NVIDIA。

| 组件 | 变更 |
|------|------|
| **llama.cpp** | CUDA → Vulkan 后端 |
| **start.ps1** | 启动参数: 去掉 `--flash-attn`/`-ctk`/`-ctv`，ngl → 99 |
| **llama_lifecycle.py** | VRAM 检测 GPU 无关化 (CUDA → vulkaninfo → WMI → fallback) |
| **restart_llama_degraded.ps1** | 去掉 CUDA 专属参数 |
| **ComfyUI (comfyui_call.py)** | `torch.cuda.empty_cache()` → `safe_empty_cache()` (GPU 无关) |
| **ASR (asr_call.py)** | GPU 检测: CUDA/HIP → Vulkan → CPU 三级降级 |
| **TTS (tts_call.py)** | 不需要改 — 它不直接调 CUDA，llama 部分已在 lifecycle 中适配 |
| **setup-llama.ps1** | 硬件检测加 AMD 分支，推荐 Vulkan 二进制下载 |

---

## 覆盖后还需做的事

### 1. 下载 Vulkan 版 llama.cpp

🔗 https://github.com/ggml-org/llama.cpp/releases

找到 `llama-bXXXX-bin-win-vulkan-x64.zip`，**不要下载 CUDA 版**。
解压后，修改 `config.yaml` 中的 `llama_exe` 路径。

### 2. 修改 config.yaml

```yaml
# 改这两行:
llama_exe: "D:\\你的路径\\llama-bXXXX-bin-win-vulkan-x64\\llama-server.exe"
restart_script: "D:\\你的路径\\restart-llama.ps1"
```

### 3. ComfyUI + GPT-SoVITS — 各自需要 AMD 版 torch

这两个工具使用 PyTorch 做推理，**需要安装 AMD GPU 兼容的 torch**，不在此适配包范围内：

| 工具 | 方案 |
|------|------|
| **ComfyUI** | 方案A: DirectML 版 (秋叶整合包有 AMD 选项)<br>方案B: ZLUDA 翻译层<br>🔗 https://github.com/comfyanonymous/ComfyUI |
| **GPT-SoVITS** | 方案A: CPU 推理 (能用，慢)<br>方案B: ROCm 版 (Linux only) |

> 适配包中的 `comfyui_call.py` 已把所有 `torch.cuda.empty_cache()` 换成 GPU 无关的 `safe_empty_cache()`。但 ComfyUI 本身的模型推理仍需 AMD 兼容 torch。

---

## 文件清单

```
AMD_GPU/
├── README.md                          ← 本文件
├── README_EN.md                       ← English version
├── start.ps1                          ← 覆盖: Vulkan 参数启动 llama
├── setup-llama.ps1                    ← 覆盖: 硬件检测加 AMD 分支
└── skills/
    ├── shared/
    │   ├── llama_lifecycle.py         ← 覆盖: VRAM 检测 GPU 无关化
    │   └── restart_llama_degraded.ps1 ← 覆盖: 去掉 CUDA 参数
    ├── asr/
    │   └── asr_call.py               ← 覆盖: GPU→Vulkan/CPU 自适应
    └── comfyui/
        └── comfyui_call.py           ← 覆盖: empty_cache GPU 无关化
```

---

## 常见问题

**Q: 我的 AMD 显卡能不能跑？**  
A: Vulkan 支持 GCN 及之后的所有 AMD 显卡 (Radeon HD 7000+, RX 400+)。4GB+ VRAM 即可跑 llama。

**Q: Intel Arc 能用吗？**  
A: 可以。Intel Arc 支持 Vulkan，同样下载 Vulkan 版 llama.cpp。

**Q: Vulkan 比 CUDA 慢多少？**  
A: 小幅慢 ~10-20%，聊天场景几乎无感知。

**Q: 怎么确认下载的是 Vulkan 版？**  
A: 文件名含 `vulkan`: `llama-bXXXX-bin-win-vulkan-x64.zip`  
   CUDA 版文件名含 `cuda`: `llama-bXXXX-bin-win-cuda-cuXX.X-x64.zip`

**Q: NVIDIA 显卡能用这个吗？**  
A: 不建议。NVIDIA 用户用原版 CUDA 配置更快。
