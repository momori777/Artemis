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

## 修复 11：startup 脚本启动后 “fail to fetch” ✅ (2026-09-29)

### 根因
`shiki-start.cmd` → `shiki_daemon.py` 在模块顶层 `import pystray`（第 2389 行）抛 `ModuleNotFoundError` → **daemon 在 dashboard(19260)/webchat(19270) 服务器启动之前就崩溃退出** → 前端所有 fetch 全部 connection refused。
（`__main__` 里的 ImportError 保护是死代码：顶层 import 先执行，永远到不了保护分支。）

### 修复
1. `pip install pystray pillow`（补齐依赖）
2. `shiki_daemon.py` 加固：
   - pystray/PIL 改为 guarded import（`except ImportError: pystray = None`）
   - `main()`：pystray 缺失时进入 headless 保活循环，服务器照常跑；`icon.run()` 抛异常（如远程/无桌面会话）也不退出，继续 headless
   - `__main__` 检查改为仅提示，不再 `sys.exit(1)`

### 验证
- daemon 后台运行：19260 + 19270 均在 Listen，`/api/status`、`/api/gateway-config`、`/` 全部 200
- 页面加载全部脚本/字体 200

## 已知非 bug / 遗留说明
- `probe_corrupt_ls` 输出的乱码是 PowerShell GBK 控制台显示问题，页面本身 UTF-8 正常
- ERR_CONNECTION_REFUSED console 噪音 = daemon(19260)/bridge(19250) 未启动时的 fetch，属预期行为（均有 catch）
- 分析器报的 10 个 "light 主题变量未在 base 定义" 为误报：`--icon-color/--radius-*/--ease-*` 等在 main.css `:root` 已定义

---

# 2026-11-20 批量小 bug 修复轮 ✅

## 修复 12：顶栏显示裸 i18n key `user_profile`
- `index.html` 的「我的档案」按钮用 `data-i18n="user_profile"`，但 `i18n.js` 里没有这个 key
- 结果：顶栏和 tooltip 都直接渲染出 `user_profile`（截图可见）
- 补 `user_profile: { zh: '我的档案', ja: 'マイプロフィール', en: 'My Profile' }`

## 修复 13：`i18n.js` 21 个 `sampler_help_*` key 重复定义
- 两段 sampler 帮助文案（旧短版 / 新长版）同时存在，同一对象字面量里后写覆盖前写，前一段是死代码
- 后果：维护时改错段落 → 改动毫无效果
- 去重：保留新长版，旧段里独有的 8 个参数说明（temp/top_p/top_k/min_p/rep_pen/freq_pen/pres_pen/max_tk）保留并放到参数说明段
- 校验：i18n key 230 → 209，重复 21 → 0，无 key 丢失

## 修复 14：侧边栏头像图片与首字母同时渲染
- `_renderCharAvatar()` 用页面级 `getElementById('char-avatar-icon')` 找图标，但 `CHAR_API_PROMISE` 回来后 `loadCharUI()` 会再跑一遍
- 第二次调用走了 else 分支：找不到已删除的图标 → 新建 `<span>` 追加，于是 `<img>` 和首字母同时存在，56px 头像被两个子元素挤开（图片左偏被裁、首字母跑到名字上，就是截图里那个悬空的 "r"）
- 修复：查找范围收敛到 `avatarEl.querySelector(...)`；两个分支各自清理另一分支的残留节点；非字符串的 avatar 值（localStorage 坏数据 `[]`）不再当 `img.src`

## 修复 15：`mergeAllCharacters()` 二次合并丢掉角色立绘
- `CHARACTERS_JSON` 带 SVG 头像，但 API 只返回 id/name/icon，`CHAR_FALLBACKS` 没有 avatar 字段
- 每次 re-merge（API 成功或失败都会触发）都会重建列表，头像被覆盖成 `null` → 立绘消失只剩首字母
- 修复：合并前快照 `prevById`，API 条目用 `c.avatar || prevById[id].avatar`，兜底条目 `Object.assign({}, prevById[id] || {}, fb, …)`

