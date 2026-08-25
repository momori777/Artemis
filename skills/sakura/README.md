# Sakura Desktop Pet（项目内置）/ Sakura Desktop Pet (Built-in)

## 中文

Sakura 桌宠 Agent 框架（完整版，含 runtime 虚拟环境）。原版文档见：

- 中文主文档：`README.md`（上游原版，中文）
- 英文文档：`docs/README.en.md`
- 安装教程：`docs/SETUP.md`
- Agent 技能：`SKILL.md`（项目内使用方式）
- Live2D 集成（草稿）：`SKILL_LIVE2D.md`

### 本目录在项目中的角色

- **Qdrant 记忆库**：`data/memory/qdrant/`（mem0-bridge 的存储后端）
- **Agent 引擎**：`app/agent/`（memory_curator 等 CCR 后台 worker）
- **运行时**：`runtime/`（独立 Python venv，勿混用系统 python）

## English

Sakura desktop-pet Agent framework (full copy, includes its runtime venv). Upstream docs:

- Chinese main doc: `README.md` (upstream original, Chinese)
- English doc: `docs/README.en.md`
- Setup guide: `docs/SETUP.md`
- In-project usage: `SKILL.md`
- Live2D integration (draft): `SKILL_LIVE2D.md`

### Role of This Directory in the Project

- **Qdrant memory store**: `data/memory/qdrant/` (storage backend for mem0-bridge)
- **Agent engine**: `app/agent/` (CCR background workers such as memory_curator)
- **Runtime**: `runtime/` (standalone Python venv — do not mix with system python)
