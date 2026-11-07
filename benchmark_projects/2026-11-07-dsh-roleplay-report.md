# DeepSeek Harness（dsh / 「大肥鱼」）角色扮演生态巡查 · 2026-11-07

> 「大肥鱼」是 DeepSeek 的社区昵称；其开源 agent harness 简称 **dsh**，
> 现已作为本项目第三个 agent 运行时（与 OpenClaw、Claude Code 并列），
> 入口：`setup-dsh.ps1` / `setup-dsh.sh`，启动 `dsh web`。

## 核心仓库

| 仓库 | 说明 |
|-|-|
| [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) | 核心 harness，*27.5 万星，everything-is-a-plugin（基于 Cordis）。npm 包 `@deepseek-ai/dsh`（已全局安装，0.2.2-rc.1），需 Node ≥24。本地克隆：`benchmark_projects/deepseek-harness/` |

## 已克隆的角色演绎插件（benchmark_projects/，git-ignored）

| 目录 | 上游 | 星 | 要点 |
|-|-|-|-|
| `dsh-liketavern/` | [Amakurai/dsh-liketavern](https://github.com/Amakurai/dsh-liketavern) | 231 | SillyTavern 角色卡/预设/世界书/正则/EJS 接入 dsh 原生管线；分支级剧情状态隔离（WAL + 回滚），重试/分支不「串味」 |
| `dsh-nexttavern/` | [a86582751/dsh-nexttavern](https://github.com/a86582751/dsh-nexttavern) | 225 | 长篇 RP agent：ST 卡导入、行动选项卡、分支对话、关键词+语义混合检索长记忆；0.2.9-rc.4，npm 包 `dsh-nexttavern` 一键装；0.3 线在做 MVU/EJS/RUBY 社区卡兼容 |
| `dsh-agent-rp/` | [hewzhew/dsh-agent-rp](https://github.com/hewzhew/dsh-agent-rp) | 217 | 角色即顶层 Agent 的 RP 运行时；「故事工程」多 Worker（研究/人物/导演/编辑）；需 Node 22.19+/24 + pnpm 11 |
| `dsh-familiar-memory/` | [Elio896/dsh-familiar-memory](https://github.com/Elio896/dsh-familiar-memory) | 101 | 本地 SQLite 记忆抽屉：字面命中 + 情绪桶 + 同日上下文 + 指数衰减；实测图记忆（激活扩散）纯亏损已砍——与本项目 mem0/Qdrant 向量路线互为对照 |
| `ProjectKaren/` | [2huy4n/ProjectKaren](https://github.com/2huy4n/ProjectKaren) | 32 | 角色时钟插件：睡觉/唤醒/主动搭话/自由动作/出游照片/天气节日生日 |
| `dafeiyu-character-cards/` | [kibsmdadah-lgtm/dafeiyu-character-cards](https://github.com/kibsmdadah-lgtm/dafeiyu-character-cards) | 7 | 12 张中文角色卡 + 72 组对话示例 + 1115 个音色目录（194 个带官方试听，豆包/MiniMax/CosyVoice），TTS 选型参考 |

## 未克隆的备选

- [zxr121/MyDearFish](https://github.com/zxr121/MyDearFish)（*75）— dsh 定制源码 + 六插件打包体验
- [Kaalia0912/dsh-whale-musume-persona](https://github.com/Kaalia0912/dsh-whale-musume-persona)（*73）— 全局鲸鱼娘人设注入
- [Ebony-Vinyl/dsh-our-free-model](https://github.com/Ebony-Vinyl/dsh-our-free-model)（*6.4 万）— dsh 内免 Key 免费用前沿模型（云端，非本地路线）
- [luckui/dsh-livestream](https://github.com/luckui/dsh-livestream)（*58）— B 站直播间当主播插件
- 轻量酒馆类：chinosk6/dsh-roleplay、chen731215-dev/dsh-tavern-v2、XCNXNXNX/dsh-portable-tavern、oliblue-evan/dsh-roleplay-preset

## 结论

- 完整长篇 RP 体验：装 **dsh-nexttavern**（npm）或 **dsh-liketavern**（分支隔离最扎实）。
- 记忆实验：dsh-familiar-memory 的「指数衰减 + 零命中返回空」结论值得 mem0 桥接侧参考（RAG 不是万能，图记忆实测负收益）。
- 「角色活着」的氛围感：ProjectKaren。
- dsh 与本项目共享推理后端：指到 llama.cpp :9931 / Strata :8080 的 OpenAI 兼容端点即可，不另拉模型。
