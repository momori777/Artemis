// ============================================================
// chars.js - Character definitions for AI Girlfriend
// Loads from daemon API (port 19260) which scans skills/harem/
// Falls back to hardcoded defaults if daemon is unreachable.
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
};

var DEFAULT_CHAR_ID = 'natsume';

function loadCharactersFromAPI() {
  return fetch('http://localhost:19260/api/characters', {
    signal: AbortSignal.timeout(3000),
  })
    .then(function (r) {
      if (!r.ok) throw new Error('API error: ' + r.status);
      return r.json();
    })
    .then(function (data) {
      if (Array.isArray(data) && data.length > 0) {
        // Convert API data to CHARACTERS format, merging with fallback data
        CHARACTERS = data.map(function (c) {
          var fb = CHAR_FALLBACKS[c.id] || {};
          return {
            id: c.id || fb.id,
            name: c.name || fb.name,
            nameEn: c.nameEn || fb.nameEn,
            icon: c.icon || fb.icon,
            persona: c.persona || fb.persona || '',
            personaNote: c.personaNote || fb.personaNote || '',
            tags: c.tags || fb.tags || ['Imported'],
            source: c.source || fb.source || '',
            accent: c.accent || fb.accent || '#c4a882',
            ttsLang: c.ttsLang || fb.ttsLang || 'ja',
            ttsMood: c.ttsMood || fb.ttsMood || 'casual',
            fallbackReplies: c.fallbackReplies || FALLBACK_REPLIES[c.id] || ['I\'m here.'],
          };
        });
        CHARACTERS_LOADED = true;
      }
    })
    .catch(function (err) {
      console.warn('Failed to load characters from API, using fallback:', err.message);
      loadFallbackCharacters();
    });
}

function loadFallbackCharacters() {
  CHARACTERS = Object.values(CHAR_FALLBACKS).map(function (fb) {
    return Object.assign({}, fb, {
      fallbackReplies: FALLBACK_REPLIES[fb.id] || ['I\'m here.'],
    });
  });
  CHARACTERS_LOADED = true;
}

function getChar(id) {
  return CHARACTERS.find(function (c) {
    return c.id === id;
  }) || CHARACTERS[0];
}

function getFallbackReply(charId) {
  var c = getChar(charId);
  var r = c.fallbackReplies || FALLBACK_REPLIES[charId] || ['Mm.'];
  return r[Math.floor(Math.random() * r.length)];
}

// ---- Boot: load fallback first so UI renders immediately,
// then replace with API data if available. ----
(function () {
  loadFallbackCharacters();
  CHAR_API_PROMISE = loadCharactersFromAPI();
})();
