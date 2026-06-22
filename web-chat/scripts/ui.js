// ============================================================
// ui.js - Chat UI controller with multi-session support
// ============================================================

var UI = {
  $messages: null,
  $input: null,
  $sendBtn: null,
  $statusInd: null,
  $statusLabel: null,
  $charName: null,
  $charSubtitle: null,
  state: {
    messages: [],
    streaming: false,
    currentCharId: DEFAULT_CHAR_ID,
    currentSessionId: null,
  },

  init: function() {
    var self = this;
    this.$messages = document.getElementById('messages');
    this.$input = document.getElementById('msg-input');
    this.$sendBtn = document.getElementById('send-btn');
    this.$statusLabel = document.getElementById('status-label');
    this.$charName = document.getElementById('char-name-text');
    this.$charSubtitle = document.getElementById('char-subtitle-text');

    // CHARACTERS already loaded with fallback via chars.js IIFE boot.
    // UI renders immediately; API refresh happens asynchronously.
    CharacterImporter.init();
    this.state.currentCharId = getActiveCharId();
    this.state.currentSessionId = ensureDefaultSession(this.state.currentCharId);
    this.loadCharUI();
    this.loadSessionsList();
    this.loadHistory();
    this.setupEvents();
    this.checkGateway();
    this.$input.focus();

    // When API characters arrive, refresh the UI
    if (CHAR_API_PROMISE) {
      CHAR_API_PROMISE.then(function () {
        self.loadCharUI();
        self.rebuildCharList();
        self.loadSessionsList();
      }).catch(function (err) {
        console.warn('API character refresh failed:', err.message);
      });
    }
  },

  setupEvents: function() {
    var self = this;
    this.$sendBtn.addEventListener('click', function() { self.sendMessage(); });
    this.$input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); self.sendMessage(); }
    });
    this.$input.addEventListener('input', function() { self.autoResize(); });

    document.getElementById('btn-reset').addEventListener('click', function() { self.resetSession(); });
    document.getElementById('btn-clear').addEventListener('click', function() { self.clearMessages(); });
    document.getElementById('btn-search').addEventListener('click', function() { self.toggleSearch(); });
    document.getElementById('btn-settings').addEventListener('click', function() { self.openSettings(); });
    document.getElementById('mobile-sidebar-toggle').addEventListener('click', function() {
      document.getElementById('sidebar').classList.toggle('mobile-open');
    });

    // Skill buttons
    document.getElementById('btn-live2d').addEventListener('click', function() { showToast('Live2D - action triggered'); });

    // New chat button in sessions list
    document.getElementById('btn-new-chat').addEventListener('click', function() { self.createSession(); });

    // Character selector
    this.initCharSelector();
    this.initSettingsPanel();
    this.initSearch();
  },

  // ---- Character UI ----
  rebuildCharList: function() {
    var self = this;
    var list = document.getElementById('char-dropdown-list');
    if (!list) return;
    var activeId = this.state.currentCharId;
    list.innerHTML = CHARACTERS.map(function(c) {
      var activeClass = c.id === activeId ? ' active' : '';
      return '<div class="char-option' + activeClass + '" data-char-id="' + c.id + '"><div class="char-option-avatar">' + c.icon.toUpperCase() + '</div><span>' + c.name + '</span></div>';
    }).join('');
    document.querySelectorAll('.char-option').forEach(function(opt) {
      opt.addEventListener('click', function() {
        var id = opt.dataset.charId;
        document.getElementById('char-dropdown').classList.remove('open');
        document.getElementById('char-select-btn').classList.remove('open');
        if (id !== self.state.currentCharId) {
          self.switchChar(id);
        }
      });
    });
  },

  selectCharacter: function(id) {
    if (this.state.currentCharId === id) return;
    this.state.currentCharId = id;
    this.state.currentSessionId = ensureDefaultSession(id);
    setActiveCharId(id);
    this.loadCharUI();
    this.loadSessionsList();
    this.loadHistory();
    this.checkGateway();
  },

  loadCharUI: function() {
    var c = getChar(this.state.currentCharId);
    if (!c) {
      console.warn('No character found for id:', this.state.currentCharId);
      return;
    }
    if (this.$charName) this.$charName.textContent = c.name;
    if (this.$charSubtitle) this.$charSubtitle.textContent = c.nameEn;
    var avatarIcon = document.getElementById('char-avatar-icon');
    if (avatarIcon) avatarIcon.textContent = c.icon.toUpperCase();
    var persona = document.getElementById('char-persona');
    if (persona) persona.textContent = c.persona;
    var personaNote = document.getElementById('char-persona-note');
    if (personaNote) personaNote.textContent = c.personaNote;
    var source = document.getElementById('char-source');
    if (source) source.textContent = c.source;

    var tagsEl = document.getElementById('char-tags');
    if (tagsEl) tagsEl.innerHTML = (c.tags || []).map(function(t) { return '<span class="tag">' + t + '</span>'; }).join('');
    var sidebarName = document.getElementById('sidebar-char-name');
    if (sidebarName) sidebarName.textContent = c.name;

    // Active in dropdown
    var self = this;
    document.querySelectorAll('.char-option').forEach(function(el) {
      el.classList.toggle('active', el.dataset.charId === self.state.currentCharId);
    });
  },

  initCharSelector: function() {
    var self = this;
    var btn = document.getElementById('char-select-btn');
    var dropdown = document.getElementById('char-dropdown');
    var list = document.getElementById('char-dropdown-list');
    if (!btn || !dropdown || !list) return;

    list.innerHTML = CHARACTERS.map(function(c) {
      return '<div class="char-option" data-char-id="' + c.id + '"><div class="char-option-avatar">' + c.icon.toUpperCase() + '</div><span>' + c.name + '</span></div>';
    }).join('');

    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      var wasOpen = dropdown.classList.contains('open');
      dropdown.classList.toggle('open', !wasOpen);
      btn.classList.toggle('open', !wasOpen);
    });

    document.addEventListener('click', function() {
      dropdown.classList.remove('open');
      btn.classList.remove('open');
    });

    list.addEventListener('click', function(e) {
      var opt = e.target.closest('.char-option');
      if (!opt) return;
      var charId = opt.dataset.charId;
      if (charId && charId !== self.state.currentCharId) {
        self.switchChar(charId);
      }
      dropdown.classList.remove('open');
      btn.classList.remove('open');
    });
  },

  switchChar: function(charId) {
    // Save current
    saveChatHistory(this.state.currentCharId, this.state.currentSessionId, this.state.messages);

    this.state.currentCharId = charId;
    setActiveCharId(charId);
    this.state.currentSessionId = ensureDefaultSession(charId);
    this.loadCharUI();
    this.loadSessionsList();
    this.loadHistory();
    showToast('Switched to ' + getChar(charId).name);
  },

  // ---- Session management ----
  loadSessionsList: function() {
    var self = this;
    var list = document.getElementById('sessions-list');
    if (!list) return;
    var sessions = getSessions(this.state.currentCharId);
    var activeId = getActiveSessionId(this.state.currentCharId);

    list.innerHTML = sessions.map(function(s) {
      var active = s.id === activeId ? ' active' : '';
      var count = s.count > 0 ? '<span class="session-msg-count">' + s.count + '</span>' : '';
      return '<div class="session-item' + active + '" data-sid="' + s.id + '">' +
        '<span class="session-name">' + escapeHtml(s.name) + '</span>' + count +
        '<span class="session-actions">' +
          '<i class="ph ph-pencil-simple session-rename" data-sid="' + s.id + '" title="Rename"></i>' +
          '<i class="ph ph-trash session-delete" data-sid="' + s.id + '" title="Delete"></i>' +
        '</span>' +
      '</div>';
    }).join('');

    // Click to switch session
    list.querySelectorAll('.session-item').forEach(function(el) {
      el.addEventListener('click', function(e) {
        // Don't switch if clicking rename/delete
        if (e.target.closest('.session-rename') || e.target.closest('.session-delete')) return;
        var sid = el.dataset.sid;
        if (sid && sid !== self.state.currentSessionId) {
          self.switchSession(sid);
        }
      });
    });

    // Rename
    list.querySelectorAll('.session-rename').forEach(function(icon) {
      icon.addEventListener('click', function(e) {
        e.stopPropagation();
        var sid = icon.dataset.sid;
        self.renameSessionPrompt(sid);
      });
    });

    // Delete
    list.querySelectorAll('.session-delete').forEach(function(icon) {
      icon.addEventListener('click', function(e) {
        e.stopPropagation();
        var sid = icon.dataset.sid;
        self.deleteSessionPrompt(sid);
      });
    });
  },

  switchSession: function(sessionId) {
    saveChatHistory(this.state.currentCharId, this.state.currentSessionId, this.state.messages);
    this.state.currentSessionId = sessionId;
    setActiveSession(this.state.currentCharId, sessionId);
    this.loadHistory();
    this.loadSessionsList();
  },

  createSession: function() {
    var num = getSessions(this.state.currentCharId).length + 1;
    var sid = createSession(this.state.currentCharId, 'Chat ' + num);
    saveChatHistory(this.state.currentCharId, this.state.currentSessionId, this.state.messages);
    this.state.currentSessionId = sid;
    setActiveSession(this.state.currentCharId, sid);
    this.loadHistory();
    this.loadSessionsList();
    showToast('New chat created');
  },

  renameSessionPrompt: function(sid) {
    var name = prompt('Rename chat:');
    if (name && name.trim()) {
      renameSession(this.state.currentCharId, sid, name.trim());
      this.loadSessionsList();
    }
  },

  deleteSessionPrompt: function(sid) {
    var sessions = getSessions(this.state.currentCharId);
    if (sessions.length <= 1) {
      showToast('Cannot delete the last chat');
      return;
    }
    if (confirm('Delete this chat permanently?')) {
      deleteSession(this.state.currentCharId, sid);
      this.state.currentSessionId = getActiveSessionId(this.state.currentCharId);
      this.loadHistory();
      this.loadSessionsList();
      showToast('Chat deleted');
    }
  },

  // ---- Message rendering ----
  renderMessage: function(msg, index) {
    var isUser = msg.role === 'user';
    var isSystem = msg.role === 'system';
    var time = msg.time || this.formatTime(new Date());
    var self = this;

    if (isSystem) {
      var el = document.createElement('div');
      el.className = 'msg-system';
      el.textContent = msg.content;
      el.dataset.msgIndex = index;
      return el;
    }

    var row = document.createElement('div');
    row.className = 'msg-row ' + (isUser ? 'user' : 'char');
    row.dataset.msgIndex = index;

    var avatar = document.createElement('div');
    avatar.className = 'msg-avatar ' + (isUser ? 'user' : 'char');
    avatar.innerHTML = isUser ? '<i class="ph ph-user"></i>' : '<i class="ph ph-heart"></i>';

    var contentWrap = document.createElement('div');
    var bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.textContent = msg.content;

    // Media
    if (msg.media) {
      if (msg.mediaType === 'audio' || /\.(wav|mp3|ogg)$/.test(msg.media)) {
        var audio = document.createElement('audio');
        audio.className = 'msg-media audio-player';
        audio.controls = true;
        audio.src = msg.media;
        bubble.appendChild(audio);
      } else {
        var img = document.createElement('img');
        img.className = 'msg-media';
        img.src = msg.media;
        img.loading = 'lazy';
        img.addEventListener('click', function() { window.open(msg.media, '_blank'); });
        bubble.appendChild(img);
      }
    }

    var timeEl = document.createElement('div');
    timeEl.className = 'msg-time';
    timeEl.textContent = time;

    contentWrap.appendChild(bubble);
    contentWrap.appendChild(timeEl);
    row.appendChild(avatar);
    row.appendChild(contentWrap);

    return row;
  },

  appendMessage: function(msg) {
    var el = this.renderMessage(msg, this.state.messages.length);
    this.$messages.appendChild(el);
    this.scrollToBottom();
  },

  scrollToBottom: function() {
    var self = this;
    requestAnimationFrame(function() {
      if (self.$messages) self.$messages.scrollTop = self.$messages.scrollHeight;
    });
  },

  // ---- Typing ----
  showTyping: function() {
    var row = document.createElement('div');
    row.className = 'msg-row char';
    row.id = 'typing-indicator';
    var avatar = document.createElement('div');
    avatar.className = 'msg-avatar char';
    avatar.innerHTML = '<i class="ph ph-heart"></i>';
    var bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.style.padding = '14px 20px';
    var dots = document.createElement('div');
    dots.className = 'typing-dots';
    dots.innerHTML = '<span></span><span></span><span></span>';
    bubble.appendChild(dots);
    row.appendChild(avatar);
    row.appendChild(bubble);
    this.$messages.appendChild(row);
    this.scrollToBottom();
  },

  hideTyping: function() {
    var el = document.getElementById('typing-indicator');
    if (el) el.remove();
  },

  // ---- Streaming ----
  createStreamBubble: function() {
    var row = document.createElement('div');
    row.className = 'msg-row char';
    row.id = 'stream-bubble';
    var avatar = document.createElement('div');
    avatar.className = 'msg-avatar char';
    avatar.innerHTML = '<i class="ph ph-heart"></i>';
    var bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.id = 'stream-bubble-text';
    var cursor = document.createElement('span');
    cursor.className = 'stream-cursor';
    bubble.appendChild(cursor);
    row.appendChild(avatar);
    row.appendChild(bubble);
    this.$messages.appendChild(row);
    this.scrollToBottom();
  },

  appendStreamToken: function(text) {
    var bubble = document.getElementById('stream-bubble-text');
    if (!bubble) return;
    var cursor = bubble.querySelector('.stream-cursor');
    if (cursor) {
      cursor.before(document.createTextNode(text));
    } else {
      bubble.appendChild(document.createTextNode(text));
    }
    this.scrollToBottom();
  },

  finalizeStream: function(text) {
    var bubble = document.getElementById('stream-bubble-text');
    if (!bubble) return;
    var cursor = bubble.querySelector('.stream-cursor');
    if (cursor) cursor.remove();
  },

  // ---- Send ----
  sendMessage: function() {
    var self = this;
    var content = this.$input.value.trim();
    if (!content || this.state.streaming) return;

    this.$input.value = '';
    this.autoResize();

    var userMsg = { role: 'user', content: content, time: this.formatTime(new Date()) };
    this.appendMessage(userMsg);
    this.state.messages.push(userMsg);

    this.showTyping();
    this.state.streaming = true;
    this.$sendBtn.disabled = true;

    var settings = getSettings();

    ApiClient.checkStatus().then(function(online) {
      if (online && settings.streamEnabled) {
        self.hideTyping();
        self.createStreamBubble();

        ApiClient.chatStream(
          self.state.messages,
          settings,
          function(token) { self.appendStreamToken(token); },
          function(result) {
            self.finalizeStream(result.text);
            var charMsg = { role: 'assistant', content: result.text, time: self.formatTime(new Date()) };
            if (result.media) charMsg.media = result.media;
            self.state.messages.push(charMsg);
            saveChatHistory(self.state.currentCharId, self.state.currentSessionId, self.state.messages);
            self.state.streaming = false;
            self.$sendBtn.disabled = false;
            self.$input.focus();
          },
          function(err) {
            console.warn('Stream failed:', err.message);
            self.finalizeStream('');
            var bubble = document.getElementById('stream-bubble');
            if (bubble) bubble.remove();
            self.doFallback();
            saveChatHistory(self.state.currentCharId, self.state.currentSessionId, self.state.messages);
            self.state.streaming = false;
            self.$sendBtn.disabled = false;
            self.$input.focus();
          }
        );
      } else {
        self.doNonStream(online);
      }
    });
  },

  doNonStream: function(online) {
    var self = this;
    if (online) {
      var settings = getSettings();
      fetch((settings.apiBase || '') + '/api/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: settings.model || 'local-model',
          messages: this.state.messages,
          stream: false,
          max_tokens: 4096,
        }),
        signal: AbortSignal.timeout(30000),
      }).then(function(res) {
        return res.json();
      }).then(function(data) {
        self.hideTyping();
        var reply = (data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content) || '';
        var charMsg = { role: 'assistant', content: reply, time: self.formatTime(new Date()) };
        self.appendMessage(charMsg);
        self.state.messages.push(charMsg);
      }).catch(function() {
        self.hideTyping();
        self.doFallback();
      }).finally(function() {
        saveChatHistory(self.state.currentCharId, self.state.currentSessionId, self.state.messages);
        self.state.streaming = false;
        self.$sendBtn.disabled = false;
        self.$input.focus();
      });
    } else {
      this.hideTyping();
      this.doFallback();
      saveChatHistory(this.state.currentCharId, this.state.currentSessionId, self.state.messages);
      this.state.streaming = false;
      this.$sendBtn.disabled = false;
      this.$input.focus();
    }
  },

  doFallback: function() {
    var reply = getFallbackReply(this.state.currentCharId);
    var charMsg = { role: 'assistant', content: reply, time: this.formatTime(new Date()) };
    this.appendMessage(charMsg);
    this.state.messages.push(charMsg);
  },

  // ---- History ----
  loadHistory: function() {
    if (!this.$messages) return;
    this.$messages.innerHTML = '';
    var msgs = getChatHistory(this.state.currentCharId, this.state.currentSessionId);
    this.state.messages = msgs.slice();
    var self = this;
    if (msgs.length === 0) {
      this.appendSystemMsg('Chat started - ' + this.formatDate(new Date()));
    } else {
      this.appendSystemMsg('Resumed (' + msgs.length + ' messages) - ' + this.formatDate(new Date()));
      msgs.forEach(function(m, i) {
        var el = self.renderMessage(m, i);
        self.$messages.appendChild(el);
      });
    }
    this.scrollToBottom();
  },

  appendSystemMsg: function(text) {
    var el = document.createElement('div');
    el.className = 'msg-system';
    el.textContent = text;
    if (this.$messages) this.$messages.appendChild(el);
  },

  // ---- Session reset ----
  resetSession: function() {
    if (this.state.messages.length === 0) return;
    this.state.messages = [];
    saveChatHistory(this.state.currentCharId, this.state.currentSessionId, []);
    this.$messages.innerHTML = '';
    this.appendSystemMsg('Session reset - ' + this.formatTime(new Date()));
    showToast('Session reset');
    this.loadSessionsList();
  },

  clearMessages: function() {
    this.state.messages = [];
    this.$messages.innerHTML = '';
    saveChatHistory(this.state.currentCharId, this.state.currentSessionId, []);
    this.appendSystemMsg('Cleared - ' + this.formatTime(new Date()));
    showToast('Messages cleared');
    this.loadSessionsList();
  },

  // ---- Search ----
  initSearch: function() {
    var self = this;
    var searchRow = document.getElementById('search-row');
    var searchInput = document.getElementById('search-input');
    if (!searchRow || !searchInput) return;

    searchInput.addEventListener('input', function() {
      var query = searchInput.value.toLowerCase();
      var bubbles = self.$messages.querySelectorAll('.msg-row, .msg-system');
      var count = 0;
      bubbles.forEach(function(el) {
        if (!query || el.textContent.toLowerCase().indexOf(query) !== -1) {
          el.style.display = '';
          count++;
        } else {
          el.style.display = 'none';
        }
      });
      var countEl = document.getElementById('search-count');
      if (countEl) countEl.textContent = query ? count + ' found' : '';
    });

    searchInput.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        searchInput.value = '';
        self.toggleSearch();
        self.$input.focus();
      }
    });
  },

  toggleSearch: function() {
    var searchRow = document.getElementById('search-row');
    if (!searchRow) return;
    var visible = searchRow.style.display !== 'none';
    searchRow.style.display = visible ? 'none' : 'flex';
    if (!visible) {
      var searchInput = document.getElementById('search-input');
      if (searchInput) searchInput.focus();
    } else {
      var si = document.getElementById('search-input');
      if (si) si.value = '';
      if (this.$messages) {
        this.$messages.querySelectorAll('.msg-row, .msg-system').forEach(function(el) { el.style.display = ''; });
      }
      var countEl = document.getElementById('search-count');
      if (countEl) countEl.textContent = '';
    }
  },

  // ---- Settings ----
  initSettingsPanel: function() {
    var saveBtn = document.getElementById('settings-save');
    var cancelBtn = document.getElementById('settings-cancel');
    var overlay = document.getElementById('settings-overlay');
    var streamCheckbox = document.getElementById('setting-stream');
    var streamToggle = document.getElementById('toggle-stream-switch');

    if (saveBtn) saveBtn.addEventListener('click', function() {
      var s = getSettings();
      s.apiBase = document.getElementById('setting-api-base').value.trim();
      s.bridgeUrl = document.getElementById('setting-bridge-url').value.trim() || 'http://localhost:19250';
      s.model = document.getElementById('setting-model').value.trim() || 'local-model';
      s.streamEnabled = document.getElementById('setting-stream').checked;
      saveSettings(s);
      ApiClient.init(s.apiBase);
      Studio.bridgeUrl = s.bridgeUrl;
      overlay.classList.remove('open');
      showToast('Settings saved');
      UI.checkGateway();
    });

    if (cancelBtn) cancelBtn.addEventListener('click', function() {
      overlay.classList.remove('open');
    });

    if (streamCheckbox && streamToggle) streamCheckbox.addEventListener('change', function(e) {
      streamToggle.classList.toggle('on', e.target.checked);
    });

    if (overlay) overlay.addEventListener('click', function(e) {
      if (e.target.id === 'settings-overlay') {
        overlay.classList.remove('open');
      }
    });
  },

  openSettings: function() {
    var s = getSettings();
    var apiBase = document.getElementById('setting-api-base');
    var bridgeUrl = document.getElementById('setting-bridge-url');
    var model = document.getElementById('setting-model');
    var streamCheckbox = document.getElementById('setting-stream');
    var streamToggle = document.getElementById('toggle-stream-switch');
    var overlay = document.getElementById('settings-overlay');

    if (apiBase) apiBase.value = s.apiBase || '';
    if (bridgeUrl) bridgeUrl.value = s.bridgeUrl || 'http://localhost:19250';
    if (model) model.value = s.model || 'local-model';
    if (streamCheckbox) streamCheckbox.checked = s.streamEnabled !== false;
    if (streamToggle) streamToggle.classList.toggle('on', s.streamEnabled !== false);
    if (overlay) overlay.classList.add('open');
  },

  // ---- Gateway ----
  checkGateway: function() {
    var self = this;
    // Use daemon API to check gateway status (avoids CORS noise on webchat port)
    fetch('http://localhost:19260/api/status', { signal: AbortSignal.timeout(3000) })
      .then(function(r) { return r.json(); })
      .then(function(services) {
        var gw = (Array.isArray(services) ? services : []).find(function(s) { return s.name === 'OpenClaw Gateway'; });
        if (self.$statusLabel) {
          self.$statusLabel.textContent = (gw && gw.online) ? 'Online' : 'Offline';
        }
      })
      .catch(function() {
        if (self.$statusLabel) self.$statusLabel.textContent = 'Offline';
      });
  },

  // ---- Helpers ----
  autoResize: function() {
    this.$input.style.height = 'auto';
    this.$input.style.height = Math.min(this.$input.scrollHeight, 160) + 'px';
  },

  formatTime: function(date) {
    return String(date.getHours()).padStart(2, '0') + ':' + String(date.getMinutes()).padStart(2, '0');
  },

  formatDate: function(date) {
    return date.getFullYear() + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      String(date.getDate()).padStart(2, '0');
  },
};

// ---- Toast ----
function showToast(text) {
  var container = document.getElementById('toast-container');
  if (!container) return;
  var t = document.createElement('div');
  t.className = 'toast';
  t.textContent = text;
  container.appendChild(t);
  setTimeout(function() { t.remove(); }, 2500);
}

function escapeHtml(str) {
  var d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

// ---- Boot ----
document.addEventListener('DOMContentLoaded', function() {
  var s = getSettings();
  ApiClient.init(s.apiBase);
  Studio.bridgeUrl = s.bridgeUrl || 'http://localhost:19250';
  Studio.init();
  UI.init();
});
