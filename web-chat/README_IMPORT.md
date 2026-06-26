# Artemis 角色数据导入指南

## 现状

6 个角色数据目前存在两个地方：
1. **`skills/harem/<角色>/`** — 后端角色卡（SOUL.md / IDENTITY.md）
2. **浏览器 `localStorage`** — 导入的角色定义、聊天历史、自定义头像

前端 `chars.js` 依赖 daemon API（19260）或 fallback 硬编码数据。

## 目标

将 localStorage 中的数据（特别是导入的角色定义和头像）整合到项目中。

## 方法 A：手动导出导入（推荐，精确控制）

### 步骤 1：导出 localStorage

1. 打开 Artemis 前端页面（http://localhost:19270）
2. 打开 DevTools（F12）
3. Console 中执行：
   ```js
   copy(localStorage.getItem('ai-gf-imported-chars'))
   ```
4. 这会复制到剪贴板

### 步骤 2：使用导出工具

打开 `http://localhost:19270/import-local.html`
- 粘贴剪贴板内容
- 点击"导出为 JSON 文件"
- 生成的 `CHARACTERS_JSON.js` 放在项目根目录

### 步骤 3：集成到前端

修改 `chars.js`，添加一个加载函数：

```javascript
// 加载 CHARACTERS_JSON.js（如果有）
(function() {
  // 检查 CHARACTERS_JSON 是否已定义
  if (typeof CHARACTERS_JSON !== 'undefined') {
    mergeAllCharacters(CHARACTERS_JSON);
  } else {
    // fallback 逻辑不变
    mergeAllCharacters(null);
  }
})();
```

并在 `index.html` 中加载：
```html
<script src="CHARACTERS_JSON.js"></script>
<script src="scripts/chars.js?v=XX"></script>
```

## 方法 B：自动同步（daemon API 扫描 harem 目录）

当前 daemon 已经扫描 `skills/harem/` 目录并返回角色信息。
前端 merge 逻辑已包含 fallback + API 数据。

问题：localStorage 中的导入角色（`ai-gf-imported-chars`）只在浏览器端存在，
daemon 不知道它们。

解决方案：
1. daemon 在 `list_characters` 时也读取 `localStorage.ai-gf-imported-chars`
2. 或者前端在 `mergeAllCharacters` 中优先使用 `localStorage` 数据

当前实现已经是方法 2（`mergeAllCharacters` 优先读 localStorage）。

## 自定义头像处理

头像存储在 `localStorage.ai-girlfriend-store-v2.avatars` 中（base64）。
如果要将头像放到项目中：
1. 导出 base64 数据
2. 解码保存为文件（`skills/harem/<角色>/avatar.jpg`）
3. 前端改为从文件加载（URL proxy）而非 base64

## 聊天历史处理

聊天历史存储在 `localStorage.ai-girlfriend-store-v2.chats` 中。
可以导出为 JSON 文件，作为 seed data 供测试/演示使用。
