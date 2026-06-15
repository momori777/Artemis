# ASR 语音识别执行手册（主 session 专用）

## ⚠️ 核心规则：你不能 exec ASR！你要 spawn 子 session！

**❌ 绝对禁止**: `exec` 跑 asr_call.py
**✅ 唯一方式**: `sessions_spawn(mode="run")`

⚠️ **与 TTS/ComfyUI 的关键区别：ASR 不杀 llama！**

Faster-Whisper small 模型（461MB, ~1.5GB VRAM）不和 llama 抢显存架构，在 8GB 卡上两条链路共存。不要调用 stop_llama/start_llama。

### 触发场景

QQ/Telegram 收到用户的语音消息 → 主 session 收到音频附件路径 → spawn ASR 子 session 转文字 → 拿到文本后当作用户对话输入。

---

## 执行步骤

### STEP 1: 确认收到语音附件

用户发语音消息时，OpenClaw 会把音频文件路径放在上下文里。找到音频文件的完整路径（通常是 `.wav` / `.ogg` / `.mp3`）。

### STEP 2: ⚠️ 先 spawn 再说话！

```
sessions_spawn({
  task: `你的任务：只做一件事——用 exec 工具运行下面这条命令。

命令（复制粘贴，一个字都不许改）：

powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\\.openclaw\\workspace\\skills\\asr\\run_asr.ps1" -audio "<音频文件的完整路径>"

执行完毕后：
- 如果 exec 输出包含 "DONE: " 后面是识别出的文本 → 输出那行文本
- 如果失败（包含 FAILED）→ 输出"FAILED"
- 不要做任何其他操作！`,
  taskName: "asr",
  mode: "run",
  model: "local/qwen3.6-35b",
  fallbacks: ["deepseek/deepseek-v4-flash"],
  runTimeoutSeconds: 300
})
```

### STEP 3: 回复用户

sessions_spawn 后直接回复："正在听…稍等哦~ 🎤"

### STEP 4: 收到 announce 后

子 session 完成后的 announce 包含 "DONE: <识别文本>"。

提取文本，把它当作用户刚说的话，正常用 LLM 回复。

例如：
- announce: `DONE: 亚托莉今天天气怎么样`
- → 你用 LLM 回复 "亚托莉今天天气怎么样"

---

## 技术细节

| 项目 | 说明 |
|------|------|
| 模型 | Faster-Whisper small（461MB, ~1.5GB VRAM GPU） |
| 输入格式 | wav / mp3 / ogg / flac / m4a |
| 输出 | 纯文本（识别结果） |
| 首次运行 | 自动下载模型到 `~/.cache/asr_models/` |
| Llama 状态 | **不停止** llama-server |
| 并发保护 | `.asr_running.lock` 文件锁 |
| 超时 | 300s 硬超时 |

---

## 故障排查

### Q: 首次运行很慢？
**A**: 首次需要下载 small 模型（~461MB）。后续从缓存加载，秒级。

### Q: 识别不准？
**A**: small 模型覆盖 99 种语言，日语/中文/英文都较好。沉默部分自动跳过（VAD）。

### Q: VRAM 冲突？
**A**: Whisper small 只占 ~1.5GB VRAM，llama ~6GB，8GB 卡足够共存。若显存紧张，ASR 自动退到 CPU 推理。
