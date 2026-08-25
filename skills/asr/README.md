# ASR 语音识别 Skill / ASR (Speech Recognition) Skill

## 中文

基于 Faster-Whisper small 的语音识别技能，用于把 QQ/Telegram/WebChat 收到的语音消息转成文字。

- **模型**：Faster-Whisper small（461MB，约 1.5GB VRAM），首次运行自动下载到 `~/.cache/asr_models/`
- **显存**：与 llama-server 共存，**不杀 llama**，无需 sessions_spawn 腾显存流程
- **入口**：`run_asr.ps1 -audio <音频路径>`（wav / mp3 / ogg / flac / m4a）
- **并发保护**：`.asr_running.lock` 文件锁；300s 硬超时

### 文件结构

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 主 session 执行手册（spawn 子 session 调 ASR） |
| `asr_call.py` | 推理脚本（自动下载模型、VAD 跳静音） |
| `run_asr.ps1` | PowerShell 包装脚本，输出 `DONE: <文本>` |

### 快速使用

```powershell
powershell -ExecutionPolicy Bypass -File skills\asr\run_asr.ps1 -audio "C:\path\to\audio.wav"
# 成功输出: DONE: <识别出的文本>
# 失败输出: FAILED
```

## English

Speech recognition skill based on Faster-Whisper small, used to transcribe voice messages received via QQ/Telegram/WebChat.

- **Model**: Faster-Whisper small (461MB, ~1.5GB VRAM), auto-downloaded on first run to `~/.cache/asr_models/`
- **VRAM**: Coexists with llama-server, **does NOT kill llama**, no VRAM-freedom spawn flow needed
- **Entry**: `run_asr.ps1 -audio <audio-path>` (wav / mp3 / ogg / flac / m4a)
- **Concurrency**: `.asr_running.lock` file lock; 300s hard timeout

### Files

| File | Description |
|------|-------------|
| `SKILL.md` | Main-session execution manual (spawn a sub-session to run ASR) |
| `asr_call.py` | Inference script (auto model download, VAD silence skipping) |
| `run_asr.ps1` | PowerShell wrapper, prints `DONE: <text>` |

### Quick Start

```powershell
powershell -ExecutionPolicy Bypass -File skills\asr\run_asr.ps1 -audio "C:\path\to\audio.wav"
# Success: DONE: <transcribed text>
# Failure: FAILED
```
