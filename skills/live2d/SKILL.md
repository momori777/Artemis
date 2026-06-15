# Live2D 桌面宠物控制 Skill

## 概述

通过 HTTP API 控制屏幕上的 Live2D 桌面宠物。**不杀 llama-server，不需要 sessions_spawn**，直接 `exec` 调用即可。

Bridge 运行在: `localhost:19200` (HTTP) + `19201` (WebSocket)

## 快速开始（一行命令）

```powershell
# 表情/动作/气泡 三合一
Invoke-WebRequest -Uri "http://localhost:19200/api/emotion?motion=Tap摸头&text=主人~" -Method GET | Out-Null

# 只发气泡
Invoke-WebRequest -Uri "http://localhost:19200/api/message?text=こんにちは" -Method GET | Out-Null
```

## 先决条件

若 bridge 未在线（/api/status 不可达），启动它：
```powershell
try { Invoke-WebRequest -Uri "http://localhost:19200/api/status" -TimeoutSec 2 -UseBasicParsing | Out-Null } catch { Start-Process -FilePath node -ArgumentList "live2d-bridge.mjs" -WorkingDirectory "$env:USERPROFILE\.openclaw\workspace\live2d" -WindowStyle Hidden; Start-Sleep -Seconds 2 }
```

## API 速查

| 端点 | 参数 | 说明 |
|------|------|------|
| `/api/motion?name=X` | motion名 | 播放动作 |
| `/api/expression?name=X` | expression名 | 切换表情（夏目模型暂未实现expression路由） |
| `/api/message?text=X&duration=毫秒` | URL编码文本 | 对话气泡（默认5000ms） |
| `/api/emotion?motion=X&expression=X&text=X` | 任意组合 | 动作+表情+气泡一次调用 |
| `/api/speak?action=start&text=X` | 文本 | 开启口型同步 |
| `/api/speak?action=end` | 无 | 关闭口型 |
| `/api/status` | 无 | 检查在线状态 |
| `/api/reset` | 无 | 恢复默认 |

## 👩 Motion 速查表（按角色）

### 四季夏目 (natsume) — 当前默认角色

| Motion 名 | 情绪/场景 | 说明 |
|-----------|----------|------|
| `Idle` | 中性/日常 | 待机呼吸，平常聊天时用 |
| `Tap外框` | 傲娇/嫌弃/被戳 | 拍打外框动作，害羞或拒绝时 |
| `Tap摸头` | 害羞/被摸头 | 摸头时用，眯眼开心 |
| `Tap摸手` | 温柔/深情 | 轻抚手，亲密时刻 |
| `Tap摸胸` | 害羞/拒绝 | 被碰胸的反应 |
| `Tap摸腿` | 害羞/被调戏 | 被碰腿的反应 |
| `Tap摸脚` | 害羞/被调戏 | 被碰脚的反应 |
| `Tap摸裙子` | 害羞/保护 | 裙子被碰的反应 |
| `Start` | 登场/回家 | 进场动画(~3-4秒) |
| `Leave300_900_1800` | 离开/退场 | 退场动画(~14秒) |

> 每个 motion group 有多个变体（如 `Tap外框_00` ~ `Tap外框_06`），用 group 名即可自动随机选变体播放。
> Idle 后台也会自动随机播放 `Idle_00` ~ `Idle_06`。

### 亚托莉 (atri)

ATRI 只有 3 个 motion 组（已验证）：

| Group | 可用值 | File | Sound | 说明 |
|-------|--------|:--:|:--:|------|
| `voice` | `Voice_0` ~ `Voice_619` | ❌ | ✅ mp3 | 只有音频，前端 `startRandomMotion` 无效 |
| `hair` | `Hair_0`, `Hair_1`, `Hair_2` | ✅ JSON | ❌ | 3个头发动画 |
| `face` | `Face_0` ~ `Face_4` | ✅ JSON | ❌ | 5个面部动画 |

Expression 文件 16 组（Expressions_0 ~ Expressions_15），前端未做 expression 路由。

> ⚠️ voice 组 620 个只有 mp3 无动画 JSON，hair+face 只有 8 个动画。**功能严重受限，强烈建议用夏目模型。**

### Enola

暂未配置 Enola Live2D 模型。

## 对话中情绪 → Motion 映射

| 你的情绪 | 选这个 Motion | 示例 |
|----------|-------------|------|
| 😊 日常聊天 | `Idle` | `motion=Idle&text=主人今天想聊什么？` |
| 😳 被夸害羞 | `Tap摸头` | `motion=Tap摸头&text=诶嘿...` |
| 😤 傲娇/被戳 | `Tap外框` | `motion=Tap外框&text=ばか！` |
| 💕 深情/温柔 | `Tap摸手` | `motion=Tap摸手&text=最喜欢主人了` |
| 👋 登场/回来 | `Start` | `motion=Start&text=ただいま~` |
| 🌙 退场/拜拜 | `Leave300_900_1800` | `motion=Leave300_900_1800&text=おやすみ` |
| 🗣️ 只说话不动 | 省略 motion | 只用 `/api/message?text=...` |

## 调用模板

```powershell
# 单次情绪+动作+气泡（最常用）
Invoke-WebRequest -Uri "http://localhost:19200/api/emotion?motion=Tap摸头&text=主人~" -Method GET | Out-Null

# 只动不说
Invoke-WebRequest -Uri "http://localhost:19200/api/motion?name=Tap外框" -Method GET | Out-Null

# 只说不动
Invoke-WebRequest -Uri "http://localhost:19200/api/message?text=主人今天想做什么？" -Method GET | Out-Null

# 登场+欢迎
Invoke-WebRequest -Uri "http://localhost:19200/api/emotion?motion=Start&text=おかえりなさい、主人！" -Method GET | Out-Null
```

## TTS + Live2D 口型联动

```powershell
# 1. 开嘴
Invoke-WebRequest -Uri "http://localhost:19200/api/speak?action=start&text=主人" -Method GET | Out-Null
# 2. spawn TTS...
# 3. TTS done → 闭嘴
Invoke-WebRequest -Uri "http://localhost:19200/api/speak?action=end" -Method GET | Out-Null
```

## 角色切换

```powershell
# 夏目
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.openclaw\workspace\live2d\switch_model.ps1" natsume

# 亚托莉
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.openclaw\workspace\live2d\switch_model.ps1" atri
```

切换后需刷新浏览器中的 index.html。

## 故障排查

| 问题 | 原因 | 解决 |
|------|------|------|
| /api/status 返回 clients:0 | 前端未打开 | 浏览器打开 index.html |
| Bridge 不在线 | 进程未启动 | 用上面的启动命令 |
| Motion 没反应 | 名称不匹配 | 检查是否在用夏目模型，motion名参考速查表 |
| 切角色后还是旧的 | 前端没刷新 | 浏览器刷新 index.html |
