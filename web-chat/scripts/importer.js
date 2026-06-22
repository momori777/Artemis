// ============================================================
// importer.js - Import SillyTavern character cards (PNG/JSON)
// ============================================================

var CharacterImporter = {
  // Parse a PNG character card (v2/v3 spec)
  parsePNG: function(buffer) {
    var bytes = new Uint8Array(buffer);

    // Check PNG signature
    var sig = [137, 80, 78, 71, 13, 10, 26, 10];
    for (var i = 0; i < 8; i++) {
      if (bytes[i] !== sig[i]) throw new Error('Not a valid PNG file');
    }

    var pos = 8;
    var charaJSON = null;

    while (pos < bytes.length) {
      // Read chunk length (big-endian uint32)
      var length = (bytes[pos] << 24) | (bytes[pos + 1] << 16) | (bytes[pos + 2] << 8) | bytes[pos + 3];
      pos += 4;
      // Read chunk type
      var type = String.fromCharCode(bytes[pos], bytes[pos + 1], bytes[pos + 2], bytes[pos + 3]);
      pos += 4;

      if (type === 'IEND') break;

      // Read chunk data
      var data = bytes.slice(pos, pos + length);
      pos += length;
      pos += 4; // skip CRC

      if (type === 'tEXt') {
        // Find null separator between keyword and text
        var nullIdx = -1;
        for (var i = 0; i < data.length; i++) {
          if (data[i] === 0) { nullIdx = i; break; }
        }
        if (nullIdx < 0) continue;

        var keyword = '';
        for (var i = 0; i < nullIdx; i++) {
          keyword += String.fromCharCode(data[i]);
        }

        if (keyword === 'chara') {
          // Extract base64 text
          var textBytes = data.slice(nullIdx + 1);
          var b64 = '';
          for (var i = 0; i < textBytes.length; i++) {
            b64 += String.fromCharCode(textBytes[i]);
          }
          try {
            var decoded = atob(b64);
            charaJSON = JSON.parse(decoded);
          } catch (e) {
            throw new Error('Failed to decode character card data: ' + e.message);
          }
        }
      }
    }

    return charaJSON;
  },

  // Convert a character card JSON to our CHARACTERS format
  convert: function(charaCard) {
    var spec = charaCard.spec || 'chara_card_v2';
    var d;

    if (spec === 'chara_card_v2' || spec === 'chara_card_v3') {
      d = charaCard.data || {};
    } else {
      // V1 or flat format
      d = charaCard;
    }

    var name = d.name || 'Imported';
    var id = 'imported-' + name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') + '-' + Date.now().toString(36);

    // Build persona/tags from available fields
    var persona = d.personality || '';
    var description = d.description || '';
    var tags = (d.tags || []).slice(0, 5);
    var personaNote = d.creator_notes || d.creatorcomment || '';
    if (!personaNote && description) {
      personaNote = description.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim().slice(0, 80);
    }

    // Accent color - generate from name hash if not specified
    var accent = this._generateAccent(name);
    var icon = name.charAt(0).toLowerCase();

    return {
      id: id,
      name: name,
      nameEn: name,
      icon: icon,
      persona: persona.slice(0, 60) || 'Custom character',
      personaNote: personaNote.slice(0, 60) || 'Imported from SillyTavern',
      tags: tags.length ? tags : ['Imported'],
      source: d.creator ? 'Created by ' + d.creator : 'Imported character',
      accent: accent,
      imported: true,
      rawCard: charaCard,
      firstMes: d.first_mes || '',
      scenario: d.scenario || '',
      systemPrompt: d.system_prompt || '',
      fallbackReplies: [
        'I\'m here.',
        'Tell me more.',
        'I see...',
        'Mm, understood.',
        'What do you think?',
        'Let\'s talk about it.',
      ],
      ttsLang: 'en',
      ttsMood: 'casual',
    };
  },

  _generateAccent: function(name) {
    var hash = 0;
    for (var i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
      hash = hash & hash; // Convert to 32bit int
    }
    var h = Math.abs(hash);
    var r = (h & 0xFF0000) >> 16;
    var g = (h & 0x00FF00) >> 8;
    var b = h & 0x0000FF;
    // Soften the color
    r = Math.floor(r * 0.7 + 80);
    g = Math.floor(g * 0.5 + 90);
    b = Math.floor(b * 0.6 + 80);
    return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
  },

  // Main import from file
  importFile: function(file) {
    var self = this;
    return new Promise(function(resolve, reject) {
      var reader = new FileReader();

      reader.onload = function(e) {
        try {
          var buffer = e.target.result;
          var charaCard;

          if (file.name.toLowerCase().endsWith('.json')) {
            // Plain JSON character card
            var text = '';
            var view = new Uint8Array(buffer);
            for (var i = 0; i < view.length; i++) {
              text += String.fromCharCode(view[i]);
            }
            charaCard = JSON.parse(text);
          } else if (file.name.toLowerCase().endsWith('.png')) {
            charaCard = self.parsePNG(buffer);
          } else {
            throw new Error('Unsupported file type. Use .png or .json character cards.');
          }

          if (!charaCard) {
            throw new Error('No character data found in file.');
          }

          var char = self.convert(charaCard);
          resolve(char);
        } catch (err) {
          reject(err);
        }
      };

      reader.onerror = function() {
        reject(new Error('Failed to read file'));
      };

      reader.readAsArrayBuffer(file);
    });
  },

  // Add imported character to global CHARACTERS
  addCharacter: function(char) {
    // Check for duplicate
    for (var i = 0; i < CHARACTERS.length; i++) {
      if (CHARACTERS[i].id === char.id) {
        return false; // already exists
      }
    }
    CHARACTERS.push(char);
    this._saveImported();
    return true;
  },

  // Save imported characters to localStorage
  _saveImported: function() {
    var imported = CHARACTERS.filter(function(c) { return c.imported; });
    // Strip rawCard before saving (too large)
    var clean = imported.map(function(c) {
      var clone = {};
      for (var k in c) {
        if (k !== 'rawCard') clone[k] = c[k];
      }
      return clone;
    });
    try {
      localStorage.setItem('ai-gf-imported-chars', JSON.stringify(clean));
    } catch (e) {
      // localStorage full - keep only essentials
      var minimal = imported.map(function(c) {
        return { id: c.id, name: c.name, icon: c.icon, persona: c.persona, accent: c.accent, imported: true };
      });
      localStorage.setItem('ai-gf-imported-chars', JSON.stringify(minimal));
    }
  },

  // Load imported characters from localStorage
  loadImported: function() {
    try {
      var raw = localStorage.getItem('ai-gf-imported-chars');
      if (!raw) return;
      var chars = JSON.parse(raw);
      var self = this;
      chars.forEach(function(c) {
        c.imported = true;
        // Don't add duplicates
        if (!CHARACTERS.find(function(ex) { return ex.id === c.id; })) {
          // Ensure fallbackReplies
          if (!c.fallbackReplies) {
            c.fallbackReplies = ['I\'m here.', 'Tell me more.', 'I see...', 'Mm.', 'What do you think?'];
          }
          if (!c.tags) c.tags = ['Imported'];
          if (!c.source) c.source = 'Imported character';
          if (!c.ttsLang) c.ttsLang = 'en';
          if (!c.ttsMood) c.ttsMood = 'casual';
          CHARACTERS.push(c);
        }
      });
    } catch (e) {
      console.warn('Failed to load imported characters:', e.message);
    }
  },

  // Remove imported character
  removeCharacter: function(id) {
    var idx = -1;
    for (var i = 0; i < CHARACTERS.length; i++) {
      if (CHARACTERS[i].id === id && CHARACTERS[i].imported) {
        idx = i;
        break;
      }
    }
    if (idx >= 0) {
      CHARACTERS.splice(idx, 1);
      this._saveImported();
      return true;
    }
    return false;
  },

  // Init - load saved imports, set up + button
  init: function() {
    this.loadImported();

    var self = this;
    var fileInput = document.getElementById('import-char-file');
    if (!fileInput) return;

    fileInput.addEventListener('change', function() {
      var file = fileInput.files[0];
      if (!file) return;

      self.importFile(file).then(function(char) {
        var added = self.addCharacter(char);
        if (added) {
          UI.showToast('Imported: ' + char.name, 'success');
          UI.rebuildCharList();
          // Switch to the new character
          UI.selectCharacter(char.id);
        } else {
          UI.showToast(char.name + ' already imported', 'warning');
        }
      }).catch(function(err) {
        UI.showToast('Import failed: ' + err.message, 'error');
      });
      // Reset input
      fileInput.value = '';
    });

    // Make sure rebuildCharList includes the + button
  },
};
