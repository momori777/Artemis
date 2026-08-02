/**
 * i18n.js — Internationalization for AI Girlfriend web-chat
 * 
 * Provides:
 *   window.i18n — get translation by key
 *   window.setLang(lang) — switch language (zh/ja/en) and update all UI
 *   window.tr(key) — shorthand for i18n(key)
 * 
 * Usage: <script src="scripts/i18n.js?v=1"></script> before all other scripts
 */

(function () {
  'use strict';

  // ── Translation tables ──
  var T = {
    // Sidebar
    app_title:               { zh: 'AI 女友',              ja: 'AI 彼女',              en: 'AI Girlfriend' },
    chats:                   { zh: '聊天',                 ja: 'チャット',             en: 'Chats' },
    new_chat:                { zh: '新建',                 ja: '新規',                 en: 'New' },
    persona:                 { zh: '人设',                 ja: '性格',                 en: 'Persona' },
    traits:                  { zh: '属性',                 ja: '特性',                 en: 'Traits' },
    source:                  { zh: '来源',                 ja: '出典',                 en: 'Source' },
    open_studio:             { zh: '打开 Studio',          ja: 'Studio を開く',        en: 'Open Studio' },
    live2d_action:           { zh: 'Live2D 动作',          ja: 'Live2D アクション',    en: 'Live2D Action' },
    checking:                { zh: '检查中...',            ja: '確認中...',            en: 'Checking...' },
    import_char:             { zh: '导入角色卡 (.png/.json/.txt)', ja: 'キャラカード取込', en: 'Import character card' },
    import_worldbook:        { zh: '导入世界书 (.md/.txt/.json)',  ja: '世界観取込',        en: 'Import world book' },

    // Main tabs
    tab_chat:                { zh: '聊天',                 ja: 'チャット',             en: 'Chat' },
    tab_studio:              { zh: 'Studio',               ja: 'Studio',               en: 'Studio' },

    // Chat header
    search:                  { zh: '搜索',                 ja: '検索',                 en: 'Search' },
    settings:                { zh: '设置',                 ja: '設定',                 en: 'Settings' },
    reset_session:           { zh: '重置会话',             ja: 'セッションリセット',     en: 'Reset session' },
    clear_messages:          { zh: '清空消息',             ja: 'メッセージ消去',         en: 'Clear messages' },
    search_placeholder:      { zh: '搜索消息...',          ja: 'メッセージ検索...',      en: 'Search messages...' },
    type_message:            { zh: '输入消息...',          ja: 'メッセージ入力...',      en: 'Type a message...' },
    send:                    { zh: '发送',                 ja: '送信',                 en: 'Send' },

    // Input action buttons
    btn_auto_paint:          { zh: 'AI自动生成画图提示词', ja: 'AIが絵の指示を生成',     en: 'AI auto-generate image prompt' },
    btn_manual_paint:        { zh: '手动输入提示词画图',    ja: '手動で絵の指示を入力',    en: 'Manual prompt image gen' },
    btn_tts_voice:           { zh: '语音朗读最近回复',      ja: '最新の返信を音声読上',    en: 'TTS read last reply' },
    btn_tts_streaming:       { zh: '流式TTS+Live2D口型同步', ja: 'ストリームTTS+口形同期', en: 'Stream TTS + Lip Sync' },
    btn_stop_llama:          { zh: '停llama释放显存',       ja: 'llama停止でVRAM解放',    en: 'Stop llama to free VRAM' },
    btn_plugins:             { zh: '增强功能 (Mem0等)',     ja: '拡張機能 (Mem0等)',      en: 'Plugins (Mem0 etc.)' },
    stop_llama_label:        { zh: '停llama',              ja: 'llama停止',            en: 'Stop llama' },

    // Thinking mode
    thinking_default:        { zh: '默认',                 ja: 'デフォルト',           en: 'Default' },
    thinking_immersive:      { zh: '沉浸',                 ja: '没入',                 en: 'Immersive' },
    thinking_analytic:       { zh: '分析',                 ja: '分析',                 en: 'Analytic' },
    thinking_godview:        { zh: '上帝',                 ja: '俯瞰',                 en: 'God View' },

    // Plugins popup
    plugin_model:            { zh: '💬 模型',              ja: '💬 モデル',            en: '💬 Model' },
    plugin_reasoning:        { zh: 'Reasoning · 深度思考',  ja: 'Reasoning · 深層思考',  en: 'Reasoning · Deep Think' },
    plugin_rea_hint:         { zh: '⚠ 开关会重启llama，需等待~30秒', ja: '⚠ llama再起動、約30秒待機', en: '⚠ Toggle restarts llama, ~30s wait' },
    plugin_think_style:      { zh: '思考风格',             ja: '思考スタイル',          en: 'Thinking Style' },
    plugin_memory:           { zh: '🧠 记忆',              ja: '🧠 記憶',              en: '🧠 Memory' },
    plugin_mem_source:       { zh: '记忆源',               ja: '記憶ソース',           en: 'Memory Source' },
    plugin_mem_view:         { zh: '查看记忆',             ja: '記憶を表示',           en: 'View Memory' },
    plugin_mem_search:       { zh: '每轮搜索记忆',          ja: '毎ターン記憶検索',      en: 'Search memory each turn' },
    plugin_mem_write:        { zh: '自动写入记忆',          ja: '自動で記憶を書込',      en: 'Auto-write memory' },
    plugin_mem_interval:     { zh: '写入间隔',             ja: '書込間隔',             en: 'Write Interval' },
    plugin_mem_round:        { zh: '轮',                   ja: 'ターン',               en: 'rounds' },

    // Settings
    settings_title:          { zh: '设置',                 ja: '設定',                 en: 'Settings' },
    settings_subtitle:       { zh: '配置 API 端点和偏好',   ja: 'APIエンドポイントと設定', en: 'Configure API and preferences' },
    settings_api_base:       { zh: 'Chat API Base URL',    ja: 'Chat API Base URL',    en: 'Chat API Base URL' },
    settings_bridge_url:     { zh: 'Artemis Bridge URL',    ja: 'Artemis Bridge URL',   en: 'Artemis Bridge URL' },
    settings_model:          { zh: '模型',                 ja: 'モデル',               en: 'Model' },
    settings_stream:         { zh: '流式响应',             ja: 'ストリーム応答',        en: 'Stream responses' },
    settings_mem0:           { zh: 'Mem0 记忆增强 (每轮搜索长期记忆)', ja: 'Mem0 記憶強化 (毎ターン長期記憶検索)', en: 'Mem0 Memory Boost (search per turn)' },
    settings_mem0_write:     { zh: 'Mem0 自动写入',        ja: 'Mem0 自動書込',        en: 'Mem0 Auto Write' },
    settings_mem0_interval:  { zh: '写入间隔 (每N轮对话)',  ja: '書込間隔 (Nターン毎)',  en: 'Write Interval (every N turns)' },
    settings_tree:           { zh: '对话树模式 (Conversation Tree)', ja: '会話ツリー',     en: 'Conversation Tree' },
    settings_tree_hint:      { zh: '开启后重新回复会创建分支，保留历史版本', ja: '再返信で分岐を作成し履歴を保存', en: 'Replies create branches, preserving history' },
    settings_tree_auto:      { zh: '自动 (Auto)',          ja: '自動',                 en: 'Auto' },
    settings_tree_on:        { zh: '开启 (On)',            ja: 'ON',                   en: 'On' },
    settings_tree_off:       { zh: '关闭 (Off)',           ja: 'OFF',                  en: 'Off' },
    settings_cancel:         { zh: '取消',                 ja: 'キャンセル',           en: 'Cancel' },
    settings_save:           { zh: '保存',                 ja: '保存',                 en: 'Save' },

    // Studio
    studio_bridge:           { zh: 'Bridge: 检查中...',    ja: 'Bridge: 確認中...',     en: 'Bridge: checking...' },
    studio_refresh:          { zh: '刷新',                 ja: '更新',                 en: 'Refresh' },
    studio_tts_tab:          { zh: 'TTS 语音',             ja: 'TTS 音声',             en: 'TTS Voice' },
    studio_comfyui_tab:      { zh: 'ComfyUI 画图',         ja: 'ComfyUI 画像',         en: 'ComfyUI Image' },
    studio_dashboard_tab:    { zh: '仪表盘',               ja: 'ダッシュボード',        en: 'Dashboard' },
    studio_debug_tab:        { zh: '模型调试',             ja: 'モデルデバッグ',        en: 'Model Debug' },
    studio_tts_text:         { zh: '文本',                 ja: 'テキスト',             en: 'Text' },
    studio_tts_placeholder:  { zh: '输入要合成的文字...',   ja: '合成する文字を入力...',  en: 'Enter text to synthesize...' },
    studio_lang:             { zh: '语言',                 ja: '言語',                 en: 'Language' },
    studio_mood:             { zh: '情绪',                 ja: '雰囲気',               en: 'Mood' },
    studio_char:             { zh: '角色',                 ja: 'キャラ',               en: 'Character' },
    studio_synthesize:       { zh: '合成',                 ja: '合成',                 en: 'Synthesize' },
    studio_audio_placeholder:{ zh: '音频预览',             ja: '音声プレビュー',        en: 'Audio preview' },
    studio_comfy_pos:        { zh: '正向提示词',           ja: 'ポジティブプロンプト',   en: 'Positive Prompt' },
    studio_comfy_neg:        { zh: '负向提示词',           ja: 'ネガティブプロンプト',   en: 'Negative Prompt' },
    studio_width:            { zh: '宽度',                 ja: '幅',                   en: 'Width' },
    studio_height:           { zh: '高度',                 ja: '高さ',                 en: 'Height' },
    studio_steps:            { zh: '步数',                 ja: 'ステップ',             en: 'Steps' },
    studio_cfg:              { zh: 'CFG',                  ja: 'CFG',                  en: 'CFG' },
    studio_checkpoint:       { zh: '模型',                 ja: 'モデル',               en: 'Checkpoint' },
    studio_presets:          { zh: '快速预设',             ja: 'クイックプリセット',    en: 'Quick Presets' },
    studio_stop_llama:       { zh: '生成前停llama (释放显存防OOM)', ja: '生成前にllama停止 (VRAM解放)', en: 'Stop llama before gen (free VRAM)' },
    studio_generate:         { zh: '生成',                 ja: '生成',                 en: 'Generate' },
    studio_image_placeholder:{ zh: '图片预览',             ja: '画像プレビュー',        en: 'Image preview' },
    studio_start_all:        { zh: '启动全部服务',          ja: '全サービス起動',        en: 'Start All Services' },
    studio_stop_all:         { zh: '停止全部',             ja: '全停止',               en: 'Stop All' },
    studio_open_webchat:     { zh: '打开聊天',             ja: 'チャットを開く',        en: 'Open Web Chat' },

    // Debug
    debug_system_prompt:     { zh: 'System Prompt',        ja: 'システムプロンプト',    en: 'System Prompt' },
    debug_user_msg:          { zh: 'User Message',         ja: 'ユーザーメッセージ',    en: 'User Message' },
    debug_model:             { zh: '模型',                 ja: 'モデル',               en: 'Model' },
    debug_temp:              { zh: 'Temperature',          ja: 'Temperature',          en: 'Temperature' },
    debug_top_p:             { zh: 'Top P',                ja: 'Top P',                en: 'Top P' },
    debug_top_k:             { zh: 'Top K',                ja: 'Top K',                en: 'Top K' },
    debug_max_tokens:        { zh: 'Max Tokens',           ja: '最大トークン',          en: 'Max Tokens' },
    debug_min_p:             { zh: 'Min P',                ja: 'Min P',                en: 'Min P' },
    debug_freq_pen:          { zh: 'Freq Penalty',         ja: '頻出ペナルティ',        en: 'Freq Penalty' },
    debug_pres_pen:          { zh: 'Pres Penalty',         ja: '存在ペナルティ',        en: 'Pres Penalty' },
    debug_repeat_pen:        { zh: 'Repeat Penalty',       ja: '繰返ペナルティ',        en: 'Repeat Penalty' },
    debug_logprobs:          { zh: 'Logprobs',             ja: 'Logprobs',             en: 'Logprobs' },
    debug_top_n:             { zh: 'Top N',                ja: 'Top N',                en: 'Top N' },
    debug_send:              { zh: '发送',                 ja: '送信',                 en: 'Send' },
    debug_clear:             { zh: '清除',                 ja: 'クリア',               en: 'Clear' },
    debug_response:          { zh: '返回',                 ja: '応答',                 en: 'Response' },
    debug_raw:               { zh: 'Raw JSON',             ja: 'Raw JSON',             en: 'Raw JSON' },
    debug_placeholder:       { zh: '发送请求查看模型返回',   ja: '送信してモデルの応答を表示', en: 'Send a request to see response' },
    debug_sending:           { zh: '发送中...',            ja: '送信中...',             en: 'Sending...' },

    // World Book
    wb_title:                { zh: '世界书',               ja: '世界観',               en: 'World Books' },
    wb_empty:                { zh: '尚未加载世界书条目',     ja: '世界観エントリ未読込',   en: 'No world book entries loaded.' },
    wb_new_entry:            { zh: '新建条目',             ja: '新規エントリ',          en: 'New Entry' },
    wb_enable_all:           { zh: '全部启用',             ja: 'すべて有効',           en: 'Enable All' },
    wb_disable_all:          { zh: '全部禁用',             ja: 'すべて無効',           en: 'Disable All' },
    wb_drop_text:            { zh: '点击或拖放文件 (.md/.txt/.json)', ja: 'ファイルをD&D (.md/.txt/.json)', en: 'Click or drag files (.md/.txt/.json)' },
    wb_drop_hint:            { zh: '支持同时上传多个文件',   ja: '複数ファイル同時アップロード可', en: 'Supports multiple files at once' },
    wb_remove_all:           { zh: '删除全部',             ja: '全て削除',             en: 'Remove All' },
    wb_close:                { zh: '关闭',                 ja: '閉じる',               en: 'Close' },

    // Avatar
    avatar_title:            { zh: '更换头像',             ja: 'アイコン変更',          en: 'Change Avatar' },
    avatar_drop_text:        { zh: '点击或拖放图片',        ja: '画像をD&D',             en: 'Click or drag image' },
    avatar_remove:           { zh: '移除头像',             ja: 'アイコン削除',          en: 'Remove Avatar' },
    avatar_cancel:           { zh: '取消',                 ja: 'キャンセル',           en: 'Cancel' },
    avatar_apply:            { zh: '应用',                 ja: '適用',                 en: 'Apply' },
    avatar_crop_hint:        { zh: '拖动选择裁剪区域，点击<strong>应用</strong>', ja: 'ドラッグで範囲選択→<strong>適用</strong>', en: 'Drag to select area, click <strong>Apply</strong>' },

    // Memory viewer
    mem_view_title:          { zh: '🧠 记忆查看',          ja: '🧠 記憶ビューア',       en: '🧠 Memory Viewer' },
    mem_view_viz:            { zh: '可视化',              ja: '可視化',                en: 'Visualize' },
    mem_view_empty:          { zh: '点击"查看记忆"按钮加载', ja: '「記憶を表示」ボタンで読込', en: 'Click "View Memory" to load' },

    // Toast / misc
    lang_changed:            { zh: '已切换为中文',          ja: '日本語に切替ました',     en: 'Switched to English' },
    theme_switch:            { zh: '切换主题',             ja: 'テーマ切替',            en: 'Switch theme' },

    // Sampler panel
    sampler_title:           { zh: 'Sampler + 上下文压缩',  ja: 'Sampler + 圧縮',       en: 'Sampler + Headroom' },
    sampler_headroom_label:  { zh: '🧠 Headroom 上下文压缩', ja: '🧠 コンテキスト圧縮',  en: '🧠 Headroom Context Compression' },
    sampler_preset_label:    { zh: 'Sampler 预设',          ja: 'Sampler プリセット',    en: 'Sampler Presets' },
    sampler_preset_rp:       { zh: '角色扮演',              ja: 'ロールプレイ',          en: 'Roleplay' },
    sampler_preset_creative: { zh: '创意',                 ja: '創造的',               en: 'Creative' },
    sampler_preset_precise:  { zh: '精确',                 ja: '精密',                 en: 'Precise' },
    sampler_preset_neutral:  { zh: '中性',                 ja: 'ニュートラル',          en: 'Neutral' },
    sampler_preset_coding:   { zh: '编程',                 ja: 'コーディング',          en: 'Coding' },
    sampler_hr_recent:       { zh: '最近保留轮数',          ja: '最近保持ターン数',       en: 'Recent Rounds' },
    sampler_hr_items:        { zh: '压缩保留条数',          ja: '圧縮後保持数',          en: 'Crushed Items' },
    sampler_hr_msgs:         { zh: '最大消息数',            ja: '最大メッセージ数',       en: 'Max Messages' },
    sampler_hr_chars:        { zh: '最大字符数',            ja: '最大文字数',            en: 'Max Chars' },
    sampler_hr_reset:        { zh: 'Reset Headroom 默认',  ja: 'Headroom 初期化',      en: 'Reset Headroom' },
    sampler_hr_recent_hint:  { zh: '最近N轮不压缩',         ja: '最近Nターンは非圧縮',    en: 'Last N rounds kept full' },
    sampler_hr_items_hint:   { zh: '旧历史压缩后条数',       ja: '旧履歴の圧縮後数',       en: 'Old history after crush' },
    sampler_hr_msgs_hint:    { zh: '超出硬截断',            ja: '超過分を強制切捨',       en: 'Hard cap: truncate above' },
    sampler_hr_chars_hint:   { zh: '超出硬截断',            ja: '超過分を強制切捨',       en: 'Hard cap: truncate above' },
    sampler_hr_reset_toast:  { zh: 'Headroom: 已恢复默认',  ja: 'Headroom: 初期化済',   en: 'Headroom: reset to defaults' },
    sampler_preset_toast:    { zh: 'Sampler 预设:',         ja: 'プリセット:',           en: 'Sampler preset: ' },
    sampler_toggle_title:    { zh: 'Sampler + Headroom 参数', ja: 'Sampler + 圧縮 設定', en: 'Sampler + Headroom Parameters' },

    // Sampler help popup — parameter descriptions
    sampler_help_title:      { zh: 'Sampler & 上下文压缩 — 参数说明', ja: 'Sampler & 圧縮 — パラメータ説明', en: 'Sampler & Headroom — Parameters' },
    sampler_help_sampler:    { zh: 'Sampler 参数（控制 LLM 输出随机性）', ja: 'Sampler パラメータ（出力ランダム性制御）', en: 'Sampler Parameters (LLM output randomness)' },
    sampler_help_temp:       { zh: '越高越随机/创造性，越低越确定/重复。0.7-0.9适合角色扮演。', ja: '高=ランダム/創造的、低=確定的。0.7-0.9はロールプレイ向け。', en: 'Higher=random/creative, lower=deterministic. 0.7-0.9 for roleplay.' },
    sampler_help_top_p:      { zh: '核采样。只从累积概率达P的候选词中选。0.9=最可能的前90%。', ja: '核サンプリング。累積確率Pまでの候補から選択。0.9=上位90%。', en: 'Nucleus sampling. Only top P probability mass. 0.9=top 90%.' },
    sampler_help_top_k:      { zh: '只从概率最高的K个token中选。40-80常见。越小越保守。', ja: '上位Kトークンから選択。40-80が一般的。小=保守的。', en: 'Sample from top K tokens. 40-80 common. Lower=conservative.' },
    sampler_help_min_p:      { zh: '剔除低于最高概率×MinP的候选。0.05-0.1常用。', ja: '最高確率×MinP未満を除外。0.05-0.1推奨。', en: 'Filter below max_prob×MinP. 0.05-0.1 recommended.' },
    sampler_help_rep_pen:    { zh: '惩罚已出现过的token。1.0=不惩罚。1.08-1.15推荐。', ja: '既出トークンにペナルティ。1.0=なし。1.08-1.15推奨。', en: 'Penalize repeated tokens. 1.0=off. 1.08-1.15 recommended.' },
    sampler_help_freq_pen:   { zh: '按出现频率惩罚。正值减少高频词。和Repeat Penalty二选一。', ja: '出現頻度でペナルティ。正=抑制。Repeat Penaltyと二択。', en: 'Penalize by frequency. Positive=reduce common words. Use this OR Repeat Penalty.' },
    sampler_help_pres_pen:   { zh: '类似Freq但看"是否出现过"。新话题引入有用。', ja: 'Freq類似だが"出現有無"のみ。新トピック導入に有効。', en: 'Like Freq but binary. Helps introduce new topics.' },
    sampler_help_max_tk:     { zh: '单次回复最大输出token数。4096足够大多数回复。', ja: '1回の返信の最大出力token。4096で十分。', en: 'Max output tokens per reply. 4096 is enough.' },
    sampler_help_hr_title:   { zh: 'Headroom 上下文压缩（控制 LLM 输入长度）', ja: 'Headroom 圧縮（入力長制御）', en: 'Headroom Context Compression (LLM input length)' },
    sampler_help_hr_core:    { zh: '核心问题：',            ja: '核心問題：',              en: 'Core Problem: ' },
    sampler_help_hr_desc:    { zh: '对话越长，上下文越接近token上限，最早记忆被挤出。Headroom自动压缩旧对话，保留关键信息。', ja: '会話が長くなるとtoken上限に近づき初期記憶が消える。Headroomが自動圧縮で重要情報を保持。', en: 'Long conversations near token limit. Headroom auto-compresses old history, keeping key info.' },
    sampler_help_smartcrusher: { zh: 'SmartCrusher 5维评分算法', ja: 'SmartCrusher 5次元スコアリング', en: 'SmartCrusher 5-Dimension Scoring' },
    sampler_help_sc1:        { zh: '首尾保留 — 开头30%和结尾15%优先保留', ja: '先頭末尾保持 — 先頭30%と末尾15%優先', en: 'First-last bias — 30% head + 15% tail kept' },
    sampler_help_sc2:        { zh: '错误保护 — system/error/warning 消息 100% 保留', ja: 'エラー保護 — system/error/warning 100%保持', en: 'Error protection — system/error/warning kept 100%' },
    sampler_help_sc3:        { zh: '统计异常 — 异常长/短消息保留', ja: '統計的外れ値 — 異常長/短を保持', en: 'Statistical outliers — unusually long/short kept' },
    sampler_help_sc4:        { zh: '查询相关 — 语义相关内容优先（BM25匹配）', ja: 'クエリ関連 — 意味的関連を優先（BM25）', en: 'Query relevance — semantic match prioritized (BM25)' },
    sampler_help_sc5:        { zh: '变化点 — 话题转换节点保留', ja: '変化点 — トピック転換節点を保持', en: 'Change points — topic transitions preserved' },
    sampler_help_hr_r1:     { zh: '最近N轮完整保留。4=保留最后4轮。', ja: '最近Nターン完全保持。4=最後4ターン。', en: 'Last N rounds kept full. 4=last 4 rounds.' },
    sampler_help_hr_r2:     { zh: '旧历史压缩后最多保留此数量。10=筛出10条最重要。', ja: '古い履歴圧縮後最大数。10=最重要10件。', en: 'After crushing, keep at most this many. 10=top 10.' },
    sampler_help_hr_r3:     { zh: '硬截断：消息总数不超过此值。24是安全值。', ja: '硬制限：総メッセージ数上限。24が安全。', en: 'Hard cap: total msgs ≤ this. 24 safe.' },
    sampler_help_hr_r4:     { zh: '硬截断：总字符数超过强制裁剪。40K≈1万token。', ja: '硬制限：総文字数超で強制切捨。40K≈1万token。', en: 'Hard cap: chars > this trimmed. 40K≈10k tokens.' },
    sampler_help_tips:       { zh: '调参建议：',           ja: '調整アドバイス：',       en: 'Tuning Tips:' },
    sampler_help_tip1:       { zh: '角色扮演：Sampler用Roleplay预设，Headroom默认(4/10/24/40k)', ja: 'RP：Sampler RPプリセット、Headroom初期値', en: 'Roleplay: Sampler Roleplay, Headroom default' },
    sampler_help_tip2:       { zh: '长对话：加大最近保留到6-8，减小压缩保留到6', ja: '長会話：最近保持6-8、圧縮後6', en: 'Long chats: Recent 6-8, Crushed 6' },
    sampler_help_tip3:       { zh: 'OOM：减小最大字符数到20k', ja: 'OOM：最大文字数20k', en: 'OOM: lower Max Chars to 20k' },
    sampler_help_tip4:       { zh: '重复：Temperature 0.5-0.6, Top P 0.7', ja: '繰返し：Temp 0.5-0.6, Top P 0.7', en: 'Repetition: Temp 0.5-0.6, Top P 0.7' },
    sampler_help_footer:     { zh: '参数实时生效。daemon stderr 含 [headroom] 统计。', ja: '即時反映。daemon stderrに [headroom] 統計。', en: 'Takes effect immediately. stderr logs [headroom] stats.' },

    // Sampler help popup
    sampler_help_title:      { zh: 'Sampler & 上下文压缩 — 参数说明', ja: 'Sampler & 圧縮 — パラメータ説明', en: 'Sampler & Headroom — Parameters' },
    sampler_help_sampler:    { zh: 'Sampler 参数（控制 LLM 输出随机性）', ja: 'Sampler パラメータ（出力ランダム性制御）', en: 'Sampler Parameters (LLM output randomness)' },
    sampler_help_hr_title:   { zh: 'Headroom 上下文压缩（控制 LLM 输入长度）', ja: 'Headroom 圧縮（入力長制御）', en: 'Headroom Context Compression (LLM input length)' },
    sampler_help_hr_core:    { zh: '核心问题：',            ja: '核心問題：',              en: 'Core Problem: ' },
    sampler_help_hr_desc:    { zh: '对话越长，上下文越接近模型token上限（12万），最早的记忆会被"挤出"窗口。Headroom在每次发消息前自动压缩旧对话，保留关键信息，节省token。', ja: '会話が長くなるとモデルのトークン上限に近づき、初期の記憶が消えます。Headroomは送信前に自動で旧会話を圧縮し、重要な情報を保持してトークンを節約します。', en: 'As conversations grow, context approaches the model token limit (120k). Earliest memories get pushed out of the window. Headroom automatically compresses old history before each message, preserving key info and saving tokens.' },
    sampler_help_smartcrusher: { zh: 'SmartCrusher 5维评分算法', ja: 'SmartCrusher 5次元スコアリング', en: 'SmartCrusher 5-Dimension Scoring Algorithm' },
    sampler_help_sc1:        { zh: '首尾保留 — 开头30%和结尾15%的历史优先保留（对话开场和结局最重要）', ja: '先頭末尾保持 — 先頭30%と末尾15%を優先保持', en: 'First-last bias — top 30% and last 15% of history kept first (openings and endings matter most)' },
    sampler_help_sc2:        { zh: '错误保护 — 包含 system/error/warning 的消息 100% 保留', ja: 'エラー保護 — system/error/warning 含むメッセージは100%保持', en: 'Error protection — messages with system/error/warning kept 100%' },
    sampler_help_sc3:        { zh: '统计异常 — 异常长/短的消息保留（可能含重要信息）', ja: '統計的外れ値 — 異常に長い/短いメッセージを保持', en: 'Statistical outliers — unusually long/short messages preserved (may contain key info)' },
    sampler_help_sc4:        { zh: '查询相关 — 与当前消息语义相关的内容优先保留（BM25匹配）', ja: 'クエリ関連 — 現在のメッセージと意味的に関連する内容を優先', en: 'Query relevance — content semantically related to current message prioritized (BM25)' },
    sampler_help_sc5:        { zh: '变化点 — 话题转换的节点保留', ja: '変化点 — トピック転換の節点を保持', en: 'Change points — topic transition nodes preserved' },
    sampler_help_hr_params:  { zh: 'Headroom 参数说明',    ja: 'Headroom パラメータ説明', en: 'Headroom Parameters' },
    sampler_help_hr_r1:     { zh: '最近N轮对话完整保留，不压缩。4=保留最后4轮（用户+AI各4条）。值越大上下文越连贯但token越多。', ja: '最近Nターン完全保持。4=最後4ターン。値が大きいほど連続性が高いがtoken消費増。', en: 'Last N rounds kept full, no compression. 4 = last 4 rounds (4 user + 4 AI messages). Higher = more coherent but more tokens.' },
    sampler_help_hr_r2:     { zh: '超出"最近轮数"的旧历史，压缩后最多保留此数量的消息。10条=从20+条旧消息中筛出10条最重要的。', ja: '古い履歴から圧縮後に残す最大メッセージ数。10 = 20+件から最重要10件。', en: 'After crushing old history, keep at most this many messages. 10 = select 10 most important from 20+ old messages.' },
    sampler_help_hr_r3:     { zh: '硬截断兜底。发往LLM的消息总数不超过此值。24是安全值（约8-12轮对话）。', ja: 'LLMへ送るメッセージ総数の上限。24が安全値（約8-12ターン）。', en: 'Hard cap fallback. Total messages sent to LLM never exceed this. 24 is a safe default (~8-12 rounds).' },
    sampler_help_hr_r4:     { zh: '硬截断兜底。总字符数超过此值强制裁剪。40K≈1万中文token，留足余量给模型推理。', ja: '総文字数の強制上限。40K≈1万日本語token。モデル推論用に余裕を残す。', en: 'Hard cap fallback. Total chars above this get trimmed. 40K ≈ 10k tokens, leaving headroom for model inference.' },
    sampler_help_tips:       { zh: '调参建议：',           ja: '調整アドバイス：',       en: 'Tuning Tips:' },
    sampler_help_tip1:       { zh: '• 角色扮演：Sampler用Roleplay预设，Headroom用默认(4/10/24/40k)', ja: '• RP：SamplerはRPプリセット、Headroomは初期値', en: '• Roleplay: Sampler on Roleplay preset, Headroom default (4/10/24/40k)' },
    sampler_help_tip2:       { zh: '• 长对话怕遗忘：加大"最近保留轮数"到6-8，减小"压缩保留条数"到6', ja: '• 長会話：最近保持6-8、圧縮後6に', en: '• Long chats: raise Recent Rounds to 6-8, lower Crushed Items to 6' },
    sampler_help_tip3:       { zh: '• 上下文爆炸（OOM）：减小"最大字符数"到20k', ja: '• OOM：最大文字数を20kに', en: '• Context explosion (OOM): lower Max Chars to 20k' },
    sampler_help_tip4:       { zh: '• 模型回复重复：降低Temperature到0.5-0.6，Top P到0.7', ja: '• 繰返し：Temperature 0.5-0.6, Top P 0.7', en: '• Repetition: lower Temperature to 0.5-0.6, Top P to 0.7' },
    sampler_help_footer:     { zh: '参数实时生效，无需重启。daemon stderr日志含 [headroom] 压缩统计。', ja: 'パラメータは即時反映。daemonのstderrに [headroom] 統計表示。', en: 'Parameters take effect immediately. daemon stderr logs contain [headroom] stats.' },

    // Sampler 参数标签（简短，slider label）
    sp_temp:                 { zh: 'Temperature',          ja: 'Temperature',          en: 'Temperature' },
    sp_top_p:                { zh: 'Top P',                ja: 'Top P',                en: 'Top P' },
    sp_top_k:                { zh: 'Top K',                ja: 'Top K',                en: 'Top K' },
    sp_min_p:                { zh: 'Min P',                ja: 'Min P',                en: 'Min P' },
    sp_rep_pen:              { zh: 'Repeat Penalty',       ja: 'Repeat Penalty',       en: 'Repeat Penalty' },
    sp_freq_pen:             { zh: 'Freq Penalty',         ja: 'Freq Penalty',         en: 'Freq Penalty' },
    sp_pres_pen:             { zh: 'Pres Penalty',         ja: 'Pres Penalty',         en: 'Pres Penalty' },
    sp_max_tokens:           { zh: 'Max Tokens',           ja: 'Max Tokens',           en: 'Max Tokens' },

    // Manual Paint modal
    paint_manual_title:      { zh: '🎨 手动画图',          ja: '🎨 手動描画',            en: '🎨 Manual Paint' },
    paint_pos_label:         { zh: '正向提示词',           ja: 'ポジティブプロンプト',   en: 'Positive Prompt' },
    paint_pos_hint:          { zh: '（英文逗号分隔标签）', ja: '（英語、カンマ区切り）',  en: '(English, comma-separated tags)' },
    paint_neg_label:         { zh: '负向提示词',           ja: 'ネガティブプロンプト',   en: 'Negative Prompt' },
    paint_quick_presets:     { zh: '快速预设',             ja: 'クイックプリセット',    en: 'Quick Presets' },
    paint_need_pos:          { zh: '请输入正向提示词',     ja: 'ポジティブプロンプトを入力してください', en: 'Please enter a positive prompt' },
    paint_cancel:            { zh: '取消',                 ja: 'キャンセル',           en: 'Cancel' },
    paint_generate:          { zh: '生成',                 ja: '生成',                 en: 'Generate' },
    paint_stop_llama_hint:   { zh: '将停止 llama 以释放资源（生成后自动重启）', ja: 'llamaを停止して資源解放（生成後に自動再開）', en: 'Will stop llama to free resources (auto-restarts after)' },
    paint_keep_llama_hint:   { zh: 'llama 保持运行（未停止）', ja: 'llama 稼働中（停止しない）', en: 'llama stays running (not stopped)' },

    // Forced injection (auto paint / regenerate)
    paint_forced_title:      { zh: '🔒 AI 自动画图强制注入', ja: '🔒 AI自動描画の強制注入', en: '🔒 Forced Injection (Auto Paint)' },
    paint_forced_hint:       { zh: '自动画图 / regenerate 时强制注入；不作用于本次手动绘制', ja: '自動描画・regenerate時に強制注入（手動描画には影響なし）', en: 'Forced into auto paint & regenerate (not this manual job)' },
    paint_forced_pos:        { zh: '强制正面提示词（追加到自动 prompt）', ja: '強制ポジティブ（自動プロンプトに追加）', en: 'Forced positive (appended to auto prompt)' },
    paint_forced_pos_ph:     { zh: '如: masterpiece, (shiki natsume:1.1), detailed eyes', ja: '例: masterpiece, (shiki natsume:1.1), detailed eyes', en: 'e.g. masterpiece, (shiki natsume:1.1), detailed eyes' },
    paint_forced_neg:        { zh: '强制负面提示词（覆盖默认）', ja: '強制ネガティブ（デフォルトを上書き）', en: 'Forced negative (overrides default)' },
    paint_forced_neg_ph:     { zh: '如: bad hands, extra fingers', ja: '例: bad hands, extra fingers', en: 'e.g. bad hands, extra fingers' },
    paint_forced_res:        { zh: '强制分辨率（留空用默认）', ja: '強制解像度（空欄はデフォルト）', en: 'Forced resolution (blank = default)' },
    paint_forced_res_hint:   { zh: '留空使用默认 768×1024×24', ja: '空欄はデフォルト 768×1024×24', en: 'Blank = default 768×1024×24' },
  };

  // ── State ──
  var _lang = localStorage.getItem('chat_language') || 'zh';

  // ── Public API ──
  window.i18n = function (key) {
    var entry = T[key];
    if (!entry) return key;
    return entry[_lang] || entry['zh'] || key;
  };
  window.tr = window.i18n;

  window.getLang = function () { return _lang; };

  window.setLang = function (lang) {
    if (!lang || !T.app_title[lang]) return;
    _lang = lang;
    localStorage.setItem('chat_language', lang);

    // Update all [data-i18n] elements
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var key = el.getAttribute('data-i18n');
      var text = window.i18n(key);
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = text;
      } else if (el.tagName === 'OPTION') {
        el.textContent = text;
      } else {
        el.textContent = text;
      }
    });

    // Update [data-i18n-title]
    document.querySelectorAll('[data-i18n-title]').forEach(function (el) {
      el.title = window.i18n(el.getAttribute('data-i18n-title'));
    });

    // Update lang dropdown buttons
    document.querySelectorAll('.lang-btn').forEach(function (b) {
      b.classList.toggle('active', b.dataset.lang === lang);
    });

    // Update lang trigger label
    var labels = { zh: '中', ja: '日', en: 'EN' };
    var label = document.getElementById('lang-current-label');
    if (label) label.textContent = labels[lang] || '中';

    // Update settings object
    try {
      var s = JSON.parse(localStorage.getItem('artemis_settings') || '{}');
      s.language = lang;
      localStorage.setItem('artemis_settings', JSON.stringify(s));
    } catch (e) {}

    // Rebuild sampler panel (has inline text)
    if (typeof window._samplerPanelRebuild === 'function') {
      window._samplerPanelRebuild();
    }
  };

  // ── Init ──
  window.setLang(_lang);
})();
