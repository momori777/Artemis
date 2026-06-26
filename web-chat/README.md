# Artemis 前端角色系统

## 角色数据加载流程

```
1. CHARACTERS_JSON.js  (硬编码文件，包含6个完整角色)
      ↓
2. chars.js (mergeAllCharacters)
      ↓
3. localStorage.ai-gf-imported-chars (浏览器导入的角色)
      ↓
4. daemon API (19260) (harem 目录扫描)
```

### 优先级
1. `CHARACTERS_JSON.js` — **最高优先级**，项目内置的6个角色
2. `localStorage` — 用户从浏览器导入的角色（覆盖内置数据）
3. `daemon API` — 后端扫描 `skills/harem/` 目录（补充新角色）

## 文件结构

```
web-chat/
├── CHARACTERS_JSON.js       # 6个角色的完整定义
├── scripts/
│   ├── chars.js             # 角色加载、合并、管理逻辑
│   ├── store.js             # localStorage 持久化
│   └── ui.js                # UI 渲染（头像、聊天、裁剪）
├── import-local.html        # 从浏览器导入 localStorage 数据
├── export-localStorage.html # 导出 localStorage 数据
└── README.md                # 本文件
```

## 6个角色

| ID | 名称 | 来源 | 颜色 |
|----|------|------|------|
| natsume | 四季夏目 | 星光咖啡蝶与死神之馆 | #d4787a |
| sakura | 夜乃桜 | Dimension Lovers!! | #7e9ec8 |
| enola | Enola | 原创角色 | #c4a882 |
| atori | 亚托莉 | ATRI -My Dear Moments- | #6eb5c0 |
| ruruka | 森亚露露卡 | 光之美少女/DZMM | #7b4f9e |

每个角色包含：
- 基础信息（id, name, icon, accent）
- 人设描述（persona, personaNote, tags, source）
- TTS 配置（lang, mood）
- 默认回复库（fallbackReplies）

## 更新角色数据

### 方法 1：直接编辑 CHARACTERS_JSON.js
```javascript
// 在 D:\AI_Girlfriend\web-chat\CHARACTERS_JSON.js 中
// 添加/修改角色对象
```

### 方法 2：从浏览器导入
1. 打开 `http://localhost:19270/import-local.html`
2. 粘贴 `localStorage.getItem('ai-gf-imported-chars')` 输出
3. 点击"导出为 JSON 文件"
4. 替换 `CHARACTERS_JSON.js` 内容

### 方法 3：Daemon 自动扫描
- 确保 `skills/harem/<角色>/` 目录存在
- Daemon 会自动扫描并返回新角色
- 前端会合并这些新角色

## 自定义头像存储

- 用户上传的头像存储在 `localStorage.ai-girlfriend-store-v2.avatars`
- 以 base64 格式保存，压缩到 256x256px
- 头像在以下位置显示：
  - 侧边栏头像
  - 角色切换下拉框
  - 聊天消息气泡

## 聊天历史

- 存储键：`localStorage.ai-girlfriend-store-v2.chats`
- 结构：`{ [charId]: { [sessionId]: { messages[], name } } }`
- 每个角色独立存储聊天记录
- 最多保留 500 条消息/会话
