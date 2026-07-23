# llama 调试面板

## 快速启动

```powershell
cd D:\AI_Girlfriend\skills\llama_debugger
.\start_debugger.ps1 8765
```

或手动启动:
```powershell
cd D:\AI_Girlfriend\skills\llama_debugger
python server.py 8765
```

访问 `http://127.0.0.1:8765`

## 功能概览

### 参数配置
- 📦 **模型** — 加载 GGUF 模型路径
- 🎮 **GPU** — 层数、设备、分割、张量分配、FlashAttention、KV卸载
- ⚙️ **CPU/线程** — 线程数、批处理线程、优先级、轮询、NUMA
- 📏 **上下文** — 上下文大小、预测长度、批处理、SWA缓存
- 🎲 **采样** — 温度、Top-K/P、Min-P、XTC、典型采样、Mirostat、重复惩罚
- 📐 **RoPE** — 频率缩放、YaRN
- 🔬 **高级** — LoRA、控制向量、Speculative Decoding、JSON Schema、日志
- 📋 **日志** — 实时查看 llama-server 输出

### 预设配置
- **均衡(默认)** — 通用推荐设置
- **速度优先** — 高速生成, 高温度, 大批处理
- **质量优先** — 低温度, Mirostat 2.0, 严格采样
- **低显存** — GPU层20, 减少批处理
- **Mem0优化** — 适合向量记忆场景
- **长上下文** — 32K 上下文, 大批处理

### 配置管理
- 自动保存(3秒防抖)到 `data/llama_debugger_config.json`
- 导出/导入 JSON 配置文件
- 一键启动/停止/重载 llama-server

### 进程管理
- 实时状态监控
- 日志自动刷新(5秒间隔)
- 错误/警告高亮显示

## 目录结构
```
skills/llama_debugger/
├── server.py              # HTTP 后端 (API + 进程管理)
├── index.html             # Web 前端 (全部在一个文件中)
├── start_debugger.ps1     # 启动脚本
├── README.md              # 本文件
└── data/                  # 运行时数据
    ├── llama_debugger_config.json  # 保存的配置
    └── llama_debugger_logs/
        └── llama_server.log       # 实时日志
```

## API 端点
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | / | Web UI |
| GET | /api/status | 进程状态 |
| GET | /api/config | 获取当前配置 |
| POST | /api/config | 保存配置 (JSON body) |
| GET | /api/logs | 获取日志 (last 500 行) |
| POST | /api/command | 发送命令 (start/stop/restart/restart_default) |
| POST | /api/import | 导入配置 |
| GET | /static/* | 静态文件 |
