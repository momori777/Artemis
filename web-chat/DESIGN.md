# Web Chat UI — AI Girlfriend 聊天前端

## 概览

基于 Taste-Skill v2 设计系统构建的聊天对话界面，对标 SillyTavern 的视觉体验，
服务于 AI Girlfriend 项目的本地化多角色聊天场景。

## 设计方向

| 维度 | 值 |
|------|-----|
| **Design Read** | Desktop web app · private-haven · dark-tech + warm-intimate |
| **VARIANCE** | 5 (offset, left-sidebar + right-chat) |
| **MOTION** | 4 (CSS transitions + entry animations) |
| **DENSITY** | 3 (airy, art-gallery spacing) |
| **色彩** | off-black deep · singular rose accent (#d4787a) · no AI-purple |
| **字体** | Geist + Geist Mono (sans defaults, no Inter) |
| **形状** | rounded-md 14px · all-soft system |

## 文件结构

```
web-chat/
├── index.html          # 主聊天界面 (单文件 HTML/CSS/JS)
├── DESIGN.md           # 本文件 — 设计规范文档
├── styles/             # (预留) 拆分的 CSS 模块
├── scripts/            # (预留) 拆分的 JS 模块
└── assets/             # (预留) 角色头像、图标等静态资源
```

## 当前功能

- [x] 三栏布局：角色信息面板 + 对话流 + 输入区
- [x] 角色信息展示（名字、性格标签、出处）
- [x] 聊天气泡（用户 / 角色双色，时间戳）
- [x] 打字指示器动画
- [x] 自动展开 textarea
- [x] 连接 OpenClaw Gateway API (`/api/v1/chat/completions`)
- [x] 离线回退 demo 回复（API 不可用时）
- [x] 会话重置 / 清空对话
- [x] 移动端响应式（sidebar 折叠）
- [x] Toast 通知
- [x] 快捷技能按钮占位（TTS / ComfyUI / Live2D）

## 待实现

- [ ] 对接实际 OpenClaw Gateway 流式响应
- [ ] 多角色切换（夏目 ⇄ 亚托莉 ⇄ 夜乃桜）
- [ ] 对话历史持久化（localStorage / IndexedDB）
- [ ] 媒体附件预览（ComfyUI 图片、TTS 音频播放）
- [ ] Live2D 嵌入窗口
- [ ] 快捷键（Enter 发送、Ctrl+Enter 换行等）
- [ ] 消息搜索
- [ ] 深色/浅色主题切换
- [ ] 设置面板（API 地址、角色选择、UI 偏好）
- [ ] WebSocket 实时推送（替代轮询）

## API 对接

默认连接本地 OpenClaw Gateway（同域 `/api/v1/chat/completions`）。
Gateway 不可用时自动回退到本地 demo 回复。

### 请求格式

```json
{
  "model": "local-model",
  "messages": [{"role": "user", "content": "你好"}],
  "stream": false,
  "max_tokens": 1024
}
```

### 响应格式

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "回复文本"
    }
  }]
}
```

## Taste-Skill 合规检查

- [x] Emoji banned (none in UI text, icon-placeholders only)
- [x] No em-dash anywhere
- [x] No AI-purple (#d4787a rose accent only)
- [x] No Inter font (Geist selected)
- [x] No pure black (#000000) or white (#ffffff)
- [x] No generic 3-column feature cards
- [x] Color lock: single accent, single palette
- [x] Shape lock: all-soft radius system
- [x] Dark mode only (consistent, no section inversions)
- [x] Reduced motion: all animations are CSS-only, light
- [x] Hero fits viewport (chat IS the hero)
- [x] Nav single-line on desktop
- [x] No hand-rolled SVG icons
- [x] No decorative status dots (only semantic online indicator)
- [x] Responsive: mobile sidebar collapse

## 角色配置

当前硬编码为「四季夏目」。切换角色需要修改：
1. `char-name`, `char-subtitle` 文本
2. `.char-avatar-inner` emoji
3. `.info-group` 性格/特征/出处内容
4. Fallback replies 语料

后续版本将通过 JS 配置对象统一管理。
