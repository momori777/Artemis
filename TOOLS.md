# TOOLS.md — 能力中枢（速查版）

> AGENTS.md 是完整版，这个是精简速查。角色切换不改这个文件。

## 串行规则

TTS/ComfyUI 停 llama-server，ASR 不杀 llama（Whisper 独立显存 ~1.5GB）。
TTS 和 ComfyUI 不能同时 spawn，ASR 可随时 spawn。全部用 sessions_spawn(mode="run")。
必须等前一个 DONE: 后才 spawn 下一个停 llama 的 skill。

## ComfyUI 画图

读 `skills/comfyui/prompt_template.md` -> 写 prompt -> spawn 子 session 跑 PS 脚本。

## ASR 语音识别

用户发语音消息 → spawn 子 session 跑 `skills/asr/run_asr.ps1` → 收到文本后当对话输入。
不杀 llama，Faster-Whisper small ~1.5GB VRAM，8GB 卡共存。

## TTS 语音

读 `memory/tts.md` -> spawn 子 session 跑 `skills/tts/run_tts.ps1`
语言: ja(默认)/zh/en  情绪: casual/tsundere/romantic/long/random

## Live2D

不杀 llama，直接 exec HTTP。详细 motion 表见 `skills/live2d/SKILL.md`
速查: Idle(日常) | Tap摸头(害羞) | Tap外框(傲娇) | Tap摸手(深情) | Start(登场) | Leave(退场)

## 角色记忆

`memory/role_play/<角色名>/` 下按日期存 markdown。
当前活跃角色 = SOUL.md 第一行声明的名字。

## 角色切换

```powershell
python skills\character_importer\card_importer.py switch "card.png" --force
python skills\character_importer\card_importer.py switch-harem natsume
```

切换后 /reset 重新加载。
