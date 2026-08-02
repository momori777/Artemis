# GPT-SoVITS 自包含说明

`skills/sovits/` 是**项目内置**的 GPT-SoVITS 引擎（clone 仓库即包含全部代码），
TTS 功能不依赖任何外部绝对路径或 config.yaml。

## 目录结构

```
skills/sovits/
├── api_v2.py                 # 流式 TTS HTTP 服务（FastAPI，端口 9880，/tts 端点）
├── api.py / webui.py         # 备用入口
├── GPT_SoVITS/               # 引擎核心（TTS_infer_pack / module / text / AR 等）
│   ├── TTS_infer_pack/TTS.py # 推理管线（已修复 CPU fp16/float32 + torchaudio 兼容）
│   ├── configs/tts_infer.yaml
│   └── pretrained_models/    # ⚠️ gitignore（chinese-hubert-base / roberta / v2Pro 底模 / sv）
├── tools/                    # i18n / audio_sr / AP_BWE_main
├── weights/                  # ⚠️ gitignore —— 角色权重放这里
│   ├── Sakura-e15.ckpt       # sakura GPT 权重
│   ├── Sakura_e8_s7176.pth   # sakura SoVITS 权重
│   └── xxx-e30.ckpt / xxx_e20_s6240.pth  # 默认权重
├── weight.json / weight_<角色>.json   # 权重索引（相对 weights/ 路径）
├── start-api.ps1             # 手动启动脚本
└── requirements.txt
```

## clone 后如何补齐权重（约 4.5GB）

权重和 pretrained 模型被 gitignore（太大不进仓库）。两种方式：

### 方式 A：从现成引擎复制（推荐）
```powershell
# 从已有 GPT-SoVITS v2Pro 目录复制到项目内：
Copy-Item <引擎根>\GPT_weights_v2Pro\*.ckpt  skills\sovits\weights\
Copy-Item <引擎根>\SoVITS_weights_v2Pro\*.pth skills\sovits\weights\
Copy-Item <引擎根>\GPT_SoVITS\pretrained_models\chinese-hubert-base       skills\sovits\GPT_SoVITS\pretrained_models\ -Recurse
Copy-Item <引擎根>\GPT_SoVITS\pretrained_models\chinese-roberta-wwm-ext-large skills\sovits\GPT_SoVITS\pretrained_models\ -Recurse
Copy-Item <引擎根>\GPT_SoVITS\pretrained_models\v2Pro                    skills\sovits\GPT_SoVITS\pretrained_models\ -Recurse
Copy-Item <引擎根>\GPT_SoVITS\pretrained_models\sv\*                     skills\sovits\GPT_SoVITS\pretrained_models\sv\
```

### 方式 B：官方渠道下载
- 引擎：https://github.com/RVC-Boss/GPT-SoVITS
- pretrained：官方 release 的 `GPT_SoVITS/pretrained_models/` 下
  `chinese-hubert-base`、`chinese-roberta-wwm-ext-large`、`v2Pro/`、`sv/`
- 角色权重：对应角色包的 GPT/SoVITS v2Pro 权重

## 启动

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

## 兼容性说明

- Python 解释器：使用 config.yaml `sovits_python`（有则用），否则系统 python
  （需装有 torch/torchaudio/soundfile/wordsegment 等依赖）
- 无 config.yaml 时全部路径从 `__file__` 推导（自包含模式）
- 已修复：CPU fp16/float32 冲突、torchaudio 2.9+ 无 set_audio_backend、
  torchcodec 缺 FFmpeg（用 soundfile 替代）、api_v2 无 `/` 路由探测失败