## 修复 16：世界书条目列表没有样式
- `worldbook.js` 渲染 `.wb-entry / -header / -key / -content / -actions / -meta`，但 CSS 里写的是旧结构的 `.wb-item*`
- 后果：条目列表是无卡片、无间距、按钮和 meta 挤在一起的裸文本
- 修复：CSS 里把 `.wb-item*` 换成与渲染结构一致的 `.wb-entry*`（卡片/悬停/标题行/内容/操作行/meta 右对齐），保留仍在用的 `.wb-action-btn`，补 `.wb-toggle-on`
- 顺带删掉 `worldbook.js` 里赋值后从未使用的 `iconClass`

## 修复 17：世界书工具栏 / 记忆查看按钮是系统原生白块
- `index.html` 用了 `.btn-sm`（New Entry / Enable All / Disable All），CSS 里没有该规则
- `.memory-view-btn`、`.memory-viz-toggle`（插件面板「查看记忆」、记忆查看器「可视化」）同样没有规则
- 暗色主题里这三个按钮渲染成白色原生按钮
- 修复：补 `.btn-sm`、`.memory-view-btn`、`.memory-viz-toggle(.active)` 样式，全部走主题变量

## 修复 18：`escapeHtml` 双份定义，转义规则随脚本加载顺序变
- `ui.js`（DOM 版，不转义引号）与 `worldbook.js`（正则版，转义引号）各定义一份全局函数，后者覆盖前者
- 风险：`ui.js` 把 `escapeHtml()` 用在 `data-char="…"` / `data-name="…"` 属性里，一旦加载顺序变化（或 worldbook.js 加载失败）引号就漏转义
- 修复：只保留 `ui.js` 一份并补 `"` / `'` 转义；`worldbook.js` 改为「不存在时才兜底定义」

## 修复 19：daemon `get_status()` 可能少返回服务
- 并行探测 + `join(timeout=2)`，超时的线程对应项仍是 `None`，最后被 `if entry is not None` 过滤掉
- 后果：`/api/status` 静默少一行，前端服务列表缺项
- 修复：先按 SERVICES 建全量结果（online 默认 False），线程只回填 online，始终返回等长列表

## 修复 20：`mem0_behavior_integration.py` 写死旧机器路径
- `C:\Users\TK\.openclaw\workspace`、`D:\AI_Girlfriend` 在本机都不存在（仓库在 `E:\AI_Girlfriend`）
- 修复：仓库根由 `Path(__file__).resolve().parents[2]` 推导，workspace 走 `OPENCLAW_WORKSPACE` 环境变量 / `%USERPROFILE%`，并支持 `GIRLFRIEND_ROOT` 覆盖（与 `skills/shared/mem0_bridge.py` 一致）

## 验证（本轮）
- `node --check`：ui.js / i18n.js / worldbook.js / chars.js 及全部 scripts/*.js 通过
- `python -m py_compile`：shiki_daemon.py、mem0_behavior_integration.py 通过
- daemon 冒烟：`_make_loopback_servers` 同时绑定 127.0.0.1 + ::1，两个族均可连接；`get_status()` 11/11 行
- 静态审计：i18n 重复 key 0、data-i18n 缺失 0、HTML 重复 id 0、label-for 断链 0、未定义 CSS 变量 0
- 浏览器实测（Edge + Playwright，1440×900，静态托管 web-chat）：
  - 顶栏显示「我的档案」，页面可见文本中不再出现 snake_case 的裸 key
  - 侧边栏头像只剩 1 个子节点（`img`），立绘正常居中，无悬空首字母
  - 世界书条目渲染为卡片（padding 10/12、圆角、hover 边框），工具栏按钮为暗色样式
  - 记忆查看器「可视化」为暗色按钮；设置/档案/世界书/记忆/Live2D 弹层均无 pageerror

## 缓存版本号
- main.css v=49→50、ui.js v=63→64、i18n.js v=7→8、worldbook.js v=1→2、chars.js v=27→28

