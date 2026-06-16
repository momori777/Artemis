# AMD GPU Adaptation Pack

> **How to use**: Copy all files from this folder to the project root (`D:\AI_Girlfriend\`), overwriting existing ones.
>
> ⚠️ Back up original files first in case you want to switch back to NVIDIA.

---

## What This Does

This pack switches llama.cpp from CUDA to **Vulkan** backend and adapts all related scripts. Vulkan is a cross-platform GPU API that works on AMD, Intel, and NVIDIA GPUs.

| Component | Change |
|-----------|--------|
| **llama.cpp** | CUDA → Vulkan backend |
| **start.ps1** | Removed `--flash-attn`/`-ctk`/`-ctv`, ngl → 99 |
| **llama_lifecycle.py** | GPU-agnostic VRAM detection (CUDA → vulkaninfo → WMI → fallback) |
| **restart_llama_degraded.ps1** | Removed CUDA-only args |
| **ComfyUI (comfyui_call.py)** | `torch.cuda.empty_cache()` → `safe_empty_cache()` (GPU-agnostic) |
| **ASR (asr_call.py)** | GPU detection: CUDA/HIP → Vulkan → CPU three-tier fallback |
| **TTS (tts_call.py)** | No changes needed — uses no CUDA directly; llama part handled by lifecycle |
| **setup-llama.ps1** | Added AMD hardware detection, Vulkan binary recommendation |

---

## What You Still Need to Do

### 1. Download Vulkan llama.cpp

🔗 https://github.com/ggml-org/llama.cpp/releases

Find `llama-bXXXX-bin-win-vulkan-x64.zip`. **Do NOT download the CUDA version.**
Extract and update `llama_exe` path in `config.yaml`.

### 2. Update config.yaml

```yaml
# Update these two lines:
llama_exe: "D:\\your_path\\llama-bXXXX-bin-win-vulkan-x64\\llama-server.exe"
restart_script: "D:\\your_path\\restart-llama.ps1"
```

### 3. ComfyUI + GPT-SoVITS — Each Needs AMD-Compatible torch

These tools use PyTorch for inference and **need AMD GPU-compatible torch** (not covered by this pack):

| Tool | Solution |
|------|----------|
| **ComfyUI** | Option A: DirectML version<br>Option B: ZLUDA translation layer<br>🔗 https://github.com/comfyanonymous/ComfyUI |
| **GPT-SoVITS** | Option A: CPU inference (works, slow)<br>Option B: ROCm version (Linux only) |

> This pack's `comfyui_call.py` already replaces all `torch.cuda.empty_cache()` calls with GPU-agnostic `safe_empty_cache()`. But ComfyUI's model inference still needs AMD-compatible torch.

---

## File List

```
AMD_GPU/
├── README.md                          ← 中文说明
├── README_EN.md                       ← This file
├── start.ps1                          ← Overwrite: Vulkan llama startup
├── setup-llama.ps1                    ← Overwrite: AMD hardware detection
└── skills/
    ├── shared/
    │   ├── llama_lifecycle.py         ← Overwrite: GPU-agnostic VRAM detection
    │   └── restart_llama_degraded.ps1 ← Overwrite: CUDA args removed
    ├── asr/
    │   └── asr_call.py               ← Overwrite: GPU→Vulkan/CPU adaptive
    └── comfyui/
        └── comfyui_call.py           ← Overwrite: empty_cache GPU-agnostic
```

---

## FAQ

**Q: Will my AMD GPU work?**  
A: Vulkan supports all AMD GPUs from GCN onward (Radeon HD 7000+, RX 400+). 4GB+ VRAM recommended.

**Q: What about Intel Arc?**  
A: Yes, Intel Arc supports Vulkan. Download the Vulkan llama.cpp binary.

**Q: Is Vulkan slower than CUDA?**  
A: Slightly (~10-20%), but barely noticeable in chat scenarios.

**Q: How do I tell Vulkan vs CUDA binaries apart?**  
A: Vulkan: `llama-bXXXX-bin-win-vulkan-x64.zip`  
   CUDA: `llama-bXXXX-bin-win-cuda-cuXX.X-x64.zip`

**Q: I have an NVIDIA GPU. Should I use this?**  
A: No. NVIDIA users should use the original CUDA config — it's faster on NVIDIA GPUs.
