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

## 下一步
1. ✅ Phosphor Icons 已本地化 — 刷新页面验证图标显示
2. 确认角色卡删除持久化是否生效
