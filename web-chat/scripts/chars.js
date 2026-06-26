// ============================================================
// chars.js - Character definitions for AI Girlfriend
// Loads from daemon API (port 19260) which scans skills/harem/
// Falls back to hardcoded defaults if daemon is unreachable.
// Imported characters survive API refreshes via localStorage.
// ============================================================

var CHARACTERS = [];
var CHARACTERS_LOADED = false;
var CHAR_API_PROMISE = null;

var CHAR_FALLBACKS = {
  natsume: {
    id: 'natsume',
    name: '四季夏目',
    nameEn: 'Shiki Natsume',
    icon: 'n',
    persona: '外冷内热 / 安静陪伴 / 四爱向',
    personaNote: '话不多但每句都有分量',
    tags: ['高岭之花', '小娇妻感', '毒舌', '独占欲'],
    source: '星光咖啡蝶与死神之馆',
    accent: '#d4787a',
    ttsLang: 'ja',
    ttsMood: 'casual',
  },
  sakura: {
    id: 'sakura',
    name: '夜乃桜',
    nameEn: 'Yono Sakura',
    icon: 's',
    persona: '冷静孤高 / 前生徒会长 / 守护者',
    personaNote: '关心笨拙但比谁都认真',
    tags: ['冷娇', '守护者', '最强战力', '责任感'],
    source: 'Dimension Lovers!!',
    accent: '#7e9ec8',
    ttsLang: 'ja',
    ttsMood: 'tsundere',
  },
  enola: {
    id: 'enola',
    name: 'Enola',
    nameEn: 'Enola',
    icon: 'e',
    persona: '温柔体贴 / 治愈系 / 陪伴型',
    personaNote: '永远在你身边',
    tags: ['温柔', '治愈', '忠诚', '陪伴'],
    source: '原创角色',
    accent: '#c4a882',
    ttsLang: 'ja',
    ttsMood: 'romantic',
  },
  atori: {
    id: 'atori',
    name: '亚托莉',
    nameEn: 'ATRI',
    icon: 'a',
    persona: '活泼元气 / 机器人少女 / 好奇心旺盛',
    personaNote: '对世界充满好奇的机械心',
    tags: ['元气', '机器人', '好奇心', '直率'],
    source: 'ATRI -My Dear Moments-',
    accent: '#6eb5c0',
    ttsLang: 'ja',
    ttsMood: 'casual',
  },
  ruruka: {
    id: 'ruruka',
    name: '森亚露露卡',
    nameEn: 'Moria Ruruka',
    icon: 'r',
    persona: '高冷寡言 / 暗之美少女 / 温柔忠诚',
    personaNote: '对外高冷，只对你一人敞开心扉',
    tags: ['高冷', '暗之美少女', '寡言', '发小&妻子', '哥特系'],
    source: '光之美少女世界书 / DZMM原创角色卡',
    accent: '#7b4f9e',
    ttsLang: 'ja',
    ttsMood: 'tsundere',
  },
};

var FALLBACK_REPLIES = {
  natsume: [
    '嗯，知道了。',
    '这样说啊...我会记住的。',
    '笨蛋，这么晚了还不睡。',
    '哼，算你有心。',
    '...我在听。',
    '知道了，别一直说。',
    '偶尔也让我主动一下嘛。',
    '你啊，总是这样。',
    '好，陪你一会儿。',
    '别太勉强自己。',
  ],
  sakura: [
    '...嗯。',
    '大丈夫、私がいる。',
    '無理しないで。',
    'ちゃんと見て。',
    '君は...本当にバカだな。',
    '...少し嬉しい。',
    '休んで。今すぐ。',
    '少し寂しい...なんてな。',
    'うん、わかった。',
    'そばにいる。',
  ],
  enola: [
    '我在呢，有什么事想说吗？',
    '今天辛苦了，好好休息吧。',
    '嗯，我能理解你的感受。',
    '没关系，慢慢来。',
    '我一直都在这里。',
    '需要我陪你聊聊天吗？',
    '能和你在一起，我很开心。',
    '不要一个人扛着，有我在。',
  ],
  atori: [
    '哇，好有趣！',
    '诶诶，这是什么意思？',
    '主人主人，快告诉我更多！',
    '嘻嘻，我明白了！',
    '嗯嗯，继续说呀~',
    '那个...能再说一次吗？',
    '我也想试试看！',
    '主人今天心情怎么样？',
  ],
  ruruka: [
    '...（绵糖探：露露卡大人说她在听）',
    '哼，随你便。',
    '...冰淇淋呢？',
    '（绵糖探：露露卡大人觉得你今天还不错）',
    '少废话，直接说事。',
    '...别以为这样我就会高兴。',
    '（绵糖探：露露卡大人笑了，我看见了！）',
    '统治世界的约定，你还记得吗...',
  ],
};

