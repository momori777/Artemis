# gpu_handoff — 整卡显存交接（停 LLM → 跑 ComfyUI → 重启 LLM）

本机只有一张 GPU。LLM 引擎（Strata，端口见 `config.yaml` 的 `strata_port`）常驻把显存占满，
ComfyUI（默认 `8188`）此时起不来 —— 这是正常现象，不是坏了。
需要整卡独占的活（大工作流 / 高 batch / 训练）只能按固定顺序：**停 LLM → 跑 ComfyUI → 重启 LLM**。

普通画图不用走这里：`skills/comfyui/run_comfyui.ps1` 那套照旧（`sessions_spawn` 里跑）。

## 为什么不能直接 exec

`gpu_handoff_run.ps1` 会杀掉正在答话的 LLM 引擎。挂在 agent 当前 turn 的 `exec` 下，
调用方进程跟着死，`finally` 里的「重启 LLM」可能永远跑不到 —— 引擎就再也起不来了。
所以必须用 `gpu_handoff_launch.ps1` 注册一次性计划任务，进程归 Task Scheduler 所有。

## 用法

```powershell
# 默认：跑本目录 workflow_sdxl_example.json，45 秒后触发
powershell -ExecutionPolicy Bypass -File skills/comfyui/gpu_handoff/gpu_handoff_launch.ps1

# 指定工作流和文件名前缀
powershell -ExecutionPolicy Bypass -File skills/comfyui/gpu_handoff/gpu_handoff_launch.ps1 `
  -WorkflowJson <api格式工作流.json> -Prefix myjob -DelaySec 30

# 只把引擎拉回来（上一步失败 / 手动收尾）
powershell -ExecutionPolicy Bypass -File skills/comfyui/gpu_handoff/gpu_handoff_launch.ps1 -SkipJob -DelaySec 5
```

触发后 agent 失联 1～3 分钟，期间不要重复发指令。回来看结果：

- `logs/gpu_handoff_result.json` → `{"status":"ok","image":"<png 路径>","note":"","finished":"..."}`
- `logs/gpu_handoff_run.log` → 完整时间线
- `logs/comfyui.log` / `comfyui.log.err` → ComfyUI 自身日志

实测（2026-10-20，832×1216 / 25 步单图）：全程约 2 分 18 秒，其中 LLM 不可用约 70 秒。

## 路径从哪来（仓库里不写绝对路径）

脚本本身不含任何绝对路径，全部从仓库根 `config.yaml`（已 gitignore）读：

| 用途 | config.yaml 键 | 缺省值 |
|---|---|---|
| ComfyUI 安装目录 | `comfyui_root` | `deps/ComfyUI` |
| ComfyUI 的 Python | `comfyui_python` | `python` |
| ComfyUI 端口 | `comfyui_port` | `8188` |
| LLM 引擎安装目录 | `strata_dir` | 必填（见 `skills/strata/SKILL.md`） |
| 引擎启动配置 | `strata_config` | 必填，可写相对 `strata_dir` 的路径 |
| LLM 端口 | `strata_port` | `8080` |

换机器 / 换安装位置只改 `config.yaml`，脚本不用动；也可用 `-ComfyRoot` / `-StrataDir` / `-StrataConfig` 临时覆盖。

## 硬性注意

1) 工作流必须是 **API 格式**（`{"1":{"class_type":...}}`），不是 UI 导出的 `nodes/links` 格式。
2) `-Prefix` 必须等于工作流里 `SaveImage.inputs.filename_prefix`，否则找不到出图。
3) 脚本只按命令行匹配杀进程（`serve/server.py`、`main.py`），不会误伤 llama.cpp（`llama_port`，默认 `9931`）。
4) `finally` 无条件重启引擎并自删计划任务；中途失败也会把 LLM 拉回来。
5) 任务名默认 `ComfyGpuHandoff`，同名任务会被先删后建；并行跑请传不同 `-TaskName`。

## 失败排查

| 现象 | 处理 |
|---|---|
| `config.yaml has no strata_dir` | 在 `config.yaml` 补 `strata_dir` / `strata_config`（Strata 安装目录，安装器自管，不在本仓库内） |
| `ComfyUI did not come up on 8188` | 看 `logs/comfyui.log.err`；多为显存没释放干净（再等 60 s）或 `comfyui_python` 环境缺 torch |
| `workflow did not finish within 900 s` | 工作流太大 / 节点报错，同样看 `comfyui.log.err` |
| `finished but no <prefix>*.png` | `-Prefix` 与 `filename_prefix` 不一致，或出图目录不是 `comfyui_root/output` |
| LLM 没回来 | `powershell -File skills/comfyui/gpu_handoff/gpu_handoff_launch.ps1 -SkipJob -DelaySec 5` |
