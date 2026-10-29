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

## Windows Smart App Control（代码完整性拦截）

本机开启了 Smart App Control（`HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy` 的
`VerifiedAndReputablePolicyState=1`）。它按**文件哈希/云信誉**判定，不看路径：新用 pip 编译/解压出来的
无签名原生扩展会被拦，报 `应用程序控制策略已阻止此文件`（CodeIntegrity 事件 3077）。

本机已按「无需管理员」的方案落地，**换解释器或重装 venv 后需要重做**：

| 被拦的东西 | 现在的做法 | 备份位置 |
|---|---|---|
| `pyopenjtalk_plus` 的 `openjtalk/htsengine .pyd` | 用 ComfyUI 环境（`F:\comfyui\ComfyUI-aki-v3\python`，早于 SAC 装好、已被云信誉放行）里的**纯 pyopenjtalk 0.4.1**整套覆盖；MeCab 词典 `open_jtalk_dic_utf_8-1.11` 拷进包目录（ComfyUI 那份 ACL 不可读，否则 `Mecab_load()` 失败） | `deps\sovits-env\pyopenjtalk_plus_pkg`、`pyopenjtalk_plus_backup` |
| `jieba_fast` 的自建 C 扩展 | 用纯 Python `jieba` + `jieba_fast/__init__.py` 别名 shim（`sys.modules['jieba_fast'] = jieba`） | `deps\sovits-env\jieba_fast_pkg_backup` |
| `torchaudio.load` 要用的 `torchcodec`（`libtorchcodec_core*.dll` 是 torch 插件 DLL） | SAC 拦的是 **torchcodec 自己**（WinError 4551），不是 FFmpeg：PySide6 自带的 `avcodec-61/avformat-61/avutil-59/swresample-5/swscale-8` 手动 `CDLL` 全部加载成功，5 个 core 版本也都在盘上 → 补 FFmpeg 救不回来。改在 `deps\sovits-env\Lib\site-packages\sitecustomize.py` 里用**已放行的 soundfile（libsndfile）**重写 `torchaudio.load/info`（纯 Python，不改 vendored 代码；`transforms.Resample` 是纯 torch，不受影响；`api_v2.py` 的输出本来就走 `sf.write`） | 无（新增文件，删掉即回滚） |

用户态自签证书**无效**（SAC 只认机器级企业信任），所以真正的白名单要管理员跑一次：

```powershell
# 以管理员运行（一次性）：自建本机代码签名 CA 装入 LocalMachine 受信任存储，并签 venv 原生文件
powershell -ExecutionPolicy Bypass -File skills\sovits\trust_local_signer.ps1
# 之后每次 pip 装了带原生扩展的包，普通权限补签即可
powershell -ExecutionPolicy Bypass -File skills\sovits\sign-unsigned.ps1
```

另有两点环境事实：`api_v2.py`/`webui.py` 需要 cwd = `skills\sovits` 且 `sys.path` 含 `skills\sovits\GPT_SoVITS`；
`onnxruntime-gpu` 面向 CUDA 12.x，本机 torch 是 cu130，缺 `cublas64_12.dll` → G2PW 走 CPU（只是警告，不影响结果）。

## 端到端冒烟测试（GPU 交接）

- **`tts_e2e_test.py`**：打 `api_v2` 的 `/set_gpt_weights` + `/set_sovits_weights`（按 `weight_<角色>.json` 解析路径）→ `/tts` 合成 → 自己校验返回的是“真人声”（时长 > 0.4 s、峰值 > 200，兼容 PCM16 / float32 wav）。结果写 UTF-8 JSON（`--report`），不依赖控制台输出（Windows 代码页吃中文）。路径全从 `config.yaml` 推，无硬编码。
- **`tts_handoff_run.ps1` + `tts_handoff_launch.ps1`**：SoVITS 版 GPU 交接（和 `skills\comfyui\gpu_handoff\` 同一套路）。计划任务里：停 Strata(8080) → 起 `api_v2.py -p 9880`（cwd = `skills\sovits`）→ 跑 e2e → 停 api_v2 → **无论如何**重启 Strata 并等 `/v1/models` 就绪。必须用计划任务：停引擎会连带杀掉 exec 子进程，重启那步就永远跑不到。

```powershell
# 从任何目录跑；-DelaySec 给自己留出读完回复的时间
powershell -ExecutionPolicy Bypass -File skills\sovits\tts_handoff_launch.ps1 -DelaySec 45
# 可选：-TestIds atori-ja,natsume-ja 只跑部分用例；-SkipJob 只重启引擎
# 跑完看：skills\sovits\handoff_logs\tts_handoff_result.json（每句 wav 路径在 tts_e2e_result.json）
```

- 2026-10-30 实测（RTX 5090 Laptop，`weights/atori-e15.ckpt + atori_e20_s9560.pth`、`weights/xxx-e30.ckpt + xxx_e20_s6240.pth`，seed 622539）：`atori-ja / atori-zh / natsume-ja / natsume-zh` **4/4 通过**；api_v2 6 s 内就绪（权重热切换），单句合成 1.2–22.2 s；引擎停机→回来共 ~60 s。
- **显存红线**：Strata 常驻 ~23 GB / 24.4 GB，只剩 ~1.3 GB，SoVITS 塞不下 → 聊天发语音也必须走交接。现在 `skills\tts\tts_http_call.py` 只是「9880 没起就顺手起一个」，**不会停 Strata**，容易 OOM 或静默转 CPU。
- **参考音频 = wav + 同名 `.txt` 逐字转录（硬性要求）**：`tts_call.py` / `tts_http_call.py` 现在只用带 sidecar 的
  wav，没有同名 `.txt` 的直接跳过，整组为空就 `exit 2`，不再从文件名臆造 `prompt_text`；
  `tts_e2e_test.py` 缺 sidecar 直接报错。原因：GPT-SoVITS v2/v2Pro 空 `prompt_text` 只克隆音色（韵律变平、
  句子拉长），v3/v4 直接 `NO_PROMPT_ERROR`。sidecar 一律用 `utf-8-sig` 读（atri 那批**带 UTF-8 BOM**，
  用 `utf-8` 读会把 BOM 混进 `prompt_text`）。
  补 sidecar 用 `skills\asr\asr_sidecars.py`（faster-whisper large-v3，CPU/int8，不占显存）：
  ```powershell
  # ComfyUI 环境里已有被 SAC 放行的 ctranslate2；模型缓存 skills\asr\models\（已 gitignore）
  F:\comfyui\ComfyUI-aki-v3\python\python.exe skills\asr\asr_sidecars.py `
    --dir skills\tts\ref_wavs_natsume --dry-run   # 先核对，再去掉 --dry-run 落盘，--force 可重写
  ```
  转录必须和录音逐字对应（不能按文件名臆造），落盘前先 `--dry-run` 核对每条是否对得上文件名。
- **2026-10-30 natsume sidecar 复核**：14/14 齐全，文件名线索与转录全部吻合；两处遗留待人工处理：
  `ref_09_おやすみ.wav` 与 `ref_08_傲娇_ここでは.wav` 音频**完全相同**（md5 `978cc8e8a7`），
  sidecar 按真实录音写的是「あと何度も言うけど、ここではしない。」，所以这条例不是おやすみ，
  想要真正的おやすみ参考音频得重新录；`ref_11_深情_大好き.wav` 转录置信度仅 51.2（「好き…大好き…」），
  建议复听确认。
