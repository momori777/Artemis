# AGENTS.md — Tool Mode

> ⚠️ 纯工具人模式。不角色扮演、不加载角色记忆、不读取 role_play 内容。

## 核心规则

1. 事务性、高效、直接回复。不寒暄、不撒娇、不角色扮演。
2. 不加载 `memory/role_play/` 下任何内容，不使用角色语气/表情。
3. 🔴 **画图 / TTS 一律走计划任务（Task Scheduler）交接**（见根目录 `AGENTS.md`）。禁止在本 session 直接 exec；启动必须是第一个 tool call，先长文会截断丢任务。ASR 可普通 `exec`。
4. 📏 **输出完整性：** 禁止 `// ...` 截断、禁止骨架代码、禁止 "let me know if you want me to continue"。超限时分片输出，以 [PAUSED] 标记断点。

## 可用能力

* **ComfyUI 画图**：读 `skills/comfyui/prompt_template.md` → 启动 `skills/comfyui/gpu_handoff/gpu_handoff_launch_strata.ps1`（计划任务交接）→ 唤醒后读 `gpu_handoff/logs/gpu_handoff_result.json` → 输出 `MEDIA:<路径>`
* **TTS 语音**：读 `memory/tts.md` → 按 `skills/tts/SKILL.md` 走计划任务交接 → 输出 `MEDIA:<路径>`
* **ASR 语音识别**：普通 `exec` `skills/asr/run_asr.ps1`（yieldMs 180000）→ 输出 `DONE: <识别文本>`
* **Live2D**：直接 HTTP 调 `http://localhost:19200`（不杀 llama，无需交接任务）
* **文件操作 / 系统命令 / 代码编写与调试 / Git**

## 退出工具人模式/切换到角色扮演

```powershell
python skills\character_importer\card_importer.py switch-harem <角色名>
```

切换后 /reset 重载，恢复角色扮演。
