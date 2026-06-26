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

    // Setup scroll detection early (before any messages load)
    this._setupScrollDetection();

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
    document.getElementById('btn-auto-paint').addEventListener('click', function() { self.autoPaint(); });
    document.getElementById('btn-manual-paint').addEventListener('click', function() { self.manualPaint(); });

    // Llama management toggle in chat input area
    var llamaToggleLabel = document.getElementById('toggle-chat-llama-label');
    var llamaToggleCheck = document.getElementById('chat-manage-llama');
    var llamaToggleSwitch = document.getElementById('toggle-chat-llama-switch');
    llamaToggleLabel.addEventListener('click', function() {
      llamaToggleCheck.checked = !llamaToggleCheck.checked;
      if (llamaToggleCheck.checked) {
        llamaToggleSwitch.classList.add('on');
      } else {
        llamaToggleSwitch.classList.remove('on');
      }
    });

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
      var deleteBtn = c.imported ? '<i class="ph ph-x char-delete-btn" data-char-id="' + c.id + '" title="Delete ' + c.name + '"></i>' : '';
      return '<div class="char-option' + activeClass + '" data-char-id="' + c.id + '"><div class="char-option-avatar">' + c.icon.toUpperCase() + '</div><span>' + c.name + '</span>' + deleteBtn + '</div>';
    }).join('') + '<div class="char-option char-import-option" id="char-import-option"><div class="char-option-avatar" style="background:var(--accent);color:#fff"><i class="ph ph-plus"></i></div><span>Import character...</span></div>';

    // Click delegation — handle char selection and delete
    list.onclick = function(e) {
      var delBtn = e.target.closest('.char-delete-btn');
      if (delBtn) {
        e.stopPropagation();
        var id = delBtn.dataset.charId;
        if (confirm('Delete "' + (getChar(id) || {}).name + '" permanently?')) {
          if (CharacterImporter.removeCharacter(id)) {
            if (self.state.currentCharId === id) {
              // Switch to first available character
              self.selectCharacter(CHARACTERS[0].id);
            } else {
              self.rebuildCharList();
            }
            UI.showToast('Character deleted', 'success');
          }
        }
        return;
      }

      var opt = e.target.closest('.char-option');
      if (!opt) return;

      if (opt.id === 'char-import-option' || opt.classList.contains('char-import-option')) {
        var fileInput = document.getElementById('import-char-file');
        if (fileInput) fileInput.click();
        return;
      }

      var charId = opt.dataset.charId;
      document.getElementById('char-dropdown').classList.remove('open');
      document.getElementById('char-select-btn').classList.remove('open');
      if (charId && charId !== self.state.currentCharId) {
        self.switchChar(charId);
      }
    };
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
      var deleteBtn = c.imported ? '<i class="ph ph-x char-delete-btn" data-char-id="' + c.id + '" title="Delete ' + c.name + '"></i>' : '';
      return '<div class="char-option" data-char-id="' + c.id + '"><div class="char-option-avatar">' + c.icon.toUpperCase() + '</div><span>' + c.name + '</span>' + deleteBtn + '</div>';
    }).join('') + '<div class="char-option char-import-option" id="char-import-option"><div class="char-option-avatar" style="background:var(--accent);color:#fff"><i class="ph ph-plus"></i></div><span>Import character...</span></div>';

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

    // Sidebar + import button (outside dropdown)
    var importBtn = document.getElementById('btn-import-char');
    if (importBtn) {
      importBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        var fileInput = document.getElementById('import-char-file');
        if (fileInput) fileInput.click();
      });
    }

    list.addEventListener('click', function(e) {
      // Delete button already handled by rebuildCharList's onclick
      if (e.target.closest('.char-delete-btn')) return;

      var opt = e.target.closest('.char-option');
      if (!opt) return;

      // Import option
      if (opt.id === 'char-import-option' || opt.classList.contains('char-import-option')) {
        e.stopPropagation();
        dropdown.classList.remove('open');
        btn.classList.remove('open');
        var fileInput = document.getElementById('import-char-file');
        if (fileInput) fileInput.click();
        return;
      }

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

    // Collapse long historical messages
    if (!isUser && msg.content && msg.content.length > this.LONG_MSG_THRESHOLD) {
      bubble.classList.add('long-collapsed');
    }

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

    // Add collapse toggle for long messages
    if (!isUser && msg.content && msg.content.length > this.LONG_MSG_THRESHOLD) {
      var btn = document.createElement('button');
      btn.className = 'msg-collapse-btn';
      btn.textContent = 'Show full message (' + Math.round(msg.content.length / 1000) + 'k chars)';
      btn.addEventListener('click', function() {
        if (bubble.classList.contains('long-collapsed')) {
          bubble.classList.remove('long-collapsed');
          btn.textContent = 'Collapse';
        } else {
          bubble.classList.add('long-collapsed');
          btn.textContent = 'Show full message (' + Math.round(msg.content.length / 1000) + 'k chars)';
        }
      });
      row.appendChild(btn);
    }

    return row;
  },

  appendMessage: function(msg) {
    var el = this.renderMessage(msg, this.state.messages.length);
    this.$messages.appendChild(el);
    this._userScrolledUp = false;
    this.scrollToBottom(true);
  },

  scrollToBottom: function(force) {
    var self = this;
    // If user scrolled up manually, don't force them back down
    if (!force && this._userScrolledUp) return;
    // Double-RAF to ensure DOM layout is complete (esp. after collapse/expand)
    requestAnimationFrame(function() {
      requestAnimationFrame(function() {
        if (self.$messages) {
          self.$messages.scrollTop = self.$messages.scrollHeight;
        }
      });
    });
  },

  _isNearBottom: function() {
    if (!this.$messages) return true;
    var el = this.$messages;
    return el.scrollHeight - el.scrollTop - el.clientHeight < 80;
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
    this._userScrolledUp = false;
    this.scrollToBottom(true);
  },

  hideTyping: function() {
    var el = document.getElementById('typing-indicator');
    if (el) el.remove();
  },

  // ---- Streaming ----
  createStreamBubble: function() {
    // Remove any stale stream-bubble from previous reply
    var old = document.getElementById('stream-bubble');
    if (old) { old.removeAttribute('id'); old.querySelector('#stream-bubble-text')?.removeAttribute('id'); }

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

    // Reset scroll state on new message
    this._userScrolledUp = false;
    this._lastScrollTs = 0;
    this._streamTokenCount = 0;
    this.scrollToBottom(true);
  },

  _setupScrollDetection: function() {
    var self = this;
    if (this._scrollDetectorSet) return;
    this._scrollDetectorSet = true;

    var onScroll = function() {
      if (self.$messages.scrollTop < self.$messages.scrollHeight - self.$messages.clientHeight - 60) {
        self._userScrolledUp = true;
      } else {
        self._userScrolledUp = false;
      }
    };

    // Cover all scroll interaction types
    this.$messages.addEventListener('wheel', onScroll, { passive: true });
    this.$messages.addEventListener('touchmove', onScroll, { passive: true });
    this.$messages.addEventListener('scroll', onScroll, { passive: true });
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
    this._streamTokenCount++;

    // Throttle scroll: every 3rd token or every 50ms
    var now = Date.now();
    if (this._streamTokenCount % 3 === 0 || now - this._lastScrollTs > 50) {
      this._lastScrollTs = now;
      this.scrollToBottom(false);
    }
  },

  finalizeStream: function(text) {
    var bubble = document.getElementById('stream-bubble-text');
    if (!bubble) return;
    var cursor = bubble.querySelector('.stream-cursor');
    if (cursor) cursor.remove();

    // Extract and inject MEDIA: image if present
    var parsed = this._parseMediaFromText(text);
    if (parsed.mediaPath) {
      var img = document.createElement('img');
      img.className = 'msg-media';
      img.src = this._resolveMediaPath(parsed.mediaPath);
      img.loading = 'lazy';
      img.addEventListener('click', function() { window.open(img.src, '_blank'); });
      bubble.appendChild(img);
      // Replace text content with cleaned version (strips MEDIA: line)
      bubble.textContent = parsed.cleanText || '';
    }

    // Collapse long messages
    var displayText = parsed.cleanText || text;
    this._autoCollapseLong(bubble, displayText);

    this._userScrolledUp = false;
    this.scrollToBottom(true);
  },

  // ---- Long message auto-collapse ----
  LONG_MSG_THRESHOLD: 2000, // characters

  _autoCollapseLong: function(bubble, text) {
    if (!bubble || text.length < this.LONG_MSG_THRESHOLD) return;

    // Get the row container
    var row = bubble.closest('.msg-row');
    if (!row) return;

    // Check if collapse button already exists
    if (row.querySelector('.msg-collapse-btn')) return;

    bubble.classList.add('long-collapsed');

    var btn = document.createElement('button');
    btn.className = 'msg-collapse-btn';
    btn.textContent = 'Show full message (' + Math.round(text.length / 1000) + 'k chars)';
    btn.addEventListener('click', function() {
      if (bubble.classList.contains('long-collapsed')) {
        bubble.classList.remove('long-collapsed');
        btn.textContent = 'Collapse';
      } else {
        bubble.classList.add('long-collapsed');
        btn.textContent = 'Show full message (' + Math.round(text.length / 1000) + 'k chars)';
      }
    });
    row.appendChild(btn);
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
    settings.characterId = self.state.currentCharId || 'natsume';
    // Pass custom system prompt for imported characters
    var currentChar = getChar(self.state.currentCharId);
    if (currentChar && currentChar.imported && currentChar.systemPrompt) {
      settings.systemPrompt = currentChar.systemPrompt;
    }

    // Always try API (daemon proxy). Fallback if it fails.
    if (settings.streamEnabled !== false) {
      self.hideTyping();
      self.createStreamBubble();

      ApiClient.chatStream(
        self.state.messages,
        settings,
        function(token) { self.appendStreamToken(token); },
        function(result) {
          self.finalizeStream(result.text);
          var parsed = self._parseMediaFromText(result.text);
          var cleanText = parsed.cleanText;
          var charMsg = { role: 'assistant', content: cleanText, time: self.formatTime(new Date()) };
          if (result.media) charMsg.media = result.media;
          else if (parsed.mediaPath) charMsg.media = self._resolveMediaPath(parsed.mediaPath);
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
      ApiClient.nonStreamChat(self.state.messages, settings).then(function(reply) {
        self.hideTyping();
        var parsed = self._parseMediaFromText(reply);
        var charMsg = { role: 'assistant', content: parsed.cleanText, time: self.formatTime(new Date()) };
        if (parsed.mediaPath) charMsg.media = self._resolveMediaPath(parsed.mediaPath);
        self.appendMessage(charMsg);
        self.state.messages.push(charMsg);
        saveChatHistory(self.state.currentCharId, self.state.currentSessionId, self.state.messages);
        self.state.streaming = false;
        self.$sendBtn.disabled = false;
        self.$input.focus();
      }).catch(function(err) {
        console.warn('Non-stream failed:', err.message);
        self.hideTyping();
        self.doFallback();
        saveChatHistory(self.state.currentCharId, self.state.currentSessionId, self.state.messages);
        self.state.streaming = false;
        self.$sendBtn.disabled = false;
        self.$input.focus();
      });
    }
  },

  doFallback: function() {
    var reply = getFallbackReply(this.state.currentCharId);
    var charMsg = { role: 'assistant', content: reply, time: this.formatTime(new Date()) };
    this.appendMessage(charMsg);
    this.state.messages.push(charMsg);
  },

  // ---- Manual Paint (user-provided prompt with full params) ----
  manualPaint: function() {
    var self = this;
    if (this.state.streaming) return;

    // Build and show a proper prompt modal
    var overlay = document.createElement('div');
    overlay.className = 'paint-modal-overlay';
    overlay.innerHTML =
      '<div class="paint-modal">' +
        '<div class="paint-modal-header">' +
          '<span>🎨 Manual Paint</span>' +
          '<button class="paint-modal-close">&times;</button>' +
        '</div>' +
        '<div class="paint-modal-body">' +
          '<label>Positive Prompt <span style="color:var(--text-muted);font-size:11px">(English, comma-separated tags)</span></label>' +
          '<textarea class="paint-prompt-input" id="paint-pos-prompt" rows="4" placeholder="masterpiece, best quality, 1girl, natsume, white hair, red eyes, standing, cherry blossom..."></textarea>' +
          '<label>Negative Prompt</label>' +
          '<textarea class="paint-prompt-input" id="paint-neg-prompt" rows="2">worst quality, bad quality, low quality, blurry, lowres, bad anatomy, extra fingers, missing fingers, extra limbs, deformed, disfigured, watermark, text, signature, jpeg artifacts</textarea>' +
          '<label>Quick Presets</label>' +
          '<div class="paint-preset-row">' +
            '<button class="paint-preset-btn" data-prompt="masterpiece, best quality, 1girl, natsume, white hair, red eyes, school uniform, standing, cherry blossom, soft lighting, detailed">Natsume</button>' +
            '<button class="paint-preset-btn" data-prompt="masterpiece, best quality, 1girl, sakura, silver pink hair, light blue eyes, school uniform, serious expression, moonlight, detailed">Sakura</button>' +
            '<button class="paint-preset-btn" data-prompt="masterpiece, best quality, 1girl, atori, silver hair, red eyes, white dress, barefoot, seaside sunset, warm light, detailed">Atori</button>' +
            '<button class="paint-preset-btn" data-prompt="masterpiece, best quality, 1girl, enola, brown hair, gentle smile, casual clothes, soft lighting, warm atmosphere">Enola</button>' +
          '</div>' +
          '<div class="paint-param-row">' +
            '<div class="paint-param"><label>W</label><input type="number" id="paint-width" value="1200" min="256" max="2048" step="64"></div>' +
            '<div class="paint-param"><label>H</label><input type="number" id="paint-height" value="1500" min="256" max="2048" step="64"></div>' +
            '<div class="paint-param"><label>Steps</label><input type="number" id="paint-steps" value="30" min="5" max="100"></div>' +
            '<div class="paint-param"><label>CFG</label><input type="number" id="paint-cfg" value="6.0" min="1" max="20" step="0.5"></div>' +
          '</div>' +
        '</div>' +
        '<div class="paint-modal-footer">' +
          '<button class="btn-secondary" id="paint-cancel">Cancel</button>' +
          '<button class="btn-primary" id="paint-generate"><i class="ph ph-image"></i> Generate</button>' +
        '</div>' +
      '</div>';

    document.body.appendChild(overlay);

    var closeModal = function() { overlay.remove(); };
    overlay.querySelector('.paint-modal-close').addEventListener('click', closeModal);
    overlay.querySelector('#paint-cancel').addEventListener('click', closeModal);
    overlay.addEventListener('click', function(e) { if (e.target === overlay) closeModal(); });

    // Preset buttons
    overlay.querySelectorAll('.paint-preset-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        overlay.querySelector('#paint-pos-prompt').value = btn.dataset.prompt;
      });
    });

    // Generate
    overlay.querySelector('#paint-generate').addEventListener('click', function() {
      var pos = overlay.querySelector('#paint-pos-prompt').value.trim();
      if (!pos) { showToast('Please enter a positive prompt'); return; }
      var neg = overlay.querySelector('#paint-neg-prompt').value.trim();
      var width = parseInt(overlay.querySelector('#paint-width').value) || 1200;
      var height = parseInt(overlay.querySelector('#paint-height').value) || 1500;
      var steps = parseInt(overlay.querySelector('#paint-steps').value) || 30;
      var cfg = parseFloat(overlay.querySelector('#paint-cfg').value) || 6.0;
      closeModal();

      self.appendSystemMsg('🎨 Generating from manual prompt...');
      self.scrollToBottom();
      self._submitPaintJob(pos, neg, width, height, steps, cfg);
    });

    // Focus the input
    setTimeout(function() {
      var ta = overlay.querySelector('#paint-pos-prompt');
      if (ta) ta.focus();
    }, 100);
  },

  // ---- Auto Paint (AI-driven image generation from chat context) ----
  autoPaint: function() {
    var self = this;
    if (this.state.streaming) return;
    if (this.state.messages.length === 0) {
      showToast('Start a conversation first so I know what to draw~');
      return;
    }

    // Show generating indicator in chat
    this.appendSystemMsg('🎨 Generating illustration from conversation context...');
    this.scrollToBottom();

    var charId = this.state.currentCharId || 'natsume';
    var recentMessages = this.state.messages.slice(-10);

    // Ask daemon to generate a paint prompt via LLM
    fetch('http://localhost:19260/api/gen-prompt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        characterId: charId,
        messages: recentMessages,
      }),
      signal: AbortSignal.timeout(60000),
    })
      .then(function(res) { return res.json(); })
      .then(function(data) {
        if (data.prompt) {
          self.appendSystemMsg('✨ Prompt: ' + data.prompt.substring(0, 80) + '...');
          self.scrollToBottom();
          self._submitPaintJob(data.prompt, data.negative || 'bad quality, worst quality, blurry, distorted, lowres, bad anatomy, extra fingers, watermark, text');
        } else {
          self.appendSystemMsg('⚠️ Failed to generate paint prompt: ' + (data.error || 'unknown'));
          self.scrollToBottom();
        }
      })
      .catch(function(err) {
        self.appendSystemMsg('⚠️ Paint prompt generation failed: ' + err.message);
        self.scrollToBottom();
      });
  },

  _submitPaintJob: function(prompt, negative, width, height, steps, cfg) {
    var self = this;
    // Prepend quality tags if not already present
    var qualityPrefix = 'masterpiece, best quality, highly detailed,';
    var hasQuality = /masterpiece|best.quality/i.test(prompt);
    var finalPositive = hasQuality ? prompt : qualityPrefix + ' ' + prompt;

    var defaultNegative = 'worst quality, bad quality, low quality, blurry, lowres, bad anatomy, extra fingers, missing fingers, extra limbs, deformed, disfigured, watermark, text, signature, jpeg artifacts, censored';
    var finalNegative = negative || defaultNegative;

    var params = {
      positive: finalPositive,
      negative: finalNegative,
      width: width || 1200,
      height: height || 1500,
      steps: steps || 30,
      cfg: cfg || 6.0,
      checkpoint: 'WAI-Nsfw-Illustrious-17.safetensors',
      manage_llama: document.getElementById('chat-manage-llama').checked,
    };

    var bridgeUrl = getSettings().bridgeUrl || 'http://localhost:19250';

    fetch(bridgeUrl + '/api/comfyui', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
      signal: AbortSignal.timeout(5000),
    })
      .then(function(res) { return res.json(); })
      .then(function(data) {
        if (data.job_id) {
          self.appendSystemMsg('🖼️ Image generation started... (job: ' + data.job_id.substring(0, 8) + ')');
          self.scrollToBottom();
          self._pollAutoPaint(data.job_id);
        } else {
          self.appendSystemMsg('⚠️ Failed to start image generation: ' + (data.error || 'unknown'));
          self.scrollToBottom();
        }
      })
      .catch(function(err) {
        self.appendSystemMsg('⚠️ Image generation failed: ' + err.message);
        self.scrollToBottom();
      });
  },

  _pollAutoPaint: function(jobId) {
    var self = this;
    var bridgeUrl = getSettings().bridgeUrl || 'http://localhost:19250';
    var attempt = 0;
    var maxAttempts = 180;

    var interval = setInterval(function() {
      attempt++;
      fetch(bridgeUrl + '/api/jobs/' + jobId, { signal: AbortSignal.timeout(3000) })
        .then(function(res) { return res.json(); })
        .then(function(job) {
          if (job.status === 'done') {
            clearInterval(interval);
            // Show image in chat
            var imgSrc = self._resolveMediaPath(job.path);
            var imgHtml = '<br><img src="' + imgSrc + '" alt="Generated" loading="lazy">';
            var el = document.createElement('div');
            el.className = 'msg-system paint-done';
            el.innerHTML = '🖼️ Done! (' + Math.round(job.elapsed || 0) + 's)' + imgHtml;
            self.$messages.appendChild(el);
            self.scrollToBottom();
          } else if (job.status === 'failed') {
            clearInterval(interval);
            self.appendSystemMsg('💔 Image generation failed: ' + (job.error || 'unknown'));
            self.scrollToBottom();
          }
        })
        .catch(function() {});

      if (attempt >= maxAttempts) {
        clearInterval(interval);
        self.appendSystemMsg('⏰ Image generation timed out');
        self.scrollToBottom();
      }
    }, 3000);
  },

  _resolveMediaPath: function(path) {
    // Proxy local files through daemon: /api/media/<encoded-absolute-path>
    if (!path) return '';
    return 'http://localhost:19260/api/media/' + encodeURIComponent(path);
  },

  // Parse MEDIA: directive from message text, returns { cleanText, mediaPath }
  _parseMediaFromText: function(text) {
    if (!text) return { cleanText: text, mediaPath: null };
    // Match MEDIA: directive — supports backtick-quoted and bare paths
    var re = /^MEDIA:\s*(?:`([^`\n]+)`|([^\n]+))\s*$/m;
    var m = text.match(re);
    if (!m) return { cleanText: text, mediaPath: null };
    var path = (m[1] || m[2] || '').trim();
    // Strip all MEDIA and qqmedia lines from text
    var clean = text.replace(/^(MEDIA|qqmedia):\s*[^\n]*\n?/gm, '').trim();
    return { cleanText: clean, mediaPath: path };
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
        // Re-extract MEDIA: from stored text on load (just in case media wasn't saved separately)
        if (!m.media && m.content && m.role === 'assistant') {
          var parsed = self._parseMediaFromText(m.content);
          if (parsed.mediaPath) {
            m.media = self._resolveMediaPath(parsed.mediaPath);
            m.content = parsed.cleanText;
            self.state.messages[i] = m;
          }
        }
        var el = self.renderMessage(m, i);
        self.$messages.appendChild(el);
      });
    }
    this._userScrolledUp = false;
    this.scrollToBottom(true);
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
    var refreshBtn = document.getElementById('settings-refresh-models');

    if (saveBtn) saveBtn.addEventListener('click', function() {
      var s = getSettings();
      s.apiBase = document.getElementById('setting-api-base').value.trim() || 'http://localhost:18789';
      s.bridgeUrl = document.getElementById('setting-bridge-url').value.trim() || 'http://localhost:19250';
      s.model = document.getElementById('setting-model-select').value || 'local/qwen3.6-35b';
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

    var streamCheckbox = document.getElementById('setting-stream');
    var streamToggle = document.getElementById('toggle-stream-switch');
    if (streamCheckbox && streamToggle) streamCheckbox.addEventListener('change', function(e) {
      streamToggle.classList.toggle('on', e.target.checked);
    });

    if (overlay) overlay.addEventListener('click', function(e) {
      if (e.target.id === 'settings-overlay') {
        overlay.classList.remove('open');
      }
    });

    if (refreshBtn) refreshBtn.addEventListener('click', function() {
      ApiClient._modelsCache = null;
      ApiClient._modelsPromise = null;
      UI._populateModelSelect(true);
      showToast('Refreshing models...');
    });
  },

  _populateModelSelect: function(forceRefresh) {
    var select = document.getElementById('setting-model-select');
    if (!select) return;
    var currentModel = getSettings().model || 'local/qwen3.6-35b';

    // Show loading
    select.innerHTML = '<option value="">Loading models...</option>';

    ApiClient.fetchModels().then(function(models) {
      select.innerHTML = models.map(function(m) {
        var sel = m.id === currentModel ? ' selected' : '';
        return '<option value="' + m.id + '"' + sel + '>' + m.name + ' (' + m.id + ')</option>';
      }).join('');
      if (models.length === 0) {
        select.innerHTML = '<option value="local/qwen3.6-35b">Local (Llama) - default</option>';
      }
    }).catch(function() {
      select.innerHTML = '<option value="local/qwen3.6-35b">Local (Llama) - default</option>';
    });
  },

  openSettings: function() {
    var self = this;
    var s = getSettings();
    var apiBase = document.getElementById('setting-api-base');
    var bridgeUrl = document.getElementById('setting-bridge-url');
    var streamCheckbox = document.getElementById('setting-stream');
    var streamToggle = document.getElementById('toggle-stream-switch');
    var overlay = document.getElementById('settings-overlay');

    if (apiBase) apiBase.value = s.apiBase || 'http://localhost:18789';
    if (bridgeUrl) bridgeUrl.value = s.bridgeUrl || 'http://localhost:19250';
    if (streamCheckbox) streamCheckbox.checked = s.streamEnabled !== false;
    if (streamToggle) streamToggle.classList.toggle('on', s.streamEnabled !== false);
    if (overlay) overlay.classList.add('open');

    // Populate model dropdown from Gateway
    this._populateModelSelect();
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