var DEFAULT_CHAR_ID = 'natsume';

// ---- Single source of truth: merge all sources into CHARACTERS ----
function mergeAllCharacters(apiData) {
  var result = [];
  var seen = {};

  // 1. Load imported chars from localStorage first (they survive everything)
  try {
    var raw = localStorage.getItem('ai-gf-imported-chars');
    if (raw) {
      var imported = JSON.parse(raw);
      imported.forEach(function(c) {
        c.imported = true;
        ensureDefaults(c);
        result.push(c);
        seen[c.id] = true;
      });
    }
  } catch (e) {}

  // 2. API data (from harem scan) — merge with fallback enrichment
  if (apiData && Array.isArray(apiData) && apiData.length > 0) {
    apiData.forEach(function(c) {
      var fb = CHAR_FALLBACKS[c.id] || {};
      var id = c.id || fb.id;
      if (seen[id]) return; // already imported
      seen[id] = true;
      result.push({
        id: id,
        name: c.name || fb.name,
        nameEn: c.nameEn || fb.nameEn,
        icon: c.icon || fb.icon,
        avatar: c.avatar || null,
        persona: c.persona || fb.persona || '',
        personaNote: c.personaNote || fb.personaNote || '',
        tags: c.tags || fb.tags || [],
        source: c.source || fb.source || '',
        accent: c.accent || fb.accent || '#c4a882',
        ttsLang: c.ttsLang || fb.ttsLang || 'ja',
        ttsMood: c.ttsMood || fb.ttsMood || 'casual',
        fallbackReplies: c.fallbackReplies || FALLBACK_REPLIES[c.id] || ['I\'m here.'],
      });
    });
  }

  // 3. Fill in any missing fallback chars (not already in result)
  Object.keys(CHAR_FALLBACKS).forEach(function(id) {
    if (seen[id]) return;
    seen[id] = true;
    var fb = CHAR_FALLBACKS[id];
    result.push(Object.assign({}, fb, {
      fallbackReplies: FALLBACK_REPLIES[id] || ['I\'m here.'],
    }));
  });

  CHARACTERS = result;
  CHARACTERS_LOADED = true;
}

function ensureDefaults(c) {
  if (!c.fallbackReplies) c.fallbackReplies = ['I\'m here.', 'Tell me more.', 'I see...', 'Mm.', 'What do you think?'];
  if (!c.tags) c.tags = ['Imported'];
  if (!c.source) c.source = 'Imported character';
  if (!c.icon) c.icon = (c.name || '?').charAt(0).toLowerCase();
  if (!c.accent) c.accent = '#888';
  if (!c.avatar) c.avatar = null;
  if (!c.persona) c.persona = 'Custom character';
  if (!c.personaNote) c.personaNote = 'Imported character';
  if (!c.nameEn) c.nameEn = c.name || '';
  if (!c.ttsLang) c.ttsLang = 'en';
  if (!c.ttsMood) c.ttsMood = 'casual';
}

// ---- Boot: build CHARACTERS from fallback + localStorage first, then API ----
function loadCharactersFromAPI() {
  return fetch('http://localhost:19260/api/characters', {
    signal: AbortSignal.timeout(3000),
  })
    .then(function (r) {
      if (!r.ok) throw new Error('API error: ' + r.status);
      return r.json();
    })
    .then(function (data) {
      mergeAllCharacters(data);
    })
    .catch(function (err) {
      console.warn('Failed to load characters from API:', err.message);
      mergeAllCharacters(null); // fallback-only merge
    });
}

function getChar(id) {
  return CHARACTERS.find(function (c) {
    return c.id === id;
  }) || CHARACTERS[0];
}

function getFallbackReply(charId) {
  var c = getChar(charId);
  var r = c && c.fallbackReplies ? c.fallbackReplies : FALLBACK_REPLIES[charId] || ['Mm.'];
  return r[Math.floor(Math.random() * r.length)];
}

// ---- Boot ----
(function () {
  // 1. Load from CHARACTERS_JSON.js (hardcoded file with all 6 characters)
  if (typeof CHARACTERS_JSON !== 'undefined' && Array.isArray(CHARACTERS_JSON)) {
    mergeAllCharacters(CHARACTERS_JSON);
  } else {
    // 2. Fallback: use fallbacks only
    mergeAllCharacters(null);
  }
  // 3. API data (from harem scan) — merge with fallback enrichment
  CHAR_API_PROMISE = loadCharactersFromAPI();
})();
