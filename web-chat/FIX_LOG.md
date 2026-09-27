# Web-Chat Fix Log

## 问题背景
用户报告：
1. Phosphor Icons 图标不渲染（所有 `<i class="ph ph-*">` 空白）
2. 导入的角色卡删除不掉

---

## 修复 1：Phosphor Icons CDN DNS 解析失败 ✅ 已修复

### 诊断过程
- 原 CDN：`https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/regular/style.css`
- PowerShell 测试：jsdelivr / unpkg / cloudflare / bootcdn / staticfile 全部 DNS 失败
- 根因：用户当前网络环境（东京）无法解析这些 CDN 域名
- 影响：图标字体 CSS 根本没加载 → 所有 `i.ph` 元素不显示 → 删除按钮的 `ph ph-x` 也看不见

### 最终方案：本地化 Phosphor Icons（2026-07-13）
1. `npm install @phosphor-icons/web@2.1.1` → `node_modules/@phosphor-icons/web/`
2. 复制字体文件到 `web-chat/fonts/`（Phosphor.woff2 / .woff / .ttf）
3. 复制 CSS 到 `web-chat/styles/phosphor-icons.css` 并修改 `@font-face` 引用本地路径
4. `index.html` 第 14 行改为 `<link rel="stylesheet" href="styles/phosphor-icons.css">`
5. 完全脱离 CDN，不受网络环境影响

---

## 修复 2：角色卡删除持久化

### 诊断
- `mergeAllCharacters()` 已在 `chars.js` 中添加了 `deletedIds` 过滤逻辑
- `removeCharacter()` 已在 `importer.js` 中添加了 `ai-gf-deleted-ids` localStorage 追踪
- 删除后触发 `mergeAllCharacters(null)` 重新合并，应能过滤掉已删除角色

### 已修改
- `scripts/chars.js`：`mergeAllCharacters()` 中过滤 deletedIds
- `scripts/importer.js`：`removeCharacter()` 中记录 deleted-ids

### 待验证
- 网络恢复后刷新页面确认：
  1. 删除按钮图标能显示
  2. 删除后页面刷新不再恢复

---

## 已修改文件列表
- `D:\AI_Girlfriend\web-chat\index.html` (CDN URL 切换)
- `D:\AI_Girlfriend\web-chat\scripts\chars.js` (deleted-ids 过滤)
- `D:\AI_Girlfriend\web-chat\scripts\importer.js` (删除持久化)
- `D:\AI_Girlfriend\web-chat\styles\main.css` (CSS icon 变量 - 待确认)

---

## 修复 3：Tree 模式下 ComfyUI 生图重启后消失 ✅ 已修复 (2026-07-13)

### 根因
`_pollAutoPaint()` 在 ComfyUI 生图完成后调用 `saveChatHistory()` 保存 messages，
但 `saveChatHistory()` 在 session 已迁移为 tree 格式时不写入新消息：
```js
if (s.tree) { saveStore(store); return; }  // 直接返回，新消息丢失！
```
所以 tree 模式下生成的图片只存在于内存，刷新页面后消失。

### 修复
1. `_pollAutoPaint()`: 改为 tree-aware 保存，用 `appendTreeNode()` + `saveSessionTree()`
2. `loadHistory()` tree 分支: 渲染前解析本地文件路径为 daemon proxy URL
3. `_renderTreeNode()` 分支跳转: 同上，添加 media 路径解析
4. `branchRegenerate` 完成后重渲染: 同上

---

## 下一步
1. ✅ Phosphor Icons 已本地化 — 刷新页面验证图标显示
2. ✅ Tree 模式生图持久化已修复 — 刷新页面验证
3. 确认角色卡删除持久化是否生效

---

# 2026-09-27 批量小 bug 修复轮 ✅

## 修复 4：start_webchat.py 服务器单线程阻塞 ✅
- 原：`HTTPServer`（单线程）+ HTTP/1.0，浏览器并发请求排队 → 刷新卡顿
- 改：`ThreadingTCPServer` + `request_queue_size=128` + `protocol_version='HTTP/1.1'` + `Cache-Control: no-store`

