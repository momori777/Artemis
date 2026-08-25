# GPT-SoVITS 引擎 / GPT-SoVITS Inference Engine

## 中文

项目内置的 GPT-SoVITS 推理引擎（clone 仓库即包含全部代码），TTS 功能不依赖任何外部绝对路径或 config.yaml。

- **服务入口**：`api_v2.py` — 流式 TTS HTTP 服务（FastAPI，端口 9880，`/tts` 端点）
- **备用入口**：`api.py` / `webui.py`
- **引擎核心**：`GPT_SoVITS/`（TTS_infer_pack / module / text / AR 等）
- **角色权重**：`weights/`（gitignore，需手动补齐，见 `SETUP.md`）
- **权重索引**：`weight.json` / `weight_<角色>.json`（相对 weights/ 路径）

### 目录结构

```
skills/sovits/
├── api_v2.py                 # 流式 TTS HTTP 服务（FastAPI，端口 9880，/tts 端点）
├── api.py / webui.py         # 备用入口
├── GPT_SoVITS/               # 引擎核心
│   ├── TTS_infer_pack/TTS.py # 推理管线（已修复 CPU fp16/float32 + torchaudio 兼容）
│   ├── configs/tts_infer.yaml
│   └── pretrained_models/    # ⚠️ gitignore（底模需手动补齐）
├── tools/                    # i18n / audio_sr / AP_BWE_main
├── weights/                  # ⚠️ gitignore —— 角色权重放这里
├── weight.json / weight_<角色>.json   # 权重索引
├── start-api.ps1             # 手动启动脚本
└── requirements.txt
```

### 启动

```powershell
# 自动（推荐）：由 tts_http_call.py 探测并自动启动
py skills\tts\tts_http_call.py "こんにちは" ja casual

# 手动：
cd skills\sovits
<python> api_v2.py -a 127.0.0.1 -p 9880
# 默认加载 custom 段（sakura）；运行时热切换：
#   GET /set_gpt_weights?weights_path=weights/xxx-e30.ckpt
#   GET /set_sovits_weights?weights_path=weights/xxx_e20_s6240.pth
```

### 权重补齐（约 4.5GB）

详见 `SETUP.md`。权重和 pretrained 模型被 gitignore（太大不进仓库）。

### 兼容性说明

- Python 解释器：使用 config.yaml `sovits_python`（有则用），否则系统 python
- 无 config.yaml 时全部路径从 `__file__` 推导（自包含模式）
- 已修复：CPU fp16/float32 冲突、torchaudio 2.9+ 无 set_audio_backend、
  torchcodec 缺 FFmpeg（用 soundfile 替代）、api_v2 无 `/` 路由探测失败

## English

Self-contained GPT-SoVITS inference engine built into the project (cloning the repo includes all code). TTS has no dependency on external absolute paths or config.yaml.

- **Service entry**: `api_v2.py` — streaming TTS HTTP service (FastAPI, port 9880, `/tts` endpoint)
- **Fallback entries**: `api.py` / `webui.py`
- **Engine core**: `GPT_SoVITS/` (TTS_infer_pack / module / text / AR, etc.)
- **Character weights**: `weights/` (gitignored, must be populated manually; see `SETUP.md`)
- **Weight indexes**: `weight.json` / `weight_<char>.json` (paths relative to weights/)

### Directory Layout

```
skills/sovits/
├── api_v2.py                 # Streaming TTS HTTP service (FastAPI, port 9880, /tts)
├── api.py / webui.py         # Fallback entries
├── GPT_SoVITS/               # Engine core
│   ├── TTS_infer_pack/TTS.py # Inference pipeline (CPU fp16/float32 + torchaudio fixes applied)
│   ├── configs/tts_infer.yaml
│   └── pretrained_models/    # ⚠️ gitignored (base models must be added manually)
├── tools/                    # i18n / audio_sr / AP_BWE_main
├── weights/                  # ⚠️ gitignored — character weights go here
├── weight.json / weight_<char>.json   # Weight indexes
├── start-api.ps1             # Manual start script
└── requirements.txt
```

### Starting

```powershell
# Automatic (recommended): probed and started by tts_http_call.py
py skills\tts\tts_http_call.py "hello" ja casual

# Manual:
cd skills\sovits
<python> api_v2.py -a 127.0.0.1 -p 9880
# Loads the custom section (sakura) by default; hot-swap at runtime:
#   GET /set_gpt_weights?weights_path=weights/xxx-e30.ckpt
#   GET /set_sovits_weights?weights_path=weights/xxx_e20_s6240.pth
```

### Populating Weights (~4.5GB)

See `SETUP.md`. Weights and pretrained models are gitignored (too large for the repo).

### Compatibility Notes

- Python interpreter: uses config.yaml `sovits_python` if present, otherwise system python
- Without config.yaml, all paths are derived from `__file__` (self-contained mode)
- Fixed: CPU fp16/float32 conflicts, torchaudio 2.9+ missing set_audio_backend,
  torchcodec missing FFmpeg (soundfile used instead), api_v2 missing `/` route probe
