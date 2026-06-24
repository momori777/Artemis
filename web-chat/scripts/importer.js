// ============================================================
// importer.js - Import character definitions (PNG/JSON/TXT)
// Automatically detects format — no guessing required.
// ============================================================

var CharacterImporter = {

  // ---- PNG parser (SillyTavern chara v2/v3 embedded) ----
  parsePNG: function(buffer) {
    var bytes = new Uint8Array(buffer);
    var sig = [137, 80, 78, 71, 13, 10, 26, 10];
    for (var i = 0; i < 8; i++) {
      if (bytes[i] !== sig[i]) throw new Error('Not a valid PNG file');
    }
    var pos = 8;
    var charaJSON = null;
    while (pos < bytes.length) {
      var length = (bytes[pos] << 24) | (bytes[pos + 1] << 16) | (bytes[pos + 2] << 8) | bytes[pos + 3];
      pos += 4;
      var type = String.fromCharCode(bytes[pos], bytes[pos + 1], bytes[pos + 2], bytes[pos + 3]);
      pos += 4;
      if (type === 'IEND') break;
      var data = bytes.slice(pos, pos + length);
      pos += length + 4;
      if (type === 'tEXt') {
        var nullIdx = -1;
        for (var i = 0; i < data.length; i++) {
          if (data[i] === 0) { nullIdx = i; break; }
        }
        if (nullIdx < 0) continue;
        var keyword = '';
        for (var i = 0; i < nullIdx; i++) { keyword += String.fromCharCode(data[i]); }
        if (keyword === 'chara') {
          var textBytes = data.slice(nullIdx + 1);
          var b64 = '';
          for (var i = 0; i < textBytes.length; i++) { b64 += String.fromCharCode(textBytes[i]); }
          try { charaJSON = JSON.parse(atob(b64)); } catch (e) { /* skip */ }
        } else if (keyword === 'ccv3') {
          var txt = new TextDecoder('utf-8').decode(data.slice(nullIdx + 1));
          try { charaJSON = JSON.parse(txt); } catch (e) { /* skip */ }
        }
      }
    }
    return charaJSON;
  },

  // ---- Auto-detect and parse ANY JSON blob ----
  parseJSONBlob: function(jsonText) {
    var data;
    try { data = JSON.parse(jsonText); } catch (e) {
      throw new Error('Invalid JSON');
    }
    return this._normalizeAnyJSON(data);
  },

  _normalizeAnyJSON: function(data) {
    if (!data || typeof data !== 'object') throw new Error('Not a JSON object');

    // If it's an array, take the first object
    if (Array.isArray(data)) {
      if (data.length === 0) throw new Error('Empty array');
      data = data[0];
    }

    // Try the common SillyTavern card wrappers
    // v2/v3: { spec: "chara_card_v2", data: { name: ... } }
    if (data.data && typeof data.data === 'object' && data.data.name) {
      data = data.data;
    }
    // v1 or flat: { name: ..., description: ... }
    // TavernAI: { char_name: ..., char_persona: ..., char_greeting: ... }
    else if (data.char_name) {
      data = {
        name: data.char_name,
        personality: data.char_persona || data.description || '',
        description: data.char_persona || data.description || data.world_scenario || '',
        first_mes: data.char_greeting || '',
        scenario: data.world_scenario || '',
        mes_example: data.example_dialogue || '',
        system_prompt: data.system_prompt || '',
        creator_notes: data.creatorcomment || data.creator_notes || '',
        tags: data.tags || [],
      };
    }
    // RisuAI / Agnai: { name: ..., personality: ..., scenario: ..., first_mes: ... }
    // Already flat, just ensure name exists
    if (!data.name) {
      // Try other name fields
      data.name = data.character_name || data.charName || data.display_name || data.title || '';
    }

    return data;
  },

  // ---- Parse TXT: extract name + personality from plain text ----
  parseTXTBlob: function(text) {
    text = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').trim();
    if (!text) throw new Error('Empty text file');

    var lines = text.split('\n').map(function(l) { return l.trim(); });
    var name = '';
    var personality = '';
    var description = '';
    var scenario = '';
    var firstMes = '';
    var tags = [];
    var source = '';
    var section = 'header';

    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      if (!line) continue;

      // Detect section headers
      var headerMatch = line.match(/^#+\s*(.+)$/);
      if (headerMatch) {
        var h = headerMatch[1].toLowerCase();
        if (h.indexOf('personality') !== -1 || h.indexOf('性格') !== -1 || h.indexOf('人设') !== -1) {
          section = 'personality'; continue;
        }
        if (h.indexOf('scenario') !== -1 || h.indexOf('场景') !== -1 || h.indexOf('背景') !== -1 || h.indexOf('background') !== -1) {
          section = 'scenario'; continue;
        }
        if (h.indexOf('greeting') !== -1 || h.indexOf('first') !== -1 || h.indexOf('开场') !== -1 || h.indexOf('问候') !== -1) {
          section = 'firstMes'; continue;
        }
        if (h.indexOf('tag') !== -1 || h.indexOf('标签') !== -1 || h.indexOf('trait') !== -1) {
          section = 'tags'; continue;
        }
        if (h.indexOf('source') !== -1 || h.indexOf('来源') !== -1 || h.indexOf('出处') !== -1) {
          section = 'source'; continue;
        }
        if (h.indexOf('desc') !== -1 || h.indexOf('描述') !== -1 || h.indexOf('设定') !== -1) {
          section = 'description'; continue;
        }
        // Unknown header -> treat as description
        section = 'description';
        continue;
      }

      // Detect key-value lines: "Name: Natsume" / "名前：夏目"
      var kv = line.match(/^([A-Za-z\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\-_\s]+)[：:]\s*(.+)$/);
      if (kv) {
        var key = kv[1].toLowerCase().trim();
        var val = kv[2].trim();
        if (key === 'name' || key === '名前' || key === '名字' || key === '名称' || key === '姓名' || key === '角色名') {
          name = val; section = 'header'; continue;
        }
        if (key === 'personality' || key === '性格' || key === '个性') {
          personality = val; section = 'personality'; continue;
        }
        if (key === 'scenario' || key === '场景') {
          scenario = val; section = 'scenario'; continue;
        }
        if (key === 'first_mes' || key === 'greeting' || key === '开场白' || key === '第一句话') {
          firstMes = val; section = 'firstMes'; continue;
        }
        if (key === 'tags' || key === '标签') {
          tags = val.split(/[,，\s]+/).filter(Boolean); section = 'tags'; continue;
        }
        if (key === 'source' || key === '来源' || key === '出处') {
          source = val; section = 'source'; continue;
        }
        if (key === 'description' || key === '描述' || key === '设定') {
          description = val; section = 'description'; continue;
        }
      }

      // Accumulate into current section
      switch (section) {
        case 'header':
          if (!name) { name = line; section = 'description'; }
          else { description += (description ? '\n' : '') + line; }
          break;
        case 'personality': personality += (personality ? '\n' : '') + line; break;
        case 'description': description += (description ? '\n' : '') + line; break;
        case 'scenario': scenario += (scenario ? '\n' : '') + line; break;
        case 'firstMes': firstMes += (firstMes ? '\n' : '') + line; break;
        case 'tags':
          tags = tags.concat(line.split(/[,，\s]+/).filter(Boolean)); break;
        case 'source': source += (source ? ' ' : '') + line; break;
        default: description += (description ? '\n' : '') + line; break;
      }
    }

    // If no name found, use first non-empty line or filename
    if (!name) name = 'Custom';

    // If no personality, use beginning of description
    if (!personality && description) {
      personality = description.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim().slice(0, 120);
    }

    return {
      name: name,
      personality: personality,
      description: description,
      scenario: scenario,
      first_mes: firstMes,
      tags: tags,
      creator_notes: source,
    };
  },

  // ---- Convert ANY parsed data to CHARACTER format ----
  convert: function(charaCard) {
    var d = charaCard || {};

    var name = d.name || 'Imported';
    var id = 'imported-' + name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') + '-' + Date.now().toString(36);

    var persona = (d.personality || '').slice(0, 60);
    if (!persona) {
      var desc = d.description || '';
      desc = desc.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim().slice(0, 60);
      persona = desc || 'Custom character';
    }

    var personaNote = d.creator_notes || d.creatorcomment || '';
    if (!personaNote && d.description) {
      personaNote = d.description.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim().slice(0, 80);
    }
    if (!personaNote) personaNote = 'Imported character';

    var tags = (Array.isArray(d.tags) ? d.tags : []).slice(0, 5);
    var accent = this._generateAccent(name);
    var icon = (name.charAt(0) || '?').toLowerCase();

    // Detect language from name characters
    var hasCJK = /[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]/.test(name);
    var ttsLang = hasCJK ? 'ja' : 'en';

    // Build system prompt from card data — inject the character's real description
    var sysPrompt = d.system_prompt || '';
    if (!sysPrompt && (d.description || d.personality)) {
      sysPrompt = 'You are ' + name + '. ';
      if (d.personality) sysPrompt += 'Personality: ' + d.personality + '. ';
      if (d.scenario) sysPrompt += 'Scenario: ' + d.scenario + '. ';
      sysPrompt += 'Stay in character. Respond naturally.';
    }

    // Build first message — use card's first_mes, or generate one
    var firstMes = d.first_mes || '';
    if (!firstMes) {
      firstMes = 'Hello! I am ' + name + '.';
    }

    // Fallback replies in appropriate language
    var fallbacks = hasCJK ? [
      '嗯，我在。',
      '继续说，我在听。',
      '明白了。',
      '嗯...',
      '你想聊什么？',
      '我一直都在。',
    ] : [
      'I\'m here.',
      'Tell me more.',
      'I see...',
      'Mm, understood.',
      'What do you think?',
      'Let\'s talk about it.',
    ];
    // If card has mes_example, extract some lines as fallback flavor
    if (d.mes_example) {
      var examples = d.mes_example.split(/\n/).filter(function(l) {
        return l.trim() && l.trim().length < 120;
      }).slice(0, 3);
      if (examples.length > 0) {
        fallbacks = examples.map(function(l) { return l.trim().replace(/^[^:]+:\s*/, ''); });
      }
    }

    return {
      id: id,
      name: name,
      nameEn: name,
      icon: icon,
      persona: persona,
      personaNote: personaNote,
      tags: tags.length ? tags : ['Imported'],
      source: d.creator ? 'Created by ' + d.creator : 'Imported character',
      accent: accent,
      imported: true,
      rawCard: d,
      firstMes: firstMes,
      scenario: d.scenario || '',
      systemPrompt: sysPrompt,
      fallbackReplies: fallbacks,
      ttsLang: ttsLang,
      ttsMood: 'casual',
    };
  },

  _generateAccent: function(name) {
    var hash = 0;
    for (var i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
      hash = hash & hash;
    }
    var h = Math.abs(hash);
    var r = Math.floor(((h & 0xFF0000) >> 16) * 0.7 + 80);
    var g = Math.floor(((h & 0x00FF00) >> 8) * 0.5 + 90);
    var b = Math.floor((h & 0x0000FF) * 0.6 + 80);
    return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
  },

  // ---- Main import: auto-detect type, try all parsers ----
  importFile: function(file, customName) {
    var self = this;
    return new Promise(function(resolve, reject) {
      var ext = file.name.toLowerCase().split('.').pop();

      if (ext === 'png') {
        var pngReader = new FileReader();
        pngReader.onload = function(e) {
          try {
            var charaCard = self.parsePNG(e.target.result);
            if (!charaCard) throw new Error('No character data in PNG (missing tEXt:chara chunk)');
            if (customName) charaCard.name = customName;
            resolve(self.convert(charaCard));
          } catch (err) { reject(err); }
        };
        pngReader.onerror = function() { reject(new Error('Failed to read PNG')); };
        pngReader.readAsArrayBuffer(file);
        return;
      }

      var textReader = new FileReader();
      textReader.onload = function(e) {
        try {
          var raw = e.target.result;
          var charaData;

          try {
            charaData = self.parseJSONBlob(raw);
          } catch (jsonErr) {
            try {
              charaData = self.parseTXTBlob(raw);
            } catch (txtErr) {
              throw new Error(
                'Could not parse this file. ' +
                'Supported: PNG character cards, JSON (any SillyTavern/RisuAI/Agnai format), or plain text with name/description.'
              );
            }
          }

          if (customName) charaData.name = customName;
          resolve(self.convert(charaData));
        } catch (err) { reject(err); }
      };
      textReader.onerror = function() { reject(new Error('Failed to read file')); };
      textReader.readAsText(file, 'utf-8');
    });
  },

  // ---- Prompt user for character name, then import ----
  promptAndImport: function(file) {
    var self = this;
    var defaultName = file.name.replace(/\.[^.]+$/, '').replace(/[_\-]+/g, ' ').replace(/\b\w/g, function(c) { return c.toUpperCase(); });

    var name = prompt('Enter character name:', defaultName);
    if (name === null) return; // cancelled
    name = name.trim();
    if (!name) name = defaultName;

    self.importFile(file, name).then(function(char) {
      var added = self.addCharacter(char);
      if (added) {
        UI.showToast('Imported: ' + char.name, 'success');
        UI.rebuildCharList();
        UI.selectCharacter(char.id);
      } else {
        UI.showToast(char.name + ' already imported', 'warning');
      }
    }).catch(function(err) {
      UI.showToast('Import failed: ' + err.message, 'error');
    });
  },

  // ---- Character management ----
  addCharacter: function(char) {
    // Check for duplicate
    for (var i = 0; i < CHARACTERS.length; i++) {
      if (CHARACTERS[i].id === char.id) return false;
    }
    // Save to localStorage
    this._saveOne(char);
    // Rebuild CHARACTERS via the single-source-of-truth merge
    if (typeof mergeAllCharacters === 'function') {
      // Get current API data... we can't, so just push + sort
    }
    CHARACTERS.push(char);
    return true;
  },

  _saveOne: function(char) {
    var raw = localStorage.getItem('ai-gf-imported-chars');
    var list = [];
    try { if (raw) list = JSON.parse(raw); } catch (e) {}
    // Remove old entry with same id
    list = list.filter(function(c) { return c.id !== char.id; });
    // Strip rawCard before saving
    var clone = {};
    for (var k in char) { if (k !== 'rawCard') clone[k] = char[k]; }
    list.push(clone);
    try {
      localStorage.setItem('ai-gf-imported-chars', JSON.stringify(list));
    } catch (e) {
      // Trim if full
      var minimal = list.map(function(c) {
        return { id: c.id, name: c.name, icon: c.icon, persona: c.persona, accent: c.accent, imported: true };
      });
      localStorage.setItem('ai-gf-imported-chars', JSON.stringify(minimal));
    }
  },

  _saveImported: function() {
    var imported = CHARACTERS.filter(function(c) { return c.imported; });
    var clean = imported.map(function(c) {
      var clone = {};
      for (var k in c) { if (k !== 'rawCard') clone[k] = c[k]; }
      return clone;
    });
    try { localStorage.setItem('ai-gf-imported-chars', JSON.stringify(clean)); } catch (e) {
      var minimal = imported.map(function(c) {
        return { id: c.id, name: c.name, icon: c.icon, persona: c.persona, accent: c.accent, imported: true };
      });
      localStorage.setItem('ai-gf-imported-chars', JSON.stringify(minimal));
    }
  },

  removeCharacter: function(id) {
    var idx = -1;
    for (var i = 0; i < CHARACTERS.length; i++) {
      if (CHARACTERS[i].id === id && CHARACTERS[i].imported) { idx = i; break; }
    }
    if (idx >= 0) { CHARACTERS.splice(idx, 1); this._saveImported(); return true; }
    return false;
  },

  init: function() {
    var self = this;
    var fileInput = document.getElementById('import-char-file');
    if (!fileInput) return;

    fileInput.addEventListener('change', function() {
      var file = fileInput.files[0];
      if (!file) return;
      self.promptAndImport(file);
      fileInput.value = '';
    });
  },
};
