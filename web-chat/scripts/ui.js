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
    ttsStreaming: false,
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
    WorldBook.init();
    this.state.currentCharId = getActiveCharId();
    this.state.currentSessionId = ensureDefaultSession(this.state.currentCharId);
    this.loadCharUI();
    this.loadSessionsList();
    this.loadHistory();
    this.setupEvents();
    this.checkGateway();
    this.$input.focus();
    this._updateStreamingTTSVisibility();

    // Avatar modal
    this._initAvatarModal();

    // When API characters arrive, refresh the UI
    if (CHAR_API_PROMISE) {
      CHAR_API_PROMISE.then(function () {
        self.loadCharUI();
        self.rebuildCharList();
        self.loadSessionsList();
        self._updateStreamingTTSVisibility();
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

    // Desktop sidebar handle — hover to peek, click to lock
    var sidebarHandle = document.getElementById('sidebar-handle');
    var sidebar = document.getElementById('sidebar');
    var sidebarLocked = false;
    var hoverTimer = null;
    if (sidebarHandle && sidebar) {
      sidebarHandle.addEventListener('mouseenter', function() {
        if (sidebarLocked) return;
        clearTimeout(hoverTimer);
        sidebar.classList.add('open');
      });
      sidebarHandle.addEventListener('mouseleave', function() {
        if (sidebarLocked) return;
        hoverTimer = setTimeout(function() {
          sidebar.classList.remove('open');
        }, 200);
      });
      sidebar.addEventListener('mouseenter', function() {
        if (sidebarLocked) return;
        clearTimeout(hoverTimer);
        sidebar.classList.add('open');
      });
      sidebar.addEventListener('mouseleave', function() {
        if (sidebarLocked) return;
        hoverTimer = setTimeout(function() {
          sidebar.classList.remove('open');
        }, 300);
      });
      sidebarHandle.addEventListener('click', function() {
        sidebarLocked = !sidebarLocked;
        sidebarHandle.classList.toggle('active', sidebarLocked);
        sidebar.classList.toggle('open', sidebarLocked);
        clearTimeout(hoverTimer);
      });
    }

    // Skill buttons
    document.getElementById('btn-live2d').addEventListener('click', function() { showToast('Live2D - action triggered'); });
    document.getElementById('btn-auto-paint').addEventListener('click', function() { self.autoPaint(); });
    document.getElementById('btn-manual-paint').addEventListener('click', function() { self.manualPaint(); });
    document.getElementById('btn-tts-voice').addEventListener('click', function() { self.ttsVoice(); });
    document.getElementById('btn-tts-streaming').addEventListener('click', function() { self.ttsStreaming(); });

    // Stop llama toggle button (persistent)
    var btnStopLlama = document.getElementById('btn-stop-llama');
    var btnStopLlamaIcon = btnStopLlama.querySelector('i');
    var btnStopLlamaLabel = btnStopLlama.querySelector('.stop-llama-label');
    btnStopLlama.addEventListener('click', function() {
      var isActive = this.classList.toggle('active');
      btnStopLlamaIcon.className = isActive ? 'ph ph-stop-circle-fill' : 'ph ph-stop-circle';
      btnStopLlamaLabel.style.display = isActive ? 'inline' : 'none';
    });

    // (画图停 llama 改为每次弹窗决定，不再用全局 toggle)
    var llamaToggleLabel = document.getElementById('toggle-chat-llama-label');
    var llamaToggleCheck = document.getElementById('chat-manage-llama');
    var llamaToggleSwitch = document.getElementById('toggle-chat-llama-switch');
    if (llamaToggleLabel && llamaToggleCheck && llamaToggleSwitch) {
      llamaToggleLabel.addEventListener('click', function() {
        llamaToggleCheck.checked = !llamaToggleCheck.checked;
        if (llamaToggleCheck.checked) {
          llamaToggleSwitch.classList.add('on');
        } else {
          llamaToggleSwitch.classList.remove('on');
        }
      });
    }

    // Reasoning (deep think) toggle
    var reasoningLabel = document.getElementById('toggle-reasoning-label');
    var reasoningCheck = document.getElementById('chat-reasoning');
    var reasoningSwitch = document.getElementById('toggle-reasoning-switch');
    var thinkingModeRow = document.getElementById('thinking-mode-row');
    var thinkingInline = document.getElementById('thinking-inline-select');
    if (reasoningLabel && reasoningCheck && reasoningSwitch) {
      // Init from settings
      var s = getSettings();
      reasoningCheck.checked = s.reasoningEnabled !== false;
      if (!reasoningCheck.checked) reasoningSwitch.classList.remove('on');
      if (thinkingModeRow) thinkingModeRow.style.display = reasoningCheck.checked ? '' : 'none';
      if (thinkingInline) thinkingInline.value = s.thinkingMode || 'default';

      reasoningLabel.addEventListener('click', function(e) {
        e.preventDefault();
        reasoningCheck.checked = !reasoningCheck.checked;
        var enabled = reasoningCheck.checked;
        if (enabled) {
          reasoningSwitch.classList.add('on');
        } else {
          reasoningSwitch.classList.remove('on');
        }
        if (thinkingModeRow) thinkingModeRow.style.display = enabled ? '' : 'none';
        saveSettings({ reasoningEnabled: enabled });
        var rea = enabled ? 'on' : 'off';
        showToast(enabled ? 'Reasoning ON — 重启llama中，等~30s' : 'Reasoning OFF — 重启llama中，等~30s');
        // Trigger restart immediately
        var xhr = new XMLHttpRequest();
        xhr.open('POST', 'http://localhost:19260/api/exec-script?script=restart_llama_rea.ps1&args=' + rea);
        xhr.timeout = 3000;
        try { xhr.send(); } catch(_) {}
      });
    }

    // Inline thinking mode select (always visible next to input)
    if (thinkingInline) {
      var s2 = getSettings();
      thinkingInline.value = s2.thinkingMode || 'default';
      thinkingInline.addEventListener('change', function() {
        var val = thinkingInline.value;
        saveSettings({ thinkingMode: val });
        // Sync plugins popup select
        var popupSelect = document.getElementById('thinking-mode-select');
        if (popupSelect) popupSelect.value = val;
        showToast('思考风格: ' + thinkingInline.options[thinkingInline.selectedIndex].text);
      });
    }

    // Mem0 memory enhancement toggle
    var mem0Label = document.getElementById('toggle-mem0-label');
    var mem0Check = document.getElementById('chat-mem0-enhanced');
    var mem0Switch = document.getElementById('toggle-mem0-switch');
    var mem0WriteRow = document.getElementById('mem0-interval-row');
    if (mem0Label && mem0Check && mem0Switch) {
      var s = getSettings();
      mem0Check.checked = s.mem0Enhanced === true;
      if (mem0Check.checked) mem0Switch.classList.add('on');
      self._updateMem0SubVisibility();

      mem0Label.addEventListener('click', function() {
        mem0Check.checked = !mem0Check.checked;
        var enabled = mem0Check.checked;
        if (enabled) {
          mem0Switch.classList.add('on');
        } else {
          mem0Switch.classList.remove('on');
        }
        saveSettings({ mem0Enhanced: enabled });
        self._updateMem0SubVisibility();
        showToast(enabled ? 'Mem0 记忆增强: ON' : 'Mem0 记忆增强: OFF');
      });
    }

    // Mem0 auto-write toggle
    var mem0WriteLabel = document.getElementById('toggle-mem0-write-label');
    var mem0WriteCheck = document.getElementById('chat-mem0-write');
    var mem0WriteSwitch = document.getElementById('toggle-mem0-write-switch');
    if (mem0WriteLabel && mem0WriteCheck && mem0WriteSwitch) {
      var s2 = getSettings();
      mem0WriteCheck.checked = s2.mem0WriteEnabled === true;
      if (mem0WriteCheck.checked) mem0WriteSwitch.classList.add('on');

      mem0WriteLabel.addEventListener('click', function() {
        mem0WriteCheck.checked = !mem0WriteCheck.checked;
        var enabled = mem0WriteCheck.checked;
        if (enabled) {
          mem0WriteSwitch.classList.add('on');
        } else {
          mem0WriteSwitch.classList.remove('on');
        }
        saveSettings({ mem0WriteEnabled: enabled });
        showToast(enabled ? 'Mem0 自动写入: ON' : 'Mem0 自动写入: OFF');
      });
    }

    // Mem0 write interval input
    var intervalInput = document.getElementById('mem0-write-interval');
    if (intervalInput) {
      var s3 = getSettings();
      intervalInput.value = s3.mem0WriteInterval || 10;
      intervalInput.addEventListener('change', function() {
        var val = parseInt(intervalInput.value) || 10;
        val = Math.max(1, Math.min(99, val));
        intervalInput.value = val;
        saveSettings({ mem0WriteInterval: val });
      });
    }

    // Memory source toggle (Mem0 vs Session History)
    var memSourceMem0 = document.getElementById('mem-source-mem0');
    var memSourceSession = document.getElementById('mem-source-session');
    if (memSourceMem0 && memSourceSession) {
      var currentMemSource = getSettings().memorySource || 'mem0';
      memSourceMem0.classList.toggle('active', currentMemSource === 'mem0');
      memSourceSession.classList.toggle('active', currentMemSource === 'session');

      memSourceMem0.addEventListener('click', function() {
        currentMemSource = 'mem0';
        memSourceMem0.classList.add('active');
        memSourceSession.classList.remove('active');
        saveSettings({ memorySource: 'mem0' });
        showToast('记忆源: Mem0');
      });

      memSourceSession.addEventListener('click', function() {
        currentMemSource = 'session';
        memSourceSession.classList.add('active');
        memSourceMem0.classList.remove('active');
        saveSettings({ memorySource: 'session' });
        showToast('记忆源: Session History');
      });
    }

    // Plugins popup toggle
    var pluginsBtn = document.getElementById('btn-plugins-toggle');
    var pluginsPopup = document.getElementById('plugins-popup');
    if (pluginsBtn && pluginsPopup) {
      // Init thinking mode select
      var thinkingSelect = document.getElementById('thinking-mode-select');
      if (thinkingSelect) {
        var s5 = getSettings();
        thinkingSelect.value = s5.thinkingMode || 'default';
        thinkingSelect.addEventListener('change', function() {
          saveSettings({ thinkingMode: thinkingSelect.value });
          // Sync inline select
          var inlineSelect = document.getElementById('thinking-inline-select');
          if (inlineSelect) inlineSelect.value = thinkingSelect.value;
          showToast('思考模式: ' + thinkingSelect.options[thinkingSelect.selectedIndex].text);
        });
      }

      pluginsBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        var visible = pluginsPopup.style.display !== 'none';
        pluginsPopup.style.display = visible ? 'none' : '';
      });
      document.addEventListener('click', function(e) {
        if (!pluginsPopup.contains(e.target) && e.target !== pluginsBtn && !pluginsBtn.contains(e.target)) {
          pluginsPopup.style.display = 'none';
        }
      });
    }

    // New chat button in sessions list
    document.getElementById('btn-new-chat').addEventListener('click', function() { self.createSession(); });

    // Memory viewer panel
    var memViewerOverlay = document.getElementById('memory-viewer-overlay');
    var memViewerBody = document.getElementById('memory-viewer-body');
    var memViewerFooter = document.getElementById('memory-viewer-footer');
    var memViewerTitle = document.getElementById('memory-viewer-title');
    var memViewerClose = document.getElementById('memory-viewer-close');
    var btnViewMemory = document.getElementById('btn-view-memory');
    if (memViewerOverlay && memViewerBody && memViewerFooter && btnViewMemory) {
      // Open memory viewer
      btnViewMemory.addEventListener('click', function() {
        self._openMemoryViewer();
      });
      // Close button
      if (memViewerClose) {
        memViewerClose.addEventListener('click', function() {
          memViewerOverlay.classList.remove('open');
        });
      }
      // Click outside to close
      memViewerOverlay.addEventListener('click', function(e) {
        if (e.target === memViewerOverlay) {
          memViewerOverlay.classList.remove('open');
        }
      });
    }

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
      var avatarHtml = self._renderDropdownAvatar(c);
      var avatarTag = typeof avatarHtml === 'string' && avatarHtml.indexOf('<img') === 0
        ? '<div class="char-option-avatar"><img class="char-option-avatar-img" src="' + avatarHtml.replace(/^<img[^>]*src="|">$/g, '') + '"></div>'
        : '<div class="char-option-avatar">' + avatarHtml + '</div>';
      return '<div class="char-option' + activeClass + '" data-char-id="' + c.id + '">' + avatarTag + '<span>' + c.name + '</span>' + deleteBtn + '</div>';
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
    this._updateStreamingTTSVisibility();
  },

  loadCharUI: function() {
    var c = getChar(this.state.currentCharId);
    if (!c) {
      console.warn('No character found for id:', this.state.currentCharId);
      return;
    }
    if (this.$charName) this.$charName.textContent = c.name;
    if (this.$charSubtitle) this.$charSubtitle.textContent = c.nameEn;
    this._renderCharAvatar();
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

  // ---- Avatar Rendering ----
  _renderCharAvatar: function() {
    var charId = this.state.currentCharId;
    var c = getChar(charId);
    var avatarEl = document.querySelector('.char-avatar');
    if (!avatarEl) return;

    // Check stored avatar first, then character data, then fallback to icon
    var avatarData = getCharAvatar(charId) || (c && c.avatar);
    var iconEl = document.getElementById('char-avatar-icon');

    if (avatarData) {
      // Remove icon if exists
      if (iconEl && iconEl.parentNode) iconEl.remove();
      // Remove existing img if any
      var existingImg = avatarEl.querySelector('.char-avatar-img');
      if (existingImg) existingImg.remove();

      var img = document.createElement('img');
      img.className = 'char-avatar-img';
      img.src = avatarData;
      img.alt = (c && c.name) || '';
      avatarEl.appendChild(img);
      avatarEl.title = 'Click to change avatar';
    } else {
      // Show icon
      if (iconEl) iconEl.textContent = (c && c.icon) || '?';
      else {
        var span = document.createElement('span');
        span.className = 'char-avatar-icon';
        span.id = 'char-avatar-icon';
        span.textContent = (c && c.icon) || '?';
        avatarEl.appendChild(span);
      }
      avatarEl.title = '';
    }
  },

  _renderDropdownAvatar: function(c) {
    // Returns avatar HTML for dropdown items
    var avatarData = getCharAvatar(c.id) || (c && c.avatar);
    if (avatarData) {
      return '<img class="char-option-avatar-img" src="' + avatarData + '">';
    }
    return c.icon.toUpperCase();
  },

  initCharSelector: function() {
    var self = this;
    var btn = document.getElementById('char-select-btn');
    var dropdown = document.getElementById('char-dropdown');
    var list = document.getElementById('char-dropdown-list');
    if (!btn || !dropdown || !list) return;

    list.innerHTML = CHARACTERS.map(function(c) {
      var deleteBtn = c.imported ? '<i class="ph ph-x char-delete-btn" data-char-id="' + c.id + '" title="Delete ' + c.name + '"></i>' : '';
      var avatarHtml = self._renderDropdownAvatar(c);
      var avatarTag = typeof avatarHtml === 'string' && avatarHtml.indexOf('<img') === 0
        ? '<div class="char-option-avatar"><img class="char-option-avatar-img" src="' + avatarHtml.replace(/^<img[^>]*src="|">$/g, '') + '"></div>'
        : '<div class="char-option-avatar">' + avatarHtml + '</div>';
      return '<div class="char-option" data-char-id="' + c.id + '">' + avatarTag + '<span>' + c.name + '</span>' + deleteBtn + '</div>';
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

  // ---- Avatar Modal ----
  _initAvatarModal: function() {
    var self = this;
    this._avatarCharId = null;
    this._avatarDataURL = null;

    // Click on sidebar avatar opens modal
    var sidebarAvatar = document.querySelector('.char-avatar');
    if (sidebarAvatar) {
      sidebarAvatar.addEventListener('click', function() {
        self._openAvatarModal(self.state.currentCharId);
      });
    }

    // Modal close button
    var closeBtn = document.getElementById('avatar-modal-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function() {
        self._closeAvatarModal();
      });
    }

    // Click outside panel closes modal
    var modal = document.getElementById('avatar-modal');
    if (modal) {
      modal.addEventListener('click', function(e) {
        if (e.target === modal) self._closeAvatarModal();
      });
    }

    // File input change — THE ONLY change handler
    var fileInput = document.getElementById('avatar-file-input');
    if (fileInput) {
      fileInput.addEventListener('change', function(e) {
        var file = e.target.files && e.target.files[0];
        if (file) self._handleAvatarFile(file);
      });
    }

    // Preview area click opens file picker
    var preview = document.getElementById('avatar-preview');
    if (preview) {
      preview.addEventListener('click', function(e) {
        var cropBox = document.getElementById('avatar-crop-box');
        if (cropBox && cropBox.style.display === 'block') return;
        if (e.target.id === 'avatar-crop-box') return;
        if (e.target.id && e.target.id.startsWith('avatar-crop-handle')) return;
        document.getElementById('avatar-file-input').click();
      });
    }

    // Drop zone click also opens file picker
    var dropZone = document.getElementById('avatar-drop-zone');
    if (dropZone) {
      dropZone.addEventListener('click', function(e) {
        e.stopPropagation();
        document.getElementById('avatar-file-input').click();
      });
    }

    // Drop zone (drag & drop support)
    if (dropZone) {
      dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropZone.classList.add('dragover');
      });
      dropZone.addEventListener('dragleave', function() {
        dropZone.classList.remove('dragover');
      });
      dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        var file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
        if (file && file.type.indexOf('image/') === 0) self._handleAvatarFile(file);
      });
    }

    // Remove avatar button
    var removeBtn = document.getElementById('btn-remove-avatar');
    if (removeBtn) {
      removeBtn.addEventListener('click', function() {
        self._removeAvatar();
      });
    }

    // Crop Apply button
    var btnCropApply = document.getElementById('btn-crop-apply');
    if (btnCropApply) {
      btnCropApply.addEventListener('click', function() {
        self._applyCrop();
      });
    }

    // Crop Cancel button
    var btnCropCancel = document.getElementById('btn-crop-cancel');
    if (btnCropCancel) {
      btnCropCancel.addEventListener('click', function() {
        self._cancelCrop();
      });
    }

    // Stash crop event handlers so we can add/remove them
    self._onCropDragHandler = null;
    self._onCropEndHandler = null;
    self._onCropDragTouchHandler = null;
    self._onCropEndHandlerTouch = null;
    self._cropPct = { x: 0, y: 0, w: 1, h: 1 };

    // Attach crop drag events once (one-time setup)
    self._attachCropEvents();
  },

  _openAvatarModal: function(charId) {
    var self = this;
    this._avatarCharId = charId;
    var c = getChar(charId);
    var modal = document.getElementById('avatar-modal');
    var iconEl = document.getElementById('avatar-preview-icon');
    var imgEl = document.getElementById('avatar-preview-img');
    var infoEl = document.getElementById('avatar-char-info');

    if (infoEl) infoEl.textContent = c ? (c.name + ' — ' + c.nameEn) : '';

    // Hide crop UI and reset state
    var cropBox = document.getElementById('avatar-crop-box');
    var hintEl = document.getElementById('avatar-crop-hint');
    var btnApply = document.getElementById('btn-crop-apply');
    var btnCancel = document.getElementById('btn-crop-cancel');
    if (cropBox) cropBox.style.display = 'none';
    if (hintEl) hintEl.style.display = 'none';
    if (btnApply) btnApply.style.display = 'none';
    if (btnCancel) btnCancel.style.display = 'none';
    this._cropPct = { x: 0, y: 0, w: 1, h: 1 };
    this._cropDragging = false;

    // Check for existing avatar
    var avatarData = getCharAvatar(charId) || (c && c.avatar);
    if (avatarData && imgEl) {
      imgEl.src = avatarData;
      imgEl.style.display = 'block';
      if (iconEl) iconEl.style.display = 'none';
    } else {
      if (imgEl) { imgEl.src = ''; imgEl.style.display = 'none'; }
      if (iconEl) { iconEl.textContent = (c && c.icon) || '?'; iconEl.style.display = ''; }
    }

    if (modal) modal.classList.add('open');
  },

  _closeAvatarModal: function() {
    var modal = document.getElementById('avatar-modal');
    if (modal) modal.classList.remove('open');
    var fileInput = document.getElementById('avatar-file-input');
    if (fileInput) fileInput.value = '';
    var nameEl = document.getElementById('avatar-file-name');
    if (nameEl) nameEl.textContent = '';
    this._avatarCharId = null;
    this._avatarDataURL = null;
    this._avatarOriginalUrl = null;
    this._avatarFile = null;
    this._cropPct = { x: 0, y: 0, w: 0, h: 0 };
    this._cropEventsAttached = false;
    this._cropDragging = false;
    // Hide crop UI
    var cropBox = document.getElementById('avatar-crop-box');
    if (cropBox) cropBox.style.display = 'none';
    var hintEl = document.getElementById('avatar-crop-hint');
    if (hintEl) hintEl.style.display = 'none';
    var btnApply = document.getElementById('btn-crop-apply');
    if (btnApply) btnApply.style.display = 'none';
    var btnCancel = document.getElementById('btn-crop-cancel');
    if (btnCancel) btnCancel.style.display = 'none';
    document.removeEventListener('mousemove', this._onCropDragHandler);
    document.removeEventListener('mouseup', this._onCropEndHandler);
    document.removeEventListener('touchmove', this._onCropDragTouchHandler);
    document.removeEventListener('touchend', this._onCropEndHandlerTouch);
  },

  _handleAvatarFile: function(file) {
    var self = this;
    var reader = new FileReader();
    reader.onload = function(e) {
      var dataUrl = e.target.result;
      self._avatarOriginalUrl = dataUrl;
      self._avatarFile = file;

      var imgEl = document.getElementById('avatar-preview-img');
      var iconEl = document.getElementById('avatar-preview-icon');
      if (imgEl) { imgEl.src = dataUrl; imgEl.style.display = 'block'; }
      if (iconEl) iconEl.style.display = 'none';

      // Show crop UI
      var cropBox = document.getElementById('avatar-crop-box');
      var hintEl = document.getElementById('avatar-crop-hint');
      var btnApply = document.getElementById('btn-crop-apply');
      var btnCancel = document.getElementById('btn-crop-cancel');
      if (cropBox) cropBox.style.display = 'block';
      if (hintEl) hintEl.style.display = '';
      if (btnApply) btnApply.style.display = '';
      if (btnCancel) btnCancel.style.display = '';

      var nameEl = document.getElementById('avatar-file-name');
      if (nameEl) nameEl.textContent = '📷 ' + file.name;

      // Initialize crop to full preview area
      self._cropPct = { x: 0, y: 0, w: 1, h: 1 };
      self._syncCropBoxFromPct();
    };
    reader.readAsDataURL(file);
  },

  // ---- Avatar Crop Selection ----
  // ---- Crop helpers (simple percentage-based) ----
  _syncCropBoxFromPct: function() {
    var cropBox = document.getElementById('avatar-crop-box');
    if (!cropBox || !this._cropPct) return;
    var p = this._cropPct;
    cropBox.style.left = (p.x * 100) + '%';
    cropBox.style.top = (p.y * 100) + '%';
    cropBox.style.width = (p.w * 100) + '%';
    cropBox.style.height = (p.h * 100) + '%';
  },

  _cropPctFromPreview: function(clientX, clientY) {
    var preview = document.getElementById('avatar-preview');
    if (!preview) return { x: 0, y: 0 };
    var r = preview.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return { x: 0, y: 0 };
    return {
      x: Math.max(0, Math.min(1, (clientX - r.left) / r.width)),
      y: Math.max(0, Math.min(1, (clientY - r.top) / r.height))
    };
  },

  _attachCropEvents: function() {
    var self = this;
    var preview = document.getElementById('avatar-preview');
    var cropBox = document.getElementById('avatar-crop-box');
    if (!preview || !cropBox) return;

    // Create stored handlers (bound once, reused for add/remove)
    self._onCropDragHandler = self._onCropDrag.bind(self);
    self._onCropEndHandler = self._onCropEnd.bind(self);
    self._onCropDragTouchHandler = self._onCropDragTouch.bind(self);
    self._onCropEndHandlerTouch = self._onCropEnd.bind(self);

    var startDrag = function(edge, clientX, clientY) {
      self._cropDragging = true;
      self._cropDragEdge = edge;
      self._cropDragPct = {
        x: self._cropPct.x, y: self._cropPct.y,
        w: self._cropPct.w, h: self._cropPct.h
      };
      self._cropStartPct = self._cropPctFromPreview(clientX, clientY);
      document.addEventListener('mousemove', self._onCropDragHandler);
      document.addEventListener('mouseup', self._onCropEndHandler);
    };

    var startDragTouch = function(edge, clientX, clientY) {
      self._cropDragging = true;
      self._cropDragEdge = edge;
      self._cropDragPct = {
        x: self._cropPct.x, y: self._cropPct.y,
        w: self._cropPct.w, h: self._cropPct.h
      };
      self._cropStartPct = self._cropPctFromPreview(clientX, clientY);
      document.addEventListener('touchmove', self._onCropDragTouchHandler);
      document.addEventListener('touchend', self._onCropEndHandlerTouch);
    };

    var handleIds = ['tl','tr','bl','br','tm','bm','lm','rm'];
    handleIds.forEach(function(edge) {
      var handle = document.getElementById('avatar-crop-handle-' + edge);
      if (handle) {
        handle.addEventListener('mousedown', function(e) {
          e.stopPropagation(); e.preventDefault();
          startDrag(edge, e.clientX, e.clientY);
        });
        handle.addEventListener('touchstart', function(e) {
          e.stopPropagation(); e.preventDefault();
          var t = e.touches[0];
          startDragTouch(edge, t.clientX, t.clientY);
        });
      }
    });

    cropBox.addEventListener('mousedown', function(e) {
      if (self._cropDragging) return;
      e.stopPropagation(); e.preventDefault();
      startDrag('move', e.clientX, e.clientY);
    });
    cropBox.addEventListener('touchstart', function(e) {
      if (self._cropDragging) return;
      e.stopPropagation(); e.preventDefault();
      var t = e.touches[0];
      startDragTouch('move', t.clientX, t.clientY);
    });
  },

  _onCropDrag: function(e) {
    if (!this._cropDragging) return;
    this._updateCropDrag(e.clientX, e.clientY);
  },

  _onCropDragTouch: function(e) {
    if (!this._cropDragging) return;
    this._updateCropDrag(e.touches[0].clientX, e.touches[0].clientY);
  },

  _updateCropDrag: function(clientX, clientY) {
    var now = this._cropPctFromPreview(clientX, clientY);
    var r = this._cropDragPct; // saved state at drag start
    var newX = r.x, newY = r.y, newW = r.w, newH = r.h;
    var dx = now.x - this._cropStartPct.x;
    var dy = now.y - this._cropStartPct.y;
    var MIN = 0.05;

    switch (this._cropDragEdge) {
      case 'tl':
        newW = r.w + (r.x - now.x); newH = r.h + (r.y - now.y);
        newX = now.x; newY = now.y;
        if (newW < MIN) { newW = MIN; newX = r.x + r.w - MIN; }
        if (newH < MIN) { newH = MIN; newY = r.y + r.h - MIN; }
        break;
      case 'tr':
        newW = r.w + (now.x - (r.x + r.w)); newH = r.h + (r.y - now.y);
        newY = now.y;
        if (newW < MIN) newW = MIN;
        if (newH < MIN) { newH = MIN; newY = r.y + r.h - MIN; }
        break;
      case 'bl':
        newW = r.w + (r.x - now.x); newH = r.h + (now.y - (r.y + r.h));
        newX = now.x;
        if (newW < MIN) { newW = MIN; newX = r.x + r.w - MIN; }
        if (newH < MIN) newH = MIN;
        break;
      case 'br':
        newW = r.w + (now.x - (r.x + r.w)); newH = r.h + (now.y - (r.y + r.h));
        if (newW < MIN) newW = MIN;
        if (newH < MIN) newH = MIN;
        break;
      case 'tm':
        newH = r.h + (r.y - now.y); newY = now.y;
        if (newH < MIN) { newH = MIN; newY = r.y + r.h - MIN; }
        break;
      case 'bm':
        newH = r.h + (now.y - (r.y + r.h));
        if (newH < MIN) newH = MIN;
        break;
      case 'lm':
        newW = r.w + (r.x - now.x); newX = now.x;
        if (newW < MIN) { newW = MIN; newX = r.x + r.w - MIN; }
        break;
      case 'rm':
        newW = r.w + (now.x - (r.x + r.w));
        if (newW < MIN) newW = MIN;
        break;
      case 'move':
        newX = Math.max(0, Math.min(1 - r.w, r.x + dx));
        newY = Math.max(0, Math.min(1 - r.h, r.y + dy));
        break;
    }

    this._cropPct = { x: newX, y: newY, w: newW, h: newH };
    this._syncCropBoxFromPct();
  },

  _onCropEnd: function() {
    this._cropDragging = false;
    this._cropDragEdge = null;
    document.removeEventListener('mousemove', this._onCropDragHandler);
    document.removeEventListener('mouseup', this._onCropEndHandler);
    document.removeEventListener('touchmove', this._onCropDragTouchHandler);
    document.removeEventListener('touchend', this._onCropEndHandlerTouch);
  },

  _applyCrop: function() {
    var self = this;
    var img = new Image();
    img.onload = function() {
      var nw = img.naturalWidth, nh = img.naturalHeight;
      // Reverse the cover scaling: preview is 300x300 with object-fit:cover
      var scaleX, scaleY, offsetX, offsetY;
      if (nw / nh > 1) {
        // Image is wider than preview -> height fills, width overflows
        scaleY = nh / 300;
        scaleX = scaleY;
        offsetX = (nw - 300 * scaleX) / 2;
        offsetY = 0;
      } else {
        // Image is taller -> width fills, height overflows
        scaleX = nw / 300;
        scaleY = scaleX;
        offsetX = 0;
        offsetY = (nh - 300 * scaleY) / 2;
      }

      var p = self._cropPct;
      var cx = offsetX + p.x * 300 * scaleX;
      var cy = offsetY + p.y * 300 * scaleY;
      var cw = p.w * 300 * scaleX;
      var ch = p.h * 300 * scaleY;

      // Square crop from center of selection
      var size = Math.min(cw, ch);
      cx += Math.floor((cw - size) / 2);
      cy += Math.floor((ch - size) / 2);
      if (cx < 0) cx = 0;
      if (cx + size > nw) cx = nw - size;
      if (cy < 0) cy = 0;
      if (cy + size > nh) cy = nh - size;

      var canvas = document.createElement('canvas');
      canvas.width = 256;
      canvas.height = 256;
      var ctx = canvas.getContext('2d');
      ctx.drawImage(img, Math.round(cx), Math.round(cy), Math.round(size), Math.round(size), 0, 0, 256, 256);

      var compressed = canvas.toDataURL('image/jpeg', 0.85);
      self._avatarDataURL = compressed;

      setCharAvatar(self._avatarCharId, compressed);
      self._renderCharAvatar();
      self.rebuildCharList();
      var charObj = getChar(self._avatarCharId);
      if (charObj) charObj.avatar = compressed;

      var previewImg = document.getElementById('avatar-preview-img');
      if (previewImg) previewImg.src = compressed;

      var nameEl = document.getElementById('avatar-file-name');
      if (nameEl) nameEl.textContent = '✓ ' + self._avatarFile.name + ' (' + Math.round(compressed.length * 0.75) + ' bytes)';

      var cropBox = document.getElementById('avatar-crop-box');
      var hintEl = document.getElementById('avatar-crop-hint');
      var btnApply = document.getElementById('btn-crop-apply');
      var btnCancel = document.getElementById('btn-crop-cancel');
      if (cropBox) cropBox.style.display = 'none';
      if (hintEl) hintEl.style.display = 'none';
      if (btnApply) btnApply.style.display = 'none';
      if (btnCancel) btnCancel.style.display = 'none';

      showToast('Avatar updated for ' + (charObj && charObj.name), 'success');
    };
    img.src = self._avatarOriginalUrl;
  },

  _cancelCrop: function() {
    var cropBox = document.getElementById('avatar-crop-box');
    var hintEl = document.getElementById('avatar-crop-hint');
    var btnApply = document.getElementById('btn-crop-apply');
    var btnCancel = document.getElementById('btn-crop-cancel');
    if (cropBox) cropBox.style.display = 'none';
    if (hintEl) hintEl.style.display = 'none';
    if (btnApply) btnApply.style.display = 'none';
    if (btnCancel) btnCancel.style.display = 'none';
    this._cropPct = { x: 0, y: 0, w: 0, h: 0 };
    this._cropDragging = false;
    document.removeEventListener('mousemove', this._onCropDragHandler);
    document.removeEventListener('mouseup', this._onCropEndHandler);
    document.removeEventListener('touchmove', this._onCropDragTouchHandler);
    document.removeEventListener('touchend', this._onCropEndHandlerTouch);
  },

  _compressImage: function(dataUrl, maxSize, callback) {
    var img = new Image();
    img.onload = function() {
      var canvas = document.createElement('canvas');
      var w = img.width, h = img.height;
      if (w > maxSize || h > maxSize) {
        if (w > h) { h = Math.round(h * maxSize / w); w = maxSize; }
        else { w = Math.round(w * maxSize / h); h = maxSize; }
      }
      canvas.width = w;
      canvas.height = h;
      var ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, w, h);
      var compressed = canvas.toDataURL('image/jpeg', 0.8);
      callback(compressed);
    };
    img.src = dataUrl;
  },

  _removeAvatar: function() {
    var self = this;
    removeCharAvatar(self._avatarCharId);
    var c = getChar(self._avatarCharId);
    if (c) c.avatar = null;
    self._closeAvatarModal();
    self._renderCharAvatar();
    self.rebuildCharList();
    showToast('Avatar removed for ' + (c && c.name), 'success');
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
  _renderTreeNode: function(node, index, tree) {
    var el = this.renderMessage(node, index);
    // Add branch indicator if parent has multiple children
    if (tree && node.parentId) {
      var parent = tree.nodes[node.parentId];
      if (parent && parent.childrenIds.length > 1) {
        // Show branch indicator on each child after a branch point
        var branchBar = document.createElement('div');
        branchBar.className = 'msg-branch-info';

        // Figure out current branch number
        var curBranchIdx = -1;
        var walk = tree.currentNodeId;
        while (walk) {
          var idx = parent.childrenIds.indexOf(walk);
          if (idx >= 0) { curBranchIdx = idx; break; }
          var wn = tree.nodes[walk];
          walk = wn ? wn.parentId : null;
        }

        var label = 'Branch ' + (curBranchIdx >= 0 ? (curBranchIdx + 1) : '?') + '/' + parent.childrenIds.length;
        branchBar.innerHTML = '<span class="branch-dot">↳</span> <span class="branch-label">' + label + '</span>';

        // Branch switcher buttons
        var branchBtns = document.createElement('span');
        branchBtns.className = 'branch-switcher';
        var siblings = parent.childrenIds.map(function(id) { return tree.nodes[id]; });
        var self = this;
        siblings.forEach(function(sib, si) {
          var btn = document.createElement('button');
          btn.textContent = '#' + (si + 1);
          btn.title = (sib.regenerated ? '[Old] ' : '') + 'Branch ' + (si + 1) + ': ' + (sib.content || '').slice(0, 40);
          btn.className = 'branch-btn';
          if (sib.regenerated) btn.classList.add('old');

          // Is this branch on the current path?
          var onPath = false;
          var w = tree.currentNodeId;
          while (w) {
            if (w === sib.id) { onPath = true; break; }
            var wnode = tree.nodes[w];
            w = wnode ? wnode.parentId : null;
          }
          if (onPath) btn.classList.add('active');

          (function(targetId, branchIdx) {
            btn.addEventListener('click', function(e) {
              e.stopPropagation();
              jumpToNode(tree, targetId);
              saveSessionTree(self.state.currentCharId, self.state.currentSessionId, tree);
              self.state.messages = getChainMessages(tree);
              self.$messages.innerHTML = '';
              self.appendSystemMsg('Jumped to branch #' + (branchIdx + 1) + ' - ' + self.formatTime(new Date()));
              getCurrentChain(tree).forEach(function(cn, ci) {
                // Only skip system/placeholder nodes. Filtering on `regenerated`
                // here is what made the re-selected branch disappear: the flag
                // stays true on a node forever, even once it is the active branch.
                if (cn.role === 'system' || cn._pending) return;
                // Resolve local filesystem media paths to daemon proxy URLs
                if (cn.media && !/^https?:\/\//.test(cn.media)) {
                  cn.media = self._resolveMediaPath(cn.media);
                }
                var cel = self._renderTreeNode(cn, ci, tree);
                self.$messages.appendChild(cel);
              });
              self.scrollToBottom(true);
            });
          })(sib.id, si);
          branchBtns.appendChild(btn);
        });
        branchBar.appendChild(branchBtns);
        // `el` is `.msg-row`, a horizontal flex container (avatar | content).
        // Inserting as its first child would push the branch bar to the LEFT of
        // the avatar. Put it at the top of the vertical content column instead,
        // so it sits directly above the bubble it describes.
        var branchHost = el.querySelector('.msg-bubble-wrap')
          || (el.querySelector('.msg-bubble') && el.querySelector('.msg-bubble').parentNode)
          || el;
        branchHost.insertBefore(branchBar, branchHost.firstChild);
      }
    }
    return el;
  },

  renderMessage: function(msg, index) {
    var isUser = msg.role === 'user';
    var isSystem = msg.role === 'system';
    var time = msg.time || this.formatTime(new Date());
    var self = this;

    // Superseded messages get a faded placeholder, but ONLY in flat (non-tree)
    // mode. In tree mode a `regenerated` node is still a real, selectable
    // branch: the flag records "this was superseded once", not "never show it".
    // Rendering the stub there is what made branch 1 look like it vanished
    // after generating branch 2.
    if (msg.regenerated && !this.state.tree) {
      var fadedRow = document.createElement('div');
      fadedRow.className = 'msg-row char faded';
      fadedRow.dataset.msgIndex = index;
      var avatar = document.createElement('div');
      avatar.className = 'msg-avatar char';
      avatar.innerHTML = '<i class="ph ph-heart"></i>';
      var bubble = document.createElement('div');
      bubble.className = 'msg-bubble';
      bubble.style.opacity = '0.4';
      bubble.style.fontStyle = 'italic';
      bubble.style.fontSize = '12px';
      bubble.textContent = '(Regenerated)';
      fadedRow.appendChild(avatar);
      fadedRow.appendChild(bubble);
      return fadedRow;
    }

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
    if (isUser) {
      avatar.innerHTML = '<i class="ph ph-user"></i>';
    } else {
      // Check for custom avatar
      var charAvatar = getCharAvatar(this.state.currentCharId) || (getChar(this.state.currentCharId) && getChar(this.state.currentCharId).avatar);
      if (charAvatar) {
        var avImg = document.createElement('img');
        avImg.src = charAvatar;
        avImg.style.cssText = 'width:100%;height:100%;object-fit:cover;border-radius:var(--radius-sm)';
        avatar.appendChild(avImg);
      } else {
        avatar.innerHTML = '<i class="ph ph-heart"></i>';
      }
    }

    var contentWrap = document.createElement('div');
    var bubble = document.createElement('div');
    bubble.className = 'msg-bubble';

    // Text content
    var textEl = document.createElement('span');
    textEl.className = 'msg-text';
    textEl.textContent = msg.content;
    bubble.appendChild(textEl);

    // Edit + Regenerate buttons (on hover)
    var btnsRow = document.createElement('div');
    btnsRow.className = 'msg-btns';

    var editBtn = document.createElement('button');
    editBtn.className = 'msg-edit-btn';
    editBtn.innerHTML = '<i class="ph ph-pencil-simple"></i>';
    editBtn.title = 'Edit message';
    editBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      self.startEditMessage(row, index, msg);
    });
    // Editing text on an image-only message makes no sense.
    if (!msg.paint) btnsRow.appendChild(editBtn);

    if (!isUser && msg.role === 'assistant') {
      var regenBtn = document.createElement('button');
      regenBtn.className = 'msg-regen-btn';
      if (msg.paint) {
        // Image messages get their own re-roll affordance so it is obvious the
        // action re-runs the image job, not the text model.
        regenBtn.classList.add('msg-repaint-btn');
        regenBtn.innerHTML = '<i class="ph ph-image"></i>';
        regenBtn.title = msg.paintParams && msg.paintParams.positive
          ? 'Re-roll this image'
          : 'No prompt stored for this image';
        if (!(msg.paintParams && msg.paintParams.positive)) {
          regenBtn.disabled = true;
          regenBtn.classList.add('is-disabled');
        }
      } else {
        regenBtn.innerHTML = '<i class="ph ph-arrows-clockwise"></i>';
        regenBtn.title = 'Regenerate reply';
      }
      regenBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        if (regenBtn.disabled) return;
        self.regenerateMessage(index);
      });
      btnsRow.appendChild(regenBtn);
    }

    // NOTE: btnsRow is intentionally NOT appended to `row` here.
    // `.msg-row` is a horizontal flex container (avatar | content), so a direct
    // child lands BESIDE the bubble. It is appended into contentWrap below the
    // bubble instead, so Edit/Regenerate sit under the message they act on.

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
        img.addEventListener('error', function() {
          img.style.display = 'none';
          var placeholder = document.createElement('div');
          placeholder.className = 'media-placeholder';
          placeholder.innerHTML = '<i class="ph ph-image-broken"></i><span>Image unavailable</span>';
          // The error event can fire after a re-render has detached this node,
          // in which case parentNode is null. Fall back to the bubble.
          if (img.parentNode) {
            img.parentNode.insertBefore(placeholder, img);
          } else if (bubble) {
            bubble.appendChild(placeholder);
          }
        });
        bubble.appendChild(img);
      }
    }

    // Paint messages: image-only, compact layout
    if (msg.paint && msg.media) {
      bubble.classList.add('paint-msg');
      // Resolve media path for display
      var paintSrc = msg.media;
      if (!/^https?:\/\//.test(paintSrc)) {
        paintSrc = self._resolveMediaPath(paintSrc);
      }
      var paintImg = document.createElement('img');
      paintImg.className = 'msg-media paint-media';
      paintImg.src = paintSrc;
      paintImg.loading = 'lazy';
      paintImg.addEventListener('click', function() { window.open(paintSrc, '_blank'); });
      paintImg.addEventListener('error', function() {
        paintImg.style.display = 'none';
        var placeholder = document.createElement('div');
        placeholder.className = 'media-placeholder';
        placeholder.innerHTML = '<i class="ph ph-image-broken"></i><span>Image unavailable (daemon offline)</span>';
        bubble.appendChild(placeholder);
      });
      bubble.innerHTML = '';
      bubble.appendChild(paintImg);
      var paintLabel = document.createElement('div');
      paintLabel.className = 'paint-label';
      paintLabel.textContent = '🖼️ Generated';
      bubble.appendChild(paintLabel);
    }

    var timeEl = document.createElement('div');
    timeEl.className = 'msg-time';
    timeEl.textContent = time;

    contentWrap.appendChild(bubble);
    contentWrap.appendChild(timeEl);
    contentWrap.appendChild(btnsRow);
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

  // ---- Message Editing ----
  startEditMessage: function(row, index, msg) {
    var self = this;
    // Don't re-edit if already editing
    if (row.classList.contains('editing')) return;

    row.classList.add('editing');
    var bubble = row.querySelector('.msg-bubble');
    if (!bubble) return;

    var originalText = msg.content || '';
    var existingTextEl = bubble.querySelector('.msg-text');

    // Replace text with textarea
    var ta = document.createElement('textarea');
    ta.className = 'msg-edit-textarea';
    ta.value = originalText;
    bubble.innerHTML = '';
    bubble.appendChild(ta);
    ta.focus();
    ta.setSelectionRange(ta.value.length, ta.value.length);

    // Save on Ctrl+Enter or blur
    var save = function() {
      var newText = ta.value;
      if (newText === originalText) {
        self.cancelEditMessage(row, index, msg, originalText);
        return;
      }
      msg.content = newText;
      self.state.messages[index] = msg;
      saveChatHistory(self.state.currentCharId, self.state.currentSessionId, self.state.messages);
      self.cancelEditMessage(row, index, msg, newText);
      showToast('Message updated');
    };

    ta.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && e.ctrlKey) {
        e.preventDefault();
        save();
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        self.cancelEditMessage(row, index, msg, originalText);
      }
    });

    ta.addEventListener('blur', function() {
      // Small delay to allow click events on other UI
      setTimeout(function() {
        if (row.classList.contains('editing')) {
          save();
        }
      }, 200);
    });
  },

  cancelEditMessage: function(row, index, msg, text) {
    row.classList.remove('editing');
    var bubble = row.querySelector('.msg-bubble');
    if (!bubble) return;
    bubble.innerHTML = '';
    var span = document.createElement('span');
    span.className = 'msg-text';
    span.textContent = text || msg.content || '';
    bubble.appendChild(span);
    // Re-render media if any
    if (msg.media) {
      if (msg.paint) {
        var paintSrc = msg.media;
        if (!/^https?:\/\//.test(paintSrc)) {
          paintSrc = this._resolveMediaPath(paintSrc);
        }
        var paintImg = document.createElement('img');
        paintImg.className = 'msg-media paint-media';
        paintImg.src = paintSrc;
        paintImg.loading = 'lazy';
        paintImg.addEventListener('click', function() { window.open(paintSrc, '_blank'); });
        bubble.appendChild(paintImg);
        var paintLabel = document.createElement('div');
        paintLabel.className = 'paint-label';
        paintLabel.textContent = '🖼️ Generated';
        bubble.appendChild(paintLabel);
      } else if (msg.mediaType === 'audio' || /\.(wav|mp3|ogg)$/.test(msg.media)) {
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
    // Restore long collapse
    if (msg.content && msg.content.length > this.LONG_MSG_THRESHOLD && msg.role !== 'user') {
      bubble.classList.add('long-collapsed');
    }

    // Restore button row.
    // Reuse the existing row if present so cancelling an edit twice does not
    // stack duplicate button rows.
    var btnsRow = row.querySelector('.msg-btns');
    if (btnsRow) {
      btnsRow.innerHTML = '';
    } else {
      btnsRow = document.createElement('div');
      btnsRow.className = 'msg-btns';
    }

    var editBtn2 = document.createElement('button');
    editBtn2.className = 'msg-edit-btn';
    editBtn2.innerHTML = '<i class="ph ph-pencil-simple"></i>';
    editBtn2.title = 'Edit message';
    editBtn2.addEventListener('click', function(e) {
      e.stopPropagation();
      self.startEditMessage(row, index, msg);
    });
    btnsRow.appendChild(editBtn2);

    if (msg.role === 'assistant') {
      var regenBtn2 = document.createElement('button');
      regenBtn2.className = 'msg-regen-btn';
      regenBtn2.innerHTML = '<i class="ph ph-arrows-clockwise"></i>';
      regenBtn2.title = 'Regenerate reply';
      regenBtn2.addEventListener('click', function(e) {
        e.stopPropagation();
        self.regenerateMessage(index);
      });
      btnsRow.appendChild(regenBtn2);
    }

    // Put the buttons under the bubble, inside the vertical content column --
    // not directly on `.msg-row`, which is a horizontal flex container.
    var wrap = bubble.parentNode || row;
    wrap.appendChild(btnsRow);
  },

  // ---- Regenerate ----
  regenerateMessage: function(assistantIndex) {
    var self = this;
    if (this.state.streaming) return;

    // Image messages carry no text, so the LLM text-stream path cannot
    // regenerate them. Re-run the image job instead.
    var target = this.state.messages[assistantIndex];
    if (target && target.paint) {
      this._regeneratePaint(assistantIndex);
      return;
    }

    var charId = this.state.currentCharId;
    var sessionId = this.state.currentSessionId;

    // ── Tree mode: create a branch ────
    if (this._useTree && this.state.tree) {
      var newId = branchRegenerate(this.state.tree, assistantIndex);
      if (!newId) return;

      // Re-render from tree
      this.state.messages = getChainMessages(this.state.tree);
      this.$messages.innerHTML = '';
      this.appendSystemMsg('Branch: regenerating - ' + this.formatDate(new Date()));
      var chain = getCurrentChain(this.state.tree);
      chain.forEach(function(n, i) {
        // `_pending` is the empty placeholder for the branch being streamed.
        if (n.role === 'system' || n._pending) return;
        var el = self._renderTreeNode(n, i, self.state.tree);
        self.$messages.appendChild(el);
      });
      saveSessionTree(charId, sessionId, this.state.tree);

      this.state.streaming = true;
      this.$sendBtn.disabled = true;
      this.showTyping();

      var settings = getSettings();
      settings.characterId = charId || 'natsume';
      var currentChar = getChar(charId);
      if (currentChar && currentChar.imported && currentChar.systemPrompt) {
        settings.systemPrompt = currentChar.systemPrompt;
      }

      // Replay messages: only send history up to (and including) the trigger user msg.
      // The pending branch node must NOT be sent to the API.
      //
      // We cut the chain at the trigger user message rather than filtering on
      // `regenerated`. During a regenerate the chain is [... , user, pending],
      // and the superseded assistant is on a DIFFERENT branch, so it is not in
      // this chain at all. Filtering on `regenerated` additionally dropped
      // legitimate earlier turns whose flag was still set from a past
      // regenerate, silently truncating the prompt.
      var allMsgs = getCurrentChain(this.state.tree);
      var lastGoodIdx = -1;
      for (var ri = allMsgs.length - 1; ri >= 0; ri--) {
        var cand = allMsgs[ri];
        if (!cand._pending && cand.role !== 'system' && String(cand.content || '').length) {
          lastGoodIdx = ri;
          break;
        }
      }
      var replayMsgs = allMsgs
        .slice(0, lastGoodIdx + 1)
        .filter(function(n) { return n.role !== 'system' && !n._pending; })
        .map(function(n) { return { role: n.role, content: n.content }; });

      self.hideTyping();
      self.createStreamBubble();

      ApiClient.chatStream(
        replayMsgs,
        settings,
        function(token, type) { self.appendStreamToken(token, type); },
        function(result) {
          self.finalizeStream(result.text);
          var parsed = self._parseMediaFromText(result.text);
          var cleanText = parsed.cleanText;
          var tree = self.state.tree;
          // Update the pending placeholder node with real content
          tree.nodes[newId].content = cleanText;
          tree.nodes[newId].time = self.formatTime(new Date());
          tree.nodes[newId]._pending = false;
          if (result.media) tree.nodes[newId].media = result.media;
          else if (parsed.mediaPath) tree.nodes[newId].media = self._resolveMediaPath(parsed.mediaPath);
          self.state.messages = getChainMessages(tree);
          saveSessionTree(charId, sessionId, tree);
          // Re-render DOM to show the new response and update branch indicators
          self.$messages.innerHTML = '';
          self.appendSystemMsg('Branch: regenerated - ' + self.formatDate(new Date()));
          getCurrentChain(tree).forEach(function(cn, ci) {
            if (cn.role === 'system' || cn._pending) return;
            // Resolve local filesystem media paths to daemon proxy URLs
            if (cn.media && !/^https?:\/\//.test(cn.media)) {
              cn.media = self._resolveMediaPath(cn.media);
            }
            var cel = self._renderTreeNode(cn, ci, tree);
            self.$messages.appendChild(cel);
          });
          self.state.streaming = false;
          self.$sendBtn.disabled = false;
          self.$input.focus();
          self.loadSessionsList();
          showToast('Reply regenerated (new branch)');
        },
        function(err) {
          console.warn('Regenerate stream failed:', err.message);
          self.finalizeStream('');
          var bubble = document.getElementById('stream-bubble');
          if (bubble) bubble.remove();
          self.doFallback(err.message);
          self.state.streaming = false;
          self.$sendBtn.disabled = false;
          self.$input.focus();
        }
      );
      return;
    }

    // ── Flat mode (original logic) ────
    var msg = this.state.messages[assistantIndex];
    if (!msg || msg.role !== 'assistant') return;

    var triggerUserIdx = assistantIndex - 1;
    if (triggerUserIdx < 0 || this.state.messages[triggerUserIdx].role !== 'user') {
      console.warn('No user message immediately before assistant index', assistantIndex);
      return;
    }

    msg.regenerated = true;
    this.state.messages.splice(assistantIndex, 1);

    var rows = this.$messages.querySelectorAll('.msg-row');
    rows.forEach(function(row) {
      var idx = parseInt(row.dataset.msgIndex);
      if (idx === assistantIndex) {
        row.remove();
      }
    });

    this.showTyping();
    this.state.streaming = true;
    this.$sendBtn.disabled = true;

    var replayMessages = this.state.messages.slice(0, triggerUserIdx + 1);

    var settings = getSettings();
    settings.characterId = self.state.currentCharId || 'natsume';
    var currentChar = getChar(self.state.currentCharId);
    if (currentChar && currentChar.imported && currentChar.systemPrompt) {
      settings.systemPrompt = currentChar.systemPrompt;
    }

    if (this.state.messages[triggerUserIdx]) {
      replayMessages.push({
        role: 'assistant',
        content: '(Regenerating: ' + this.formatTime(new Date()) + ')',
        _regenPlaceholder: true,
      });
      replayMessages.push({
        role: 'user',
        content: 'Please reply again with a different answer.',
      });
    }

    self.hideTyping();
    self.createStreamBubble();

    ApiClient.chatStream(
      replayMessages,
      settings,
      function(token, type) { self.appendStreamToken(token, type); },
      function(result) {
        self.finalizeStream(result.text);
        var parsed = self._parseMediaFromText(result.text);
        var cleanText = parsed.cleanText;
        var newMsg = { role: 'assistant', content: cleanText, time: self.formatTime(new Date()) };
        if (result.media) newMsg.media = result.media;
        else if (parsed.mediaPath) newMsg.media = self._resolveMediaPath(parsed.mediaPath);
        self.state.messages.splice(triggerUserIdx + 1, 0, newMsg);
        self.$messages.innerHTML = '';
        for (var mi = 0; mi < self.state.messages.length; mi++) {
          self.$messages.appendChild(self.renderMessage(self.state.messages[mi], mi));
        }
        saveChatHistory(self.state.currentCharId, self.state.currentSessionId, self.state.messages);
        self.state.streaming = false;
        self.$sendBtn.disabled = false;
        self.$input.focus();
        showToast('Reply regenerated');
      },
      function(err) {
        console.warn('Regenerate stream failed:', err.message);
        self.hideTyping();
        var bubble = document.getElementById('stream-bubble');
        if (bubble) bubble.remove();
        self.doFallback(err.message);
        saveChatHistory(self.state.currentCharId, self.state.currentSessionId, self.state.messages);
        self.state.streaming = false;
        self.$sendBtn.disabled = false;
        self.$input.focus();
      }
    );
  },

  // ---- Regenerate an image (paint) message ----
  // Image messages have empty `content`, so the text-stream regenerate path
  // cannot produce anything for them. This re-runs the ComfyUI job using the
  // params stored on the message and swaps the image in place.
  _regeneratePaint: function(assistantIndex) {
    var self = this;
    if (this.state.paintRegenerating) return;

    var msg = this.state.messages[assistantIndex];
    if (!msg || !msg.paint) return;

    var params = msg.paintParams;
    if (!params || !params.positive) {
      showToast('No prompt stored for this image, use Paint to make a new one');
      return;
    }

    var manageLlama = false;
    var stopBtn = document.getElementById('btn-stop-llama');
    if (stopBtn) manageLlama = stopBtn.classList.contains('active');

    this.state.paintRegenerating = true;
    var row = this.$messages.querySelector('.msg-row[data-msg-index="' + assistantIndex + '"]');
    if (row) row.classList.add('paint-regenerating');
    showToast('Re-rolling image...');

    var bridgeUrl = getSettings().bridgeUrl || 'http://localhost:19250';
    var job = {
      positive: params.positive,
      negative: params.negative,
      width: params.width,
      height: params.height,
      steps: params.steps,
      cfg: params.cfg,
      checkpoint: params.checkpoint,
      manage_llama: manageLlama,
    };

    var finish = function(ok, detail) {
      self.state.paintRegenerating = false;
      if (row) row.classList.remove('paint-regenerating');
      if (!ok) {
        self.appendSystemMsg('Image re-roll failed: ' + (detail || 'unknown'));
        self.scrollToBottom();
      }
    };

    fetch(bridgeUrl + '/api/comfyui', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(job),
      signal: AbortSignal.timeout(5000),
    })
      .then(function(res) { return res.json(); })
      .then(function(data) {
        if (!data.job_id) { finish(false, data.error); return; }
        self._pollPaintRegen(data.job_id, assistantIndex, finish);
      })
      .catch(function(err) { finish(false, err.message); });
  },

  _pollPaintRegen: function(jobId, assistantIndex, finish) {
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
            self._applyPaintRegen(assistantIndex, job.path);
            finish(true);
          } else if (job.status === 'failed') {
            clearInterval(interval);
            finish(false, job.error);
          }
        })
        .catch(function() {});

      if (attempt >= maxAttempts) {
        clearInterval(interval);
        finish(false, 'timed out');
      }
    }, 2000);
  },

  // Swap the new image into the message, in both tree and flat sessions.
  _applyPaintRegen: function(assistantIndex, newPath) {
    var self = this;
    var msg = this.state.messages[assistantIndex];
    if (msg) {
      msg.media = newPath;
      msg.time = this.formatTime(new Date());
    }

    if (this._useTree && this.state.tree) {
      var node = getNodeByChainIndex(this.state.tree, assistantIndex);
      if (node) {
        node.media = newPath;
        node.paint = true;
        node.mediaType = 'image';
        node.time = this.formatTime(new Date());
      }
      saveSessionTree(this.state.currentCharId, this.state.currentSessionId, this.state.tree);
      this.state.messages = getChainMessages(this.state.tree);
      this.$messages.innerHTML = '';
      this.appendSystemMsg('Image re-rolled - ' + this.formatTime(new Date()));
      var tree = this.state.tree;
      getCurrentChain(tree).forEach(function(cn, ci) {
        if (cn.role === 'system' || cn._pending) return;
        if (cn.media && !/^https?:\/\//.test(cn.media)) {
          cn.media = self._resolveMediaPath(cn.media);
        }
        self.$messages.appendChild(self._renderTreeNode(cn, ci, tree));
      });
    } else {
      saveChatHistory(this.state.currentCharId, this.state.currentSessionId, this.state.messages);
      this.$messages.innerHTML = '';
      for (var mi = 0; mi < this.state.messages.length; mi++) {
        this.$messages.appendChild(this.renderMessage(this.state.messages[mi], mi));
      }
    }
    this.scrollToBottom(true);
    showToast('Image re-rolled');
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
    // Also clean stale reasoning blocks from old bubbles
    var oldReasoning = document.getElementById('stream-reasoning');
    if (oldReasoning && oldReasoning.parentElement && !oldReasoning.parentElement.querySelector('#stream-bubble')) {
      oldReasoning.removeAttribute('id');
      var oldReasonContent = document.getElementById('stream-reasoning-content');
      if (oldReasonContent) oldReasonContent.removeAttribute('id');
    }

    var row = document.createElement('div');
    row.className = 'msg-row char';
    row.id = 'stream-bubble';
    var avatar = document.createElement('div');
    avatar.className = 'msg-avatar char';
    avatar.innerHTML = '<i class="ph ph-heart"></i>';
    var wrap = document.createElement('div');
    wrap.className = 'msg-bubble-wrap';

    // Reasoning block (hidden until reasoning arrives)
    var reasonBlock = document.createElement('div');
    reasonBlock.className = 'reasoning-block';
    reasonBlock.id = 'stream-reasoning';
    reasonBlock.style.display = 'none';
    var reasonHeader = document.createElement('div');
    reasonHeader.className = 'reasoning-header';
    reasonHeader.innerHTML = '<i class="ph ph-brain"></i> 思考过程 <span class="reasoning-expand">展开</span>';
    reasonHeader.onclick = function() {
      var content = document.getElementById('stream-reasoning-content');
      var isVisible = content.style.display !== 'none';
      content.style.display = isVisible ? 'none' : '';
      reasonHeader.querySelector('.reasoning-expand').textContent = isVisible ? '展开' : '收起';
    };
    var reasonContent = document.createElement('div');
    reasonContent.className = 'reasoning-content';
    reasonContent.id = 'stream-reasoning-content';
    reasonContent.style.display = 'none';
    reasonBlock.appendChild(reasonHeader);
    reasonBlock.appendChild(reasonContent);
    wrap.appendChild(reasonBlock);

    var bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.id = 'stream-bubble-text';
    var cursor = document.createElement('span');
    cursor.className = 'stream-cursor';
    bubble.appendChild(cursor);
    wrap.appendChild(bubble);

    row.appendChild(avatar);
    row.appendChild(wrap);
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

  appendStreamToken: function(text, type) {
    type = type || 'content';
    if (type === 'reasoning') {
      var reasoningBlock = document.getElementById('stream-reasoning');
      var reasoningContent = document.getElementById('stream-reasoning-content');
      if (reasoningBlock && reasoningContent) {
        reasoningBlock.style.display = '';
        reasoningContent.appendChild(document.createTextNode(text));
      }
      return;
    }
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
    // Remove reasoning block if empty
    var reasoningBlock = document.getElementById('stream-reasoning');
    var reasoningContent = document.getElementById('stream-reasoning-content');
    if (reasoningBlock && reasoningContent && !reasoningContent.textContent.trim()) {
      reasoningBlock.remove();
    }

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

    var charId = this.state.currentCharId;
    var sessionId = this.state.currentSessionId;

    var userMsg = { role: 'user', content: content, time: this.formatTime(new Date()) };
    this.appendMessage(userMsg);

    if (this._useTree && this.state.tree) {
      appendTreeNode(this.state.tree, userMsg);
      this.state.messages = getChainMessages(this.state.tree);
      saveSessionTree(charId, sessionId, this.state.tree);
    } else {
      this.state.messages.push(userMsg);
      saveChatHistory(charId, sessionId, this.state.messages);
    }

    this.showTyping();
    this.state.streaming = true;
    this.$sendBtn.disabled = true;

    var settings = getSettings();
    settings.characterId = self.state.currentCharId || 'natsume';
    var currentChar = getChar(self.state.currentCharId);
    if (currentChar && currentChar.imported && currentChar.systemPrompt) {
      settings.systemPrompt = currentChar.systemPrompt;
    }

    if (settings.streamEnabled !== false) {
      self.hideTyping();
      self.createStreamBubble();

      // Use tree messages or flat messages
      var apiMessages = self._useTree && self.state.tree ? getChainMessages(self.state.tree) : self.state.messages;

      ApiClient.chatStream(
        apiMessages,
        settings,
        function(token, type) { self.appendStreamToken(token, type); },
        function(result) {
          self.finalizeStream(result.text);
          var parsed = self._parseMediaFromText(result.text);
          var cleanText = parsed.cleanText;
          var charMsg = { role: 'assistant', content: cleanText, time: self.formatTime(new Date()) };
          if (result.media) charMsg.media = result.media;
          else if (parsed.mediaPath) charMsg.media = self._resolveMediaPath(parsed.mediaPath);

          if (self._useTree && self.state.tree) {
            appendTreeNode(self.state.tree, charMsg);
            self.state.messages = getChainMessages(self.state.tree);
            saveSessionTree(charId, sessionId, self.state.tree);
          } else {
            self.state.messages.push(charMsg);
            saveChatHistory(charId, sessionId, self.state.messages);
          }
          self.state.streaming = false;
          self.$sendBtn.disabled = false;
          self.$input.focus();
          self.loadSessionsList();
        },
        function(err) {
          console.warn('Stream failed:', err.message);
          self.finalizeStream('');
          var bubble = document.getElementById('stream-bubble');
          if (bubble) bubble.remove();
          self.doFallback(err.message);
          if (self._useTree && self.state.tree) {
            saveSessionTree(charId, sessionId, self.state.tree);
          } else {
            saveChatHistory(charId, sessionId, self.state.messages);
          }
          self.state.streaming = false;
          self.$sendBtn.disabled = false;
          self.$input.focus();
        }
      );
    } else {
      var apiMsgs = self._useTree && self.state.tree ? getChainMessages(self.state.tree) : self.state.messages;
      ApiClient.nonStreamChat(apiMsgs, settings).then(function(reply) {
        self.hideTyping();
        var parsed = self._parseMediaFromText(reply);
        var charMsg = { role: 'assistant', content: parsed.cleanText, time: self.formatTime(new Date()) };
        if (parsed.mediaPath) charMsg.media = self._resolveMediaPath(parsed.mediaPath);
        self.appendMessage(charMsg);
        if (self._useTree && self.state.tree) {
          appendTreeNode(self.state.tree, charMsg);
          self.state.messages = getChainMessages(self.state.tree);
          saveSessionTree(charId, sessionId, self.state.tree);
        } else {
          self.state.messages.push(charMsg);
          saveChatHistory(charId, sessionId, self.state.messages);
        }
        self.state.streaming = false;
        self.$sendBtn.disabled = false;
        self.$input.focus();
        self.loadSessionsList();
      }).catch(function(err) {
        console.warn('Non-stream failed:', err.message);
        self.hideTyping();
        self.doFallback(err.message);
        if (self._useTree && self.state.tree) {
          saveSessionTree(charId, sessionId, self.state.tree);
        } else {
          saveChatHistory(charId, sessionId, self.state.messages);
        }
        self.state.streaming = false;
        self.$sendBtn.disabled = false;
        self.$input.focus();
      });
    }
  },

  doFallback: function(error) {
    var errMsg = error ? '⚠️ ' + error : '⚠️ API 请求失败';
    var charMsg = { role: 'assistant', content: errMsg, time: this.formatTime(new Date()) };
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
          '<span style="margin-right:auto;font-size:12px;color:var(--text-muted);align-self:center" id="paint-stop-llama-status"></span>' +
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
      var manage_llama = document.getElementById('btn-stop-llama').classList.contains('active');
      if (manage_llama) self.appendSystemMsg('🎨 Stopping llama for painting...');
      closeModal();

      self.appendSystemMsg('🎨 Generating from manual prompt...');
      self.scrollToBottom();
      self._submitPaintJob(pos, neg, width, height, steps, cfg, manage_llama);
    });

    // Focus the input
    setTimeout(function() {
      var ta = overlay.querySelector('#paint-pos-prompt');
      if (ta) ta.focus();
    }, 100);
  },

  // ---- TTS Voice (generate speech for last assistant reply) ----
  ttsVoice: function() {
    var self = this;
    if (this.state.streaming) return;

    // Find the last assistant message with text content
    var lastText = '';
    for (var i = this.state.messages.length - 1; i >= 0; i--) {
      var m = this.state.messages[i];
      if (m.role === 'assistant' && m.content && m.content.trim()) {
        lastText = m.content.trim();
        break;
      }
    }
    if (!lastText) {
      showToast('No assistant reply to voice yet');
      return;
    }

    this.appendSystemMsg('🎤 Generating voice...');
    this.scrollToBottom();

    var bridgeUrl = getSettings().bridgeUrl || 'http://localhost:19250';
    fetch(bridgeUrl + '/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: lastText.substring(0, 500),
        lang: 'ja',
        mood: 'casual',
        character: this.state.currentCharId || 'natsume',
      }),
      signal: AbortSignal.timeout(5000),
    })
      .then(function(res) { return res.json(); })
      .then(function(data) {
        if (data.job_id) {
          self._pollTTS(data.job_id);
        } else {
          self.appendSystemMsg('🎤 TTS failed: ' + (data.error || 'unknown'));
          self.scrollToBottom();
        }
      })
      .catch(function(err) {
        self.appendSystemMsg('🎤 TTS error: ' + err.message);
        self.scrollToBottom();
      });
  },

  _pollTTS: function(jobId) {
    var self = this;
    var bridgeUrl = getSettings().bridgeUrl || 'http://localhost:19250';
    var attempt = 0;
    var maxAttempts = 120;

    var interval = setInterval(function() {
      attempt++;
      fetch(bridgeUrl + '/api/jobs/' + jobId, { signal: AbortSignal.timeout(3000) })
        .then(function(res) { return res.json(); })
        .then(function(job) {
          if (job.status === 'done') {
            clearInterval(interval);
            var audioSrc = self._resolveMediaPath(job.path);
            var el = document.createElement('div');
            el.className = 'msg-system tts-done';
            el.innerHTML = '🎤 Voice ready! <audio controls src="' + audioSrc + '"></audio>';
            self.$messages.appendChild(el);
            self.scrollToBottom();
            // Also save to messages if wanted
          } else if (job.status === 'failed') {
            clearInterval(interval);
            self.appendSystemMsg('🎤 TTS failed: ' + (job.error || 'unknown'));
            self.scrollToBottom();
          }
        })
        .catch(function() {});

      if (attempt >= maxAttempts) {
        clearInterval(interval);
        self.appendSystemMsg('🎤 TTS timed out');
        self.scrollToBottom();
      }
    }, 3000);
  },
  // ---- Streaming TTS + Live2D Lip-Sync ----
  ttsStreaming: function() {
    var self = this;
    if (this.state.streaming || this.state.ttsStreaming) return;
    if (!this._hasTTSForCurrentChar()) {
      showToast('This character has no TTS voice model yet');
      return;
    }

    // Find the last assistant message, extract only the last 1-2 sentences
    var lastText = '';
    for (var i = this.state.messages.length - 1; i >= 0; i--) {
      var m = this.state.messages[i];
      if (m.role === 'assistant' && m.content && m.content.trim()) {
        lastText = m.content.trim();
        break;
      }
    }
    if (!lastText) {
      showToast('No assistant reply to voice yet');
      return;
    }
    // Only use last 1-2 sentences (~100 chars max) for streaming TTS
    lastText = extractLastSentences(lastText, 2);
    var charCfg = getChar(charId);
    var lang = (charCfg && charCfg.ttsLang) || 'ja';
    var mood = (charCfg && charCfg.ttsMood) || 'casual';

    // Button feedback: active state
    this.state.ttsStreaming = true;
    this._updateTTSStreamingButton();

    this.appendSystemMsg('📢 Streaming TTS + Live2D Lip-Sync...');
    this.scrollToBottom();

    var bridgeUrl = getSettings().bridgeUrl || 'http://localhost:19250';

    // Send TTS job through bridge
    fetch(bridgeUrl + '/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: lastText.substring(0, 500),
        lang: lang,
        mood: mood,
        character: charId,
        live2d_sync: true,
      }),
      signal: AbortSignal.timeout(5000),
    })
      .then(function(res) { return res.json(); })
      .then(function(data) {
        if (data.job_id) {
          self._pollTTSLipSync(data.job_id);
        } else {
          self.state.ttsStreaming = false;
          self._updateTTSStreamingButton();
          self.appendSystemMsg('📢 Streaming TTS failed: ' + (data.error || 'unknown'));
          self.scrollToBottom();
        }
      })
      .catch(function(err) {
        self.state.ttsStreaming = false;
        self._updateTTSStreamingButton();
        self.appendSystemMsg('📢 Streaming TTS error: ' + err.message);
        self.scrollToBottom();
      });
  },

  _updateTTSStreamingButton: function() {
    var btn = document.getElementById('btn-tts-streaming');
    if (!btn) return;
    if (this.state.ttsStreaming) {
      btn.classList.add('active');
      btn.style.color = '#0f0';
      btn.style.borderColor = '#0f0';
      btn.title = 'Streaming TTS generating...';
    } else {
      btn.classList.remove('active');
      btn.style.color = '';
      btn.style.borderColor = '';
      btn.title = '流式TTS+Live2D口型同步';
    }
  },

  _hasTTSForCurrentChar: function() {
    var charId = this.state.currentCharId || 'natsume';
    // Characters with TTS ref_wavs: natsume, sakura, atori, enola
    var ttsChars = ['natsume', 'sakura', 'atori', 'enola'];
    return ttsChars.indexOf(charId) >= 0;
  },

  _updateStreamingTTSVisibility: function() {
    var btn = document.getElementById('btn-tts-streaming');
    if (!btn) return;
    if (this._hasTTSForCurrentChar()) {
      btn.style.display = '';
      btn.style.opacity = '1';
      btn.title = '流式TTS+Live2D口型同步';
    } else {
      btn.style.display = 'none';
      btn.style.opacity = '0.3';
      btn.title = 'No TTS model for this character';
    }
  },

  _updateMem0SubVisibility: function() {
    var enhanced = document.getElementById('chat-mem0-enhanced');
    var writeLabel = document.getElementById('toggle-mem0-write-label');
    var intervalRow = document.getElementById('mem0-interval-row');
    var show = enhanced && enhanced.checked;
    if (writeLabel) writeLabel.style.display = show ? '' : 'none';
    if (intervalRow) intervalRow.style.display = show ? '' : 'none';
  },

  _pollTTSLipSync: function(jobId) {
    var self = this;
    var bridgeUrl = getSettings().bridgeUrl || 'http://localhost:19250';
    var attempt = 0;
    var maxAttempts = 120;

    var interval = setInterval(function() {
      attempt++;
      fetch(bridgeUrl + '/api/jobs/' + jobId, { signal: AbortSignal.timeout(3000) })
        .then(function(res) { return res.json(); })
        .then(function(job) {
          if (job.status === 'done') {
            clearInterval(interval);
            self.state.ttsStreaming = false;
            self._updateTTSStreamingButton();
            var audioSrc = self._resolveMediaPath(job.path);

            // Trigger Live2D lip-sync via bridge's speak_audio API
            var encodedPath = encodeURIComponent(job.path);
            fetch('http://localhost:19200/api/speak_audio?action=start&audio_path=' + encodedPath + '&text=' + encodeURIComponent(job.text || ''), {
              signal: AbortSignal.timeout(5000),
            }).catch(function() {
              // Bridge might be offline, that's ok - audio still plays in chat
            });

            var el = document.createElement('div');
            el.className = 'msg-system tts-done';
            el.innerHTML = '📢 Lip-Sync active! <audio controls src="' + audioSrc + '"></audio>';
            self.$messages.appendChild(el);
            self.scrollToBottom();

            // Auto-stop lip-sync after estimated duration + 2s
            var estDuration = (job.duration_sec || 8) + 2;
            setTimeout(function() {
              fetch('http://localhost:19200/api/speak_audio?action=end', {
                signal: AbortSignal.timeout(5000),
              }).catch(function() {});
            }, estDuration * 1000);
          } else if (job.status === 'failed') {
            clearInterval(interval);
            self.state.ttsStreaming = false;
            self._updateTTSStreamingButton();
            self.appendSystemMsg('📢 Streaming TTS failed: ' + (job.error || 'unknown'));
            self.scrollToBottom();
          }
        })
        .catch(function() {});

      if (attempt >= maxAttempts) {
        clearInterval(interval);
        self.state.ttsStreaming = false;
        self._updateTTSStreamingButton();
        self.appendSystemMsg('📢 Streaming TTS timed out');
        self.scrollToBottom();
      }
    }, 3000);
  },
  autoPaint: function() {
    var self = this;
    if (this.state.streaming) return;
    if (this.state.messages.length === 0) {
      showToast('Start a conversation first so I know what to draw~');
      return;
    }

    var manage_llama = document.getElementById('btn-stop-llama').classList.contains('active');
    
    // Show generating indicator
    var indicatorMsg = manage_llama ? '🎨 Generating prompt (will stop llama after)...' : '🎨 Generating prompt...';
    self.appendSystemMsg(indicatorMsg);
    this.scrollToBottom();

    var charId = this.state.currentCharId || 'natsume';
    var recentMessages = this.state.messages.slice(-10);

    // Step 1: Ask daemon to generate a paint prompt via LLM (needs llama running)
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
          // Step 2: Now submit the job (bridge will stop llama if manage_llama is set)
          if (manage_llama) self.appendSystemMsg('🎨 Submitting paint job (stopping llama)...');
          self._submitPaintJob(data.prompt, data.negative || 'bad quality, worst quality, blurry, distorted, lowres, bad anatomy, extra fingers, watermark, text', undefined, undefined, undefined, undefined, manage_llama);
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

  _submitPaintJob: function(prompt, negative, width, height, steps, cfg, manage_llama) {
    var self = this;
    // manage_llama defaults to false (keep llama running)
    if (manage_llama === undefined) manage_llama = false;
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
      manage_llama: manage_llama,
    };

    // Remember the params on the instance so the resulting image message can
    // store them. Without this, an image message has no way to be re-rolled:
    // its `content` is empty, so the text-regenerate path has nothing to work
    // with. See _regeneratePaint().
    this._lastPaintParams = {
      positive: params.positive,
      negative: params.negative,
      width: params.width,
      height: params.height,
      steps: params.steps,
      cfg: params.cfg,
      checkpoint: params.checkpoint,
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
            // Save image as an assistant message with media field so it persists
            var imgPath = job.path;
            var imgSrc = self._resolveMediaPath(imgPath);
            var imgMsg = {
              role: 'assistant',
              content: '',
              media: imgPath,
              mediaType: 'image',
              time: self.formatTime(new Date()),
              paint: true,
              // Persist the generation params so this image can be re-rolled
              // later from its own regenerate button.
              paintParams: self._lastPaintParams || null
            };
            self.state.messages.push(imgMsg);
            // Persist: use tree-aware save to avoid losing paint images in tree sessions
            if (self._useTree && self.state.tree) {
              appendTreeNode(self.state.tree, imgMsg);
              self.state.messages = getChainMessages(self.state.tree);
              saveSessionTree(self.state.currentCharId, self.state.currentSessionId, self.state.tree);
            } else {
              saveChatHistory(self.state.currentCharId, self.state.currentSessionId, self.state.messages);
            }
            self.appendMessage(imgMsg);
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
    var self = this;
    var charId = this.state.currentCharId;
    var sessionId = this.state.currentSessionId;

    // Tree mode
    if (isTreeSession(charId, sessionId)) {
      this._useTree = true;
      var tree = this.state.tree = getSessionTree(charId, sessionId);
      if (!tree) {
        this.appendSystemMsg('Chat started - ' + this.formatDate(new Date()));
        this._userScrolledUp = false;
        this.scrollToBottom(true);
        return;
      }
      var chain = getCurrentChain(tree);
      var msgCount = chain.filter(function(n) { return n.role !== 'system'; }).length;
      if (msgCount === 0) {
        this.appendSystemMsg('Chat started - ' + this.formatDate(new Date()));
      } else {
        // Also store flat message array for API calls
        this.state.messages = getChainMessages(tree);
        this.appendSystemMsg('Resumed (' + msgCount + ' messages) - ' + this.formatDate(new Date()));
        chain.forEach(function(n, i) {
          if (n.role === 'system') return;
          // NOTE: do NOT filter on n.regenerated here. getCurrentChain() already
          // walks up from currentNodeId, so every node it returns is on the
          // ACTIVE path by definition. The `regenerated` flag only means "this
          // node was superseded at some point" -- it stays true forever, so
          // filtering on it made a re-selected branch render as an empty gap.
          // Skip only the streaming placeholder.
          if (n._pending) return;
          // Resolve local filesystem media paths to daemon proxy URLs
          if (n.media && !/^https?:\/\//.test(n.media)) {
            n.media = self._resolveMediaPath(n.media);
          }
          var el = self._renderTreeNode(n, i, tree);
          self.$messages.appendChild(el);
        });
      }
      this._userScrolledUp = false;
      this.scrollToBottom(true);
      return;
    }

    // Tree mode forced on for old sessions: migrate
    var settings = getSettings();
    if (settings.treeMode === 'on') {
      var store = loadStore();
      var s = (store.chats[charId] || {})[sessionId];
      if (s && s.messages && s.messages.length > 0) {
        var migrated = migrateToTree(s.messages);
        s.tree = migrated;
        s.messages = [];
        saveStore(store);
        // Reload with tree
        return this.loadHistory();
      }
    }

    // Flat message mode
    this._useTree = false;
    this.state.tree = null;
    var msgs = getChatHistory(charId, sessionId);
    this.state.messages = msgs.slice();
    if (msgs.length === 0) {
      this.appendSystemMsg('Chat started - ' + this.formatDate(new Date()));
    } else {
      this.appendSystemMsg('Resumed (' + msgs.length + ' messages) - ' + this.formatDate(new Date()));
      msgs.forEach(function(m, i) {
        if (!m.media && m.content && m.role === 'assistant') {
          var parsed = self._parseMediaFromText(m.content);
          if (parsed.mediaPath) {
            m.media = self._resolveMediaPath(parsed.mediaPath);
            m.content = parsed.cleanText;
            self.state.messages[i] = m;
          }
        }
        // Convert any local file path media to daemon proxy URL
        if (m.media && !/^https?:\/\//.test(m.media)) {
          m.media = self._resolveMediaPath(m.media);
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
    var charId = this.state.currentCharId;
    var sessionId = this.state.currentSessionId;
    var hasContent = this._useTree && this.state.tree
      ? treeNodeCount(this.state.tree) > 1
      : this.state.messages.length > 0;
    if (!hasContent) return;
    
    if (this._useTree && this.state.tree) {
      this.state.tree = migrateToTree([]);
      saveSessionTree(charId, sessionId, this.state.tree);
    } else {
      this.state.messages = [];
      saveChatHistory(charId, sessionId, []);
    }
    this.$messages.innerHTML = '';
    this.appendSystemMsg('Session reset - ' + this.formatTime(new Date()));
    showToast('Session reset');
    this.loadSessionsList();
  },

  clearMessages: function() {
    var charId = this.state.currentCharId;
    var sessionId = this.state.currentSessionId;
    if (this._useTree && this.state.tree) {
      this.state.tree = migrateToTree([]);
      saveSessionTree(charId, sessionId, this.state.tree);
    } else {
      this.state.messages = [];
      saveChatHistory(charId, sessionId, []);
    }
    this.$messages.innerHTML = '';
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
      s.reasoningEnabled = document.getElementById('setting-reasoning').checked;
      s.mem0Enhanced = document.getElementById('setting-mem0') ? document.getElementById('setting-mem0').checked : s.mem0Enhanced;
      s.mem0WriteEnabled = document.getElementById('setting-mem0-write') ? document.getElementById('setting-mem0-write').checked : s.mem0WriteEnabled;
      s.mem0WriteInterval = document.getElementById('setting-mem0-interval') ? parseInt(document.getElementById('setting-mem0-interval').value) || 10 : s.mem0WriteInterval;
      s.treeMode = document.getElementById('setting-tree-mode') ? document.getElementById('setting-tree-mode').value : (s.treeMode || 'auto');
      saveSettings(s);
      ApiClient.init(s.apiBase);
      Studio.bridgeUrl = s.bridgeUrl;
      overlay.classList.remove('open');
      // Refresh session after tree mode change
      self.loadHistory();
      showToast('Settings saved');
      // Sync chat toggle with settings
      var chatReasoningCheck = document.getElementById('chat-reasoning');
      var chatReasoningSwitch = document.getElementById('toggle-reasoning-switch');
      if (chatReasoningCheck) chatReasoningCheck.checked = s.reasoningEnabled;
      if (chatReasoningSwitch) chatReasoningSwitch.classList.toggle('on', s.reasoningEnabled);
      // Sync thinking mode
      var thinkingModeRow = document.getElementById('thinking-mode-row');
      var thinkingSelect = document.getElementById('thinking-mode-select');
      if (thinkingModeRow) thinkingModeRow.style.display = s.reasoningEnabled ? '' : 'none';
      if (thinkingSelect) thinkingSelect.value = s.thinkingMode || 'default';
      // Sync mem0 chat toggle
      var chatMem0Check = document.getElementById('chat-mem0-enhanced');
      var chatMem0Switch = document.getElementById('toggle-mem0-switch');
      var mem0WriteRow = document.getElementById('mem0-interval-row');
      if (chatMem0Check) chatMem0Check.checked = s.mem0Enhanced;
      if (chatMem0Switch) chatMem0Switch.classList.toggle('on', s.mem0Enhanced);
      UI._updateMem0SubVisibility();
      var chatMem0WriteCheck = document.getElementById('chat-mem0-write');
      var chatMem0WriteSwitch = document.getElementById('toggle-mem0-write-switch');
      if (chatMem0WriteCheck) chatMem0WriteCheck.checked = s.mem0WriteEnabled;
      if (chatMem0WriteSwitch) chatMem0WriteSwitch.classList.toggle('on', s.mem0WriteEnabled);
      var intervalInput = document.getElementById('mem0-write-interval');
      if (intervalInput) intervalInput.value = s.mem0WriteInterval || 10;
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

    // Settings reasoning toggle
    var settingReasoningCheck = document.getElementById('setting-reasoning');
    var settingReasoningToggle = document.getElementById('toggle-setting-reasoning-switch');
    var settingReasoningLabel = document.getElementById('toggle-setting-reasoning-label');
    if (settingReasoningLabel && settingReasoningCheck && settingReasoningToggle) {
      settingReasoningLabel.addEventListener('click', function() {
        settingReasoningCheck.checked = !settingReasoningCheck.checked;
        settingReasoningToggle.classList.toggle('on', settingReasoningCheck.checked);
      });
    }

    // Settings mem0 enhanced toggle
    var settingMem0Check = document.getElementById('setting-mem0');
    var settingMem0Toggle = document.getElementById('toggle-setting-mem0-switch');
    var settingMem0Label = document.getElementById('toggle-setting-mem0-label');
    if (settingMem0Label && settingMem0Check && settingMem0Toggle) {
      settingMem0Label.addEventListener('click', function() {
        settingMem0Check.checked = !settingMem0Check.checked;
        settingMem0Toggle.classList.toggle('on', settingMem0Check.checked);
      });
    }

    // Settings mem0 write toggle
    var settingMem0WriteCheck = document.getElementById('setting-mem0-write');
    var settingMem0WriteToggle = document.getElementById('toggle-setting-mem0-write-switch');
    var settingMem0WriteLabel = document.getElementById('toggle-setting-mem0-write-label');
    if (settingMem0WriteLabel && settingMem0WriteCheck && settingMem0WriteToggle) {
      settingMem0WriteLabel.addEventListener('click', function() {
        settingMem0WriteCheck.checked = !settingMem0WriteCheck.checked;
        settingMem0WriteToggle.classList.toggle('on', settingMem0WriteCheck.checked);
      });
    }

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
    var reasoningCheckbox = document.getElementById('setting-reasoning');
    var reasoningToggle = document.getElementById('toggle-setting-reasoning-switch');
    var overlay = document.getElementById('settings-overlay');

    if (apiBase) apiBase.value = s.apiBase || 'http://localhost:18789';
    if (bridgeUrl) bridgeUrl.value = s.bridgeUrl || 'http://localhost:19250';
    if (streamCheckbox) streamCheckbox.checked = s.streamEnabled !== false;
    if (streamToggle) streamToggle.classList.toggle('on', s.streamEnabled !== false);
    if (reasoningCheckbox) reasoningCheckbox.checked = s.reasoningEnabled !== false;
    if (reasoningToggle) reasoningToggle.classList.toggle('on', s.reasoningEnabled !== false);
    // Mem0 settings
    var mem0Check = document.getElementById('setting-mem0');
    var mem0Toggle = document.getElementById('toggle-setting-mem0-switch');
    var mem0WriteCheck = document.getElementById('setting-mem0-write');
    var mem0WriteToggle = document.getElementById('toggle-setting-mem0-write-switch');
    var mem0Interval = document.getElementById('setting-mem0-interval');
    if (mem0Check) mem0Check.checked = s.mem0Enhanced === true;
    if (mem0Toggle) mem0Toggle.classList.toggle('on', s.mem0Enhanced === true);
    if (mem0WriteCheck) mem0WriteCheck.checked = s.mem0WriteEnabled === true;
    if (mem0WriteToggle) mem0WriteToggle.classList.toggle('on', s.mem0WriteEnabled === true);
    if (mem0Interval) mem0Interval.value = s.mem0WriteInterval || 10;
    // Tree mode
    var treeModeSelect = document.getElementById('setting-tree-mode');
    if (treeModeSelect) treeModeSelect.value = s.treeMode || 'auto';
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

  // ---- Memory Viewer ----
  _openMemoryViewer: function() {
    var self = this;
    var memViewerOverlay = document.getElementById('memory-viewer-overlay');
    var memViewerBody = document.getElementById('memory-viewer-body');
    var memViewerFooter = document.getElementById('memory-viewer-footer');
    var memViewerTitle = document.getElementById('memory-viewer-title');
    if (!memViewerOverlay) return;

    // Clear and show loading
    memViewerBody.innerHTML = '<div class="memory-viewer-loading">Loading memory...</div>';
    memViewerFooter.textContent = '';
    var memSource = getSettings().memorySource || 'mem0';
    memViewerTitle.textContent = memSource === 'mem0' ? '🧠 Mem0 记忆' : '🧠 OpenClaw 会话历史';

    // Open overlay
    memViewerOverlay.classList.add('open');

    // Fetch based on current memory source
    if (memSource === 'mem0') {
      // Use existing mem0 search
      var mem0Data = this._mem0SearchResult;
      if (mem0Data && mem0Data.length > 0) {
        self._renderMem0Viewer(mem0Data);
      } else {
        // Try to fetch from mem0 if cached result is empty
        memViewerBody.innerHTML = '<div class="memory-viewer-empty">No memories found in Mem0</div>';
      }
    } else {
      // Fetch session history from backend
      memViewerBody.innerHTML = '<div class="memory-viewer-loading">Loading session history...</div>';
      var limit = 20;
      fetch('http://localhost:19260/api/session-history?sessionKey=main&limit=' + limit)
        .then(function(r) { return r.json(); })
        .then(function(data) {
          if (data.ok && data.history && data.history.length > 0) {
            self._renderSessionViewer(data.history);
            memViewerFooter.textContent = 'Showing ' + data.history.length + ' of ' + limit + ' recent messages';
          } else {
            memViewerBody.innerHTML = '<div class="memory-viewer-empty">No session history available</div>';
            memViewerFooter.textContent = '';
          }
        })
        .catch(function(err) {
          memViewerBody.innerHTML = '<div class="memory-viewer-empty">Failed to load session history: ' + escapeHtml(err.message) + '</div>';
          memViewerFooter.textContent = '';
        });
    }
  },

  _renderMem0Viewer: function(results) {
    var memViewerBody = document.getElementById('memory-viewer-body');
    if (!memViewerBody) return;

    var html = '';
    results.forEach(function(mem) {
      var timeStr = mem.timestamp || '';
      if (timeStr) {
        try {
          var d = new Date(mem.timestamp);
          timeStr = d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0') + ' ' + String(d.getHours()).padStart(2,'0') + ':' + String(d.getMinutes()).padStart(2,'0');
        } catch(e) {}
      }
      html += '<div class="mem-entry">';
      if (timeStr) html += '<div class="mem-time">' + escapeHtml(timeStr) + '</div>';
      html += '<div class="mem-source">Mem0 · score: ' + (mem.score ? mem.score.toFixed(2) : 'N/A') + '</div>';
      html += '<div class="mem-content">' + escapeHtml(mem.content) + '</div>';
      html += '</div>';
    });

    memViewerBody.innerHTML = html;
  },

  _renderSessionViewer: function(history) {
    var memViewerBody = document.getElementById('memory-viewer-body');
    if (!memViewerBody) return;

    var html = '';
    // Reverse to show oldest first
    var reversed = history.slice().reverse();
    reversed.forEach(function(msg) {
      var roleClass = msg.role === 'user' ? 'user-msg' : 'assistant-msg';
      var roleLabel = msg.role === 'user' ? '👤 User' : '🤖 Assistant';
      var timeStr = msg.timestamp || '';
      if (timeStr) {
        try {
          var d = new Date(msg.timestamp);
          timeStr = d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0') + ' ' + String(d.getHours()).padStart(2,'0') + ':' + String(d.getMinutes()).padStart(2,'0');
        } catch(e) {}
      }
      var content = msg.content || '';
      if (content.length > 500) content = content.substring(0, 500) + '...';

      html += '<div class="mem-entry ' + roleClass + '">';
      if (timeStr) html += '<div class="mem-time">' + escapeHtml(timeStr) + '</div>';
      html += '<div class="mem-source">' + escapeHtml(roleLabel) + '</div>';
      html += '<div class="mem-content">' + escapeHtml(content) + '</div>';
      html += '</div>';
    });

    memViewerBody.innerHTML = html;
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
  initLangSwitch();
});

// ── Language Switch (dropdown) ──
function initLangSwitch() {
  var trigger = document.getElementById('lang-trigger');
  var dropdown = document.getElementById('lang-dropdown');
  var wrapper = document.getElementById('lang-switch');
  if (!trigger || !wrapper) return;

  // Toggle open/close
  trigger.addEventListener('click', function(e) {
    e.stopPropagation();
    wrapper.classList.toggle('open');
  });

  // Click outside closes
  document.addEventListener('click', function(e) {
    if (!wrapper.contains(e.target)) {
      wrapper.classList.remove('open');
    }
  });

  // Each lang button
  var btns = wrapper.querySelectorAll('.lang-btn');
  btns.forEach(function(btn) {
    btn.addEventListener('click', function() {
      var lang = this.dataset.lang;
      if (typeof setLang === 'function') {
        setLang(lang);
      }
      wrapper.classList.remove('open');
    });
  });

  // i18n.js already restores from localStorage on load
}

// ============================================================
// Helper: extract last N sentences from text
// Supports Chinese (。/！/？/…) and Japanese/English (./!/?) punctuation
// ============================================================
function extractLastSentences(text, count) {
  if (!text) return text;
  // Split by sentence-ending punctuation: Chinese + Japanese + English markers
  var sentences = text.split(/(?<=[。！？…、.!?\n])\s*/g).filter(function(s) { return s.trim().length > 0; });
  if (sentences.length <= count) return text;
  return sentences.slice(-count).join('').trim();
}
