# AI Girlfriend 项目优化日志

**日期**: 2026-07-29  
**优化范围**: 中高优先级问题修复

---

## ✅ 已完成的优化

### 🔴 高优先级修复

#### 1. **配置硬编码问题**
**问题**: `http://127.0.0.1:8080` 在多处硬编码，导致端口修改需要改多个文件  
**修复**:
- 添加全局常量 `LLAMA_BASE_URL = f"http://127.0.0.1:{LLAMA_PORT}/v1"`
- 替换所有硬编码为 `LLAMA_BASE_URL`
- 影响位置：
  - `_handle_chat_proxy()` - 主聊天路由
  - `_handle_debug_llama()` - 调试端点
  - `_handle_gen_prompt()` - 图片提示词生成

**影响**: 现在只需修改 `config.yaml` 的 `llama_port` 即可，无需修改代码

---

#### 2. **API 超时和重试机制**
**问题**: 
- 固定 120s 超时，无法配置
- 网络错误时立即失败，没有重试

**修复**:
- 添加配置项到 `config.yaml`:
  ```yaml
  api_timeout: 180          # 默认 180s
  api_max_retries: 2        # 默认重试 2 次
  ```
- 实现指数退避重试：
  - HTTP 5xx 错误：延迟 1s、2s、3s 后重试
  - 网络错误：延迟 2s、4s、6s 后重试
  - HTTP 4xx 错误：不重试（客户端错误）

**影响**: 提高了云端模型调用的稳定性，减少偶发网络抖动导致的失败

---

#### 3. **错误处理和日志增强**
**问题**: 
- 502 错误只返回 `str(e)`，不包含上下文
- 无法区分本地/云端错误

**修复**:
- 错误响应现在包含：
  - 错误类型（`HTTPError`, `URLError`, `timeout`）
  - 模型 ID (`model`)
  - 请求端点 (`endpoint`)
  - 完整错误详情（前 200 字符）
- 添加路由日志：
  ```
  [chat] routing to local llama: http://127.0.0.1:8080/v1
  [chat] routing to cloud provider: https://api.deepseek.com model=deepseek-v4
  ```

**影响**: 调试时能快速定位是本地 llama 还是云端 API 的问题

---

### 🟡 中优先级修复

#### 4. **并发控制**
**问题**: 多个请求同时调用 llama-server 可能导致 OOM 或响应变慢

**修复**:
- 添加信号量（Semaphore）限制本地 llama 并发数
- 配置项：
  ```yaml
  llama_max_concurrent: 3   # 默认最多 3 个并发
  ```
- 超过限制时返回 503：
  ```json
  {"error": "Server busy, too many concurrent requests. Please retry."}
  ```
- 云端模型不受此限制（各家 API 有自己的限流）

**影响**: 防止本地 llama 过载，提高响应稳定性

---

#### 5. **流式响应异常处理**
**问题**: 流式传输中途出错时，客户端可能卡住或收到不完整数据

**修复**:
- 添加 `try-finally` 确保 `resp.close()` 被调用
- 流中出现异常时发送错误事件：
  ```
  data: {"error":"<error message>"}
  ```
- 客户端能正确捕获并显示错误

**影响**: 避免客户端无限等待，提升用户体验

---

## 📋 配置文件变更

### `config.yaml` 新增配置（可选）

```yaml
# API 超时和并发控制（可选）
api_timeout: 180          # API 请求超时秒数（默认 180）
api_max_retries: 2        # 失败重试次数（默认 2）
llama_max_concurrent: 3   # 本地 llama 最大并发请求数（默认 3）
```

**注意**: 这些配置都有合理的默认值，不添加也能正常运行

---

## 🔍 代码变更统计

| 文件 | 修改类型 | 行数变化 |
|------|---------|---------|
| `shiki_daemon.py` | 重构 + 增强 | +80 / -40 |
| `config.yaml` | 新增配置 | +7 |

---

## ✅ 测试建议

### 1. 本地模型测试
```bash
# 修改端口后验证
# 1. 修改 config.yaml: llama_port: 8081
# 2. 重启 shiki_daemon.py
# 3. 前端发送消息，检查是否正确路由到 8081
```

### 2. 云端模型测试
```bash
# 1. 前端选择 deepseek/deepseek-v4
# 2. 发送消息
# 3. 检查控制台日志：应该显示 "routing to cloud provider"
# 4. 检查返回内容是否来自 DeepSeek（不是本地模型）
```

### 3. 并发测试
```bash
# 1. 设置 llama_max_concurrent: 2
# 2. 同时打开 3 个浏览器标签页
# 3. 同时发送消息
# 4. 第 3 个请求应该收到 503 错误："Server busy"
```

### 4. 重试测试
```bash
# 1. 暂时关闭 llama-server
# 2. 前端发送消息
# 3. 应该看到 3 次重试日志（1 次初始 + 2 次重试）
# 4. 最终返回网络错误
```

---

## 🚀 性能影响

- **延迟**: 正常情况下无影响；网络错误时增加重试延迟（最多 12s）
- **内存**: 信号量占用可忽略（< 1KB）
- **并发**: 本地 llama 并发限制可能让部分请求排队，但避免了 OOM

---

## 📝 未来优化建议（低优先级）

1. **类型安全**: 添加请求/响应的 TypeScript 类型定义
2. **请求缓存**: 相同问题短时间内返回缓存结果
3. **可观测性**: 添加 Prometheus metrics（请求数、延迟分布、错误率）
4. **代码重构**: 将 `_handle_chat_proxy` 拆分为更小的函数
5. **测试覆盖**: 添加单元测试和集成测试

---

## 🔗 相关文件

- 主要修改: `shiki_daemon.py`
- 配置文件: `config.yaml`
- 前端 API: `web-chat/scripts/api.js`（无修改，兼容现有逻辑）

---

**修复完成时间**: 2026-07-29 21:50  
**测试状态**: ⏳ 待用户验证
