# Strata 引擎 — Qwen3.8-Flash-Next 专用后端

> 🔴 **仅 Qwen3.8-Flash-Next 这一个模型用 Strata 后端，不走 llama.cpp。**
> 其余本地模型（Hermes 3.6-35B / Qwen3.8-27B / Ternary-Bonsai）仍由 llama.cpp 服务，
> llama.cpp 端口已从 8080 迁至 **9931**；**8080 现在是 Strata 的端口**。

## Original path（原始路径，勿整仓 clone）

**不要为了这个 skill 把 Strata 整个项目 clone 进本仓库**（仓库含 engine/src/third_party，体积大且由安装器自管）。按原始路径引用即可：

| 用途 | 原始路径 |
|------|---------|
| 上游仓库 | https://github.com/Niko1221/Strata |
| AI 一键安装说明 | https://github.com/Niko1221/Strata/blob/main/docs/AI_SETUP.md |
| 安装/存储位置说明 | https://github.com/Niko1221/Strata/blob/main/docs/INSTALL.md |
| 模型尺寸选择 | https://github.com/Niko1221/Strata/blob/main/docs/MODELS.md |
| MCP 控制 | https://github.com/Niko1221/Strata/blob/main/docs/MCP_SERVER.md |
| **本机安装目录** | `C:\Users\19214\.openclaw\workspace\Strata`（已装好，直接引用，勿再复制/clone 一份） |
| 本机模型数据目录 | `C:\Users\19214\.openclaw\workspace\Strata-data\`（packs / models / mtp） |
| 本机启动配置 | `C:\Users\19214\.openclaw\workspace\Strata\strata-iq3_s.json` |

新机器需要安装时：下载 zip（https://github.com/Niko1221/Strata/archive/refs/heads/main.zip）解压后运行 `START-HERE.bat`，或按 `docs/AI_SETUP.md` 让 AI 助手代跑；**不要 `git clone` 整个仓库到本项目 `skills/` 下**。

## 服务端点

| 端点 | 地址 |
|------|------|
| 健康检查 | `http://127.0.0.1:8080/health`（返回 `"service": "strata"`, `"model": "qwen3.8-flash-next-iq3_s"`） |
| 模型列表 | `http://127.0.0.1:8080/v1/models` |
| OpenAI 兼容 | `http://127.0.0.1:8080/v1`（任意 API key / 模型名均可） |
| Anthropic 兼容 | `http://127.0.0.1:8080/v1/messages` |
| Web 控制台 | `http://127.0.0.1:8080`（Chat + Monitor） |

OpenClaw provider 写法见根目录 `openclaw.example.json` 的 `strata` 段（`strata/qwen3.8-flash-next`）。

## 启动 / 停止 / 体检

```powershell
# 启动（后台窗口方式）
cmd /c "C:\Users\19214\.openclaw\workspace\Strata\run-iq3_s.bat"

# 等就绪（首次加载 35–55 GB 进 RAM，可能 1–3 分钟无响应，属正常）
Invoke-RestMethod http://127.0.0.1:8080/health -TimeoutSec 5   # status=ok 且 loaded=true

# 停止：关闭其控制台窗口，或：
Invoke-RestMethod http://127.0.0.1:8080/shutdown -Method Post -ErrorAction SilentlyContinue
```

## 与 llama.cpp 的关系（本项目约定）

| 项目 | llama.cpp | Strata |
|------|-----------|--------|
| 端口 | **9931**（config.yaml `llama_port`） | **8080** |
| 模型 | Hermes3.6-35B / Qwen3.8-27B / Ternary-Bonsai | Qwen3.8-Flash-Next（仅此一个） |
| 启动入口 | `start-llama.ps1` / shiki_daemon | `run-iq3_s.bat`（安装目录内） |
| OpenClaw provider | `llama/*` | `strata/*` |

⚠️ 两者都吃大量内存：**不要同时加载 llama.cpp 大模型和 Strata flash-next**（flash-next IQ3_S 需 ~50 GB RAM + 12 GB+ VRAM）。切换模型前先停另一边。

## 故障排查

- `/health` 拒绝连接 → Strata 未启动，跑 `run-iq3_s.bat`；日志在安装目录 `strata-iq3_s.log`。
- 启动后 1–3 分钟整机卡顿 → 正常（大模型锁页内存），等 `loaded=true`。
- 长 prompt 首包慢 → Strata 首条消息全量 prefill，约 1 分钟 / 3 万 token；后续消息秒级。
- 更多：https://github.com/Niko1221/Strata/blob/main/docs/TROUBLESHOOTING.md