## 修复 5：index.html 10 处 broken label-for ✅
- `for` 指向不存在的 checkbox ID（如 `toggle-mem0-write` → 实际 ID `chat-mem0-write`）
- 全部改为指向真实 ID；JS 手动 toggle 的 label（studio.js `llamaToggleLabel1`）加 `e.preventDefault()` 防双重触发
- Playwright 验证：11 个 toggle 全部 PASS、无交叉污染、无 pageerror

## 修复 6：apiBase fallback 错误 + api.js 全部 fetch 硬编码 ✅
- ui.js fallback `http://localhost:18789`（不存在）→ `http://localhost:19260`
- api.js 7 处 fetch 硬编码 `localhost:19260` → 统一改用 `this.base`，使 settings.apiBase / `ApiClient.init()` 真正生效

## 修复 7：删除 ui.js 死代码 ✅
- 引用了 HTML 不存在的 ID（`toggle-chat-llama-label` / `chat-manage-llama` / `toggle-chat-llama-switch`）的整段全局 llama toggle；注释已声明该功能废弃，直接移除

## 修复 8：Plugins 弹窗完全不可见（定位 bug）✅
- `.plugins-popup` 的 CSS `bottom:100%` 以 `#main`（position:relative）为 containing block，而不是输入区 → 弹窗渲染到 y=-307（屏幕外），永远打不开
- ui.js 打开时动态计算按钮位置，把 popup 锚定在按钮上方（右对齐防溢出）
- Playwright hit-test 验证：popup 渲染在按钮上方且 `hitInsidePopup: true`

## 修复 9：11 个未定义的 CSS 变量（隐形元素 bug）✅
- `--surface-elevated / --border / --text / --surface(-primary/-secondary/-tertiary) / --surface-hover / --font-ui / --success-soft / --danger` 被 20+ 条规则引用但从未定义 → plugins 弹窗背景/边框透明、多个控件颜色失效
- main.css `:root` 添加 legacy 别名（`var()` 引用现有主题变量，自动跟随明/暗切换）
- 验证：re-analyze undefined = 0；计算样式确认 popup bg/border/font 正常渲染

## 修复 10：api.js nonStreamChat 丢失 sampler 参数 ✅
- 非流式聊天路径完全不传 sampler_panel 的 temperature/top_p/top_k/min_p/ penalties/max_tokens（只有流式路径有）
- 与流式路径对齐：`getSamplerParams()` merge + `??` fallback

## 验证（本轮全部通过）
- `node --check`：ui.js / api.js / studio.js OK
- probe_overlays：**7/7 PASS**（settings/worldbook/memory-viewer/live2d/studio/plugins/sampler，open+close 均正常；isOpen 已支持 transform 滑出式面板）
- test_toggles：**11/11 PASS** + 无交叉污染 + 无 pageerror
- probe_corrupt_ls / ls2：所有 localStorage key（store/settings/language/sampler×2/imported-chars/deleted-ids/worldbook-entries）灌入坏数据后重载 → **0 failures**，无 crash、无 undefined i18n 文本
- tree.js 静态审查：迁移/链遍历/分支逻辑均有 null guard，无 bug
- 消息渲染安全：`formatMsgText()` 先 escapeHtml 再 markdown，用户/LLM 内容无法注入 HTML
- index.html 无重复 ID

## 缓存版本号
- ui.js v=58→59、api.js v=27→28、main.css v=46→47（studio.js v=28 本轮早前已升）

## 已知非 bug / 遗留说明
- `probe_corrupt_ls` 输出的乱码是 PowerShell GBK 控制台显示问题，页面本身 UTF-8 正常
- ERR_CONNECTION_REFUSED console 噪音 = daemon(19260)/bridge(19250) 未启动时的 fetch，属预期行为（均有 catch）
- 分析器报的 10 个 "light 主题变量未在 base 定义" 为误报：`--icon-color/--radius-*/--ease-*` 等在 main.css `:root` 已定义
