# Headroom Proxy — mem0 注入 + 上下文压缩管线

`artemis_headroom_proxy.py` 起的本地代理（默认 19251）。走它的请求会自动
注入角色记忆并压缩历史，无需手动调用。

## 路由

```
OpenClaw Gateway
  ├─ <provider>/<model-id>     → 直连原始后端（不走 proxy）
  ├─ local-llama/llama-local   → proxy → 本地 llama-server
  └─ local-llama/<model-id>    → proxy → 原始后端（云端模型）
                                   │
                                   ├─ [1] mem0 记忆注入（Qdrant 向量搜索）
                                   ├─ [2] SmartCrusher 压缩历史
                                   └─ [3] 转发到真实后端
```

真实后端地址存在 sidecar 路由文件里（`headroom_routes.json`，位于 OpenClaw
配置目录），proxy 按 model id 查表。

## 什么时候走 proxy

| 场景 | model 字段 | 走 proxy |
|---|---|---|
| 角色扮演对话 | `local-llama/*` | 是（记忆注入 + 压缩） |
| 工具人 / 事务性 | `<provider>/<model-id>` | 否（直连省延迟） |
| 子任务 spawn | `local/<model-id>` | 否 |

原则：需要角色记忆和上下文压缩的对话走 `local-llama/*`，纯工具操作走原始
provider。

## 自动配置

`start.ps1` 启动 proxy 后会扫描 OpenClaw 配置，**只加不改**：新增
`local-llama` provider 并把现有云端模型复制到其下，原始 provider 保持原样，
原始 baseUrl 存入 sidecar 路由文件。clone 后无需手工配置。

## SmartCrusher 参数

定义在 `skills/shared/context_trimming.py`：

| 参数 | 值 | 说明 |
|---|---|---|
| `RECENT_FULL_ROUNDS` | 4 | 最近 4 轮完整保留，不压缩 |
| `MAX_MESSAGES` | 24 | 消息数硬限制 |
| `MAX_CHARS` | 40000 | 字符数硬限制 |
| `max_items_after_crush` | 10 | 压缩后最多保留条数 |
| `first_fraction` | 0.3 | 开头保留比例 |
| `last_fraction` | 0.15 | 结尾保留比例 |
| `variance_threshold` | 2.0 | 异常值标准差阈值 |

System prompt 100% 保留。超出 4 轮的历史走 SmartCrusher 5 维评分压缩，
24 条 / 40K 字符做兜底。日志走 stderr，前缀 `[headroom-proxy]`。

## mem0 注入参数

定义在 `artemis_headroom_proxy.py`：

| 参数 | 值 | 含义 |
|---|---|---|
| `MEM0_SEARCH_LIMIT` | 5 | 每次搜索返回条数 |
| `MEM0_SCORE_HIGH` | 0.7 | 高相关，回复中必须体现 |
| `MEM0_SCORE_MEDIUM` | 0.5 | 中等相关，自然融入 |
| `MEM0_SCORE_LOW` | 0.3 | 低于此忽略 |

角色检测：从 system prompt 关键词匹配，再用 Qdrant `user_id` 过滤。

| SOUL.md 关键词 | user_id |
|---|---|
| 四季夏目 / natsume / 夏目 | natsume |
| 夜乃桜 / sakura / 夜乃樱 | sakura |
| Enola / enola | enola |
| Atori / atori / atri | atori |

手动查询记忆见 `skills/mem0-bridge/SKILL.md`。
