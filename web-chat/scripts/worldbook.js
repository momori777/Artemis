// ============================================================
// worldbook.js — Per-entry worldbook (SillyTavern-style)
// Each entry: { id, key, content, priority, enabled, source }
// - key: short label (e.g. "Location: Tokyo")
// - content: the actual text to inject
// - priority: 0=off, 1=low, 2=medium, 3=high, 4=essential
// - enabled: whether this entry is currently active
// - source: "manual" | "import"
//
// Entries are sent to daemon as an array { entries: [...] }
// The daemon merges enabled entries into the system prompt.
// ============================================================

var WorldBook = {
  _entries: [],  // Array of { id, key, content, priority, enabled, source, updatedAt }

  // ── Priority labels ──
  _priorityLabel: function(p) {
    return { 0: 'Off', 1: '低', 2: '中', 3: '高', 4: '关键' }[p] || '中';
  },
  _priorityColor: function(p) {
    return { 0: '#555', 1: '#6b8f5a', 2: '#d4a017', 3: '#e85d4a', 4: '#c9302e' }[p] || '#6b8f5a';
  },

  init: function() {
    var self = this;
    self._load();
    self._updateUI();
    self._syncToDaemon();

    // Import button
    var importBtn = document.getElementById('btn-import-worldbook');
    if (importBtn) {
      importBtn.addEventListener('click', function() {
        self._openModal();
      });
    }

    // File input
    var fileInput = document.getElementById('import-worldbook-file');
    if (fileInput) {
      fileInput.setAttribute('multiple', 'multiple');
      fileInput.addEventListener('change', function() {
        var files = fileInput.files;
        if (files && files.length > 0) {
          var handled = 0;
          for (var i = 0; i < files.length; i++) {
            self._handleFile(files[i], function() {
              handled++;
              if (handled === files.length) {
                self._updateList();
                self._updateUI();
                self._syncToDaemon();
              }
            });
          }
        }
        fileInput.value = '';
      });
    }

    // Modal close
    var modal = document.getElementById('worldbook-modal');
    if (modal) {
      modal.addEventListener('click', function(e) {
        if (e.target === modal) self._closeModal();
      });
    }
    var closeBtn = document.getElementById('worldbook-modal-close');
    if (closeBtn) closeBtn.addEventListener('click', function() { self._closeModal(); });
    var cancelBtn = document.getElementById('worldbook-modal-cancel');
    if (cancelBtn) cancelBtn.addEventListener('click', function() { self._closeModal(); });

    // Drop zone
    var dropZone = document.getElementById('worldbook-drop-zone');
    if (dropZone) {
      dropZone.addEventListener('click', function() {
        document.getElementById('import-worldbook-file').click();
      });
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
        var files = e.dataTransfer && e.dataTransfer.files;
        if (files && files.length > 0) {
          var handled = 0;
          for (var i = 0; i < files.length; i++) {
            self._handleFile(files[i], function() {
              handled++;
              if (handled === files.length) {
                self._updateList();
                self._updateUI();
                self._syncToDaemon();
              }
            });
          }
        }
      });
    }

    // Remove all button
    var removeAllBtn = document.getElementById('btn-remove-all-worldbook');
    if (removeAllBtn) {
      removeAllBtn.addEventListener('click', function() {
        if (self._entries.length === 0) return;
        if (confirm('Remove ALL ' + self._entries.length + ' world book entries?')) {
          self.removeAll();
          self._updateList();
          self._updateUI();
          self._closeModal();
          UI.showToast('All world book entries removed', 'success');
        }
      });
    }

    // "New Entry" button
    var newEntryBtn = document.getElementById('btn-new-worldbook-entry');
    if (newEntryBtn) {
      newEntryBtn.addEventListener('click', function() {
        self._addEmptyEntry();
      });
    }

    // "Enable all" button
    var enableAllBtn = document.getElementById('btn-enable-all-worldbook');
    if (enableAllBtn) {
      enableAllBtn.addEventListener('click', function() {
        for (var i = 0; i < self._entries.length; i++) {
          self._entries[i].enabled = true;
        }
        self._save();
        self._updateList();
        self._updateUI();
        self._syncToDaemon();
        UI.showToast('All entries enabled', 'success');
      });
    }

    // "Disable all" button
    var disableAllBtn = document.getElementById('btn-disable-all-worldbook');
    if (disableAllBtn) {
      disableAllBtn.addEventListener('click', function() {
        for (var i = 0; i < self._entries.length; i++) {
          self._entries[i].enabled = false;
        }
        self._save();
        self._updateList();
        self._updateUI();
        self._syncToDaemon();
        UI.showToast('All entries disabled', 'info');
      });
    }
  },

  _load: function() {
    try {
      var raw = localStorage.getItem('ai-gf-worldbook-entries');
      if (raw) this._entries = JSON.parse(raw);
    } catch (e) { this._entries = []; }
  },

  _save: function() {
    try {
      localStorage.setItem('ai-gf-worldbook-entries', JSON.stringify(this._entries));
    } catch (e) {
      UI.showToast('World book entries too large for localStorage', 'error');
    }
  },

  _genId: function() {
    return 'wb-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
  },

  // ── CRUD ──

  addEntry: function(key, content, priority, enabled, source, id) {
    id = id || this._genId();
    var entry = {
      id: id,
      key: key || '',
      content: content || '',
      priority: Math.max(0, Math.min(4, priority || 2)),
      enabled: enabled !== false,
      source: source || 'manual',
      updatedAt: new Date().toISOString()
    };
    this._entries.push(entry);
    this._save();
    return entry;
  },

  updateEntry: function(id, updates) {
    for (var i = 0; i < this._entries.length; i++) {
      if (this._entries[i].id === id) {
        if (updates.key !== undefined) this._entries[i].key = updates.key;
        if (updates.content !== undefined) this._entries[i].content = updates.content;
        if (updates.priority !== undefined) this._entries[i].priority = Math.max(0, Math.min(4, updates.priority));
        if (updates.enabled !== undefined) this._entries[i].enabled = updates.enabled;
        this._entries[i].updatedAt = new Date().toISOString();
        this._save();
        return this._entries[i];
      }
    }
    return null;
  },

  toggleEntry: function(id) {
    for (var i = 0; i < this._entries.length; i++) {
      if (this._entries[i].id === id) {
        this._entries[i].enabled = !this._entries[i].enabled;
        this._entries[i].updatedAt = new Date().toISOString();
        this._save();
        this._updateList();
        this._updateUI();
        this._syncToDaemon();
        return this._entries[i].enabled;
      }
    }
    return null;
  },

  changePriority: function(id, newPriority) {
    return this.updateEntry(id, { priority: Math.max(0, Math.min(4, newPriority)) });
  },

  removeEntry: function(id) {
    var name = '';
    this._entries = this._entries.filter(function(e) {
      if (e.id === id) { name = e.key || 'Entry'; return false; }
      return true;
    });
    this._save();
    return name;
  },

  removeAll: function() {
    this._entries = [];
    this._save();
  },

  getAll: function() {
    return this._entries;
  },

  getEnabledCount: function() {
    var count = 0;
    for (var i = 0; i < this._entries.length; i++) {
      if (this._entries[i].enabled) count++;
    }
    return count;
  },

  count: function() {
    return this._entries.length;
  },

  // ── File import ──

  _handleFile: function(file, done) {
    var self = this;
    var reader = new FileReader();
    reader.onload = function(e) {
      var content = e.target.result;
      var ext = file.name.toLowerCase().split('.').pop();
      var name = file.name.replace(/\.[^.]+$/, '');

      if (ext === 'json') {
        try {
          var parsed = JSON.parse(content);
          // SillyTavern worldbook format: { lore: [{ key, content, ... }] }
          // or { worldbook: [...] }, { memory: [...] }
          var lore = parsed.lore || parsed.worldbook || parsed.world || parsed.memory || parsed.entries;
          if (Array.isArray(lore) && lore.length > 0) {
            var count = 0;
            for (var i = 0; i < lore.length; i++) {
              var item = lore[i];
              var key = item.key || item.name || ('Entry ' + (i + 1));
              var text = item.content || item.text || item.description || '';
              var pri = item.priority || 2;
              var enabled = item.enabled !== false;
              self.addEntry(key, text, pri, enabled, 'import-' + name);
              count++;
            }
            if (count > 0) {
              if (done) done();
              UI.showToast('Imported ' + count + ' entries from ' + name, 'success');
              return;
            }
          }
          // Fallback: try flat key-value pairs
          var parts = [];
          for (var key in parsed) {
            if (parsed.hasOwnProperty(key) && typeof parsed[key] === 'string') {
              parts.push({ key: key, content: parsed[key] });
            }
          }
          if (parts.length > 0) {
            for (var j = 0; j < parts.length; j++) {
              self.addEntry(parts[j].key, parts[j].content, 2, true, 'import-' + name);
            }
            if (done) done();
            return;
          }
          // Deep flatten
          var flat = self._flattenObject(parsed, '');
          if (flat.length > 0) {
            for (var k = 0; k < flat.length; k++) {
              self.addEntry(flat[k].key, flat[k].value, 2, true, 'import-' + name);
            }
            if (done) done();
            return;
          }
          // Last resort: treat as single chunk
          self.addEntry(name, JSON.stringify(parsed, null, 2), 2, true, 'import-' + name);
          if (done) done();
        } catch (e) {
          self.addEntry(name, content, 2, true, 'import-' + name);
          if (done) done();
        }
      } else if (ext === 'md' || ext === 'txt') {
        // Try to parse as key: value per line
        var lines = content.split('\n');
        var entryLines = [];
        for (var li = 0; li < lines.length; li++) {
          var line = lines[li].trim();
          if (!line || line.startsWith('#') || line.startsWith('---')) continue;
          // Look for "key: content" or "key:: content" or "key | content"
          var colonIdx = line.indexOf(':');
          var doubleCol = line.indexOf('::');
          var pipeIdx = line.indexOf('|');
          var sepIdx = -1;
          if (doubleCol > 0) sepIdx = doubleCol;
          else if (colonIdx > 0 && colonIdx < line.length - 1) sepIdx = colonIdx;
          else if (pipeIdx > 0) sepIdx = pipeIdx;

          if (sepIdx > 0 && sepIdx < line.length - 1) {
            var eKey = line.substring(0, sepIdx).trim();
            var eVal = line.substring(sepIdx + (line[sepIdx+1] === ':' ? 2 : 1)).trim();
            if (eKey && eVal) {
              entryLines.push({ key: eKey, content: eVal });
            }
          } else {
            // Blank line → new entry boundary
            if (line.length > 0) {
              entryLines.push({ key: 'Entry', content: line });
            }
          }
        }
        if (entryLines.length > 0) {
          for (var m = 0; m < entryLines.length; m++) {
            self.addEntry(entryLines[m].key, entryLines[m].content, 2, true, 'import-' + name);
          }
          if (done) done();
          return;
        }
        // Fallback: single chunk
        self.addEntry(name, content, 2, true, 'import-' + name);
        if (done) done();
      } else {
        // Plain text → single entry
        self.addEntry(name, content, 2, true, 'import-' + name);
        if (done) done();
      }
    };
    reader.readAsText(file, 'utf-8');
  },

  _flattenObject: function(obj, prefix) {
    var result = [];
    for (var key in obj) {
      if (!obj.hasOwnProperty(key)) continue;
      var fullKey = prefix ? prefix + '.' + key : key;
      if (typeof obj[key] === 'string') {
        result.push({ key: fullKey, value: obj[key] });
      } else if (typeof obj[key] === 'object' && obj[key] !== null && !Array.isArray(obj[key])) {
        result = result.concat(this._flattenObject(obj[key], fullKey));
      } else if (Array.isArray(obj[key])) {
        for (var i = 0; i < obj[key].length; i++) {
          if (typeof obj[key][i] === 'string') {
            result.push({ key: fullKey + '[' + i + ']', value: obj[key][i] });
          } else if (typeof obj[key][i] === 'object' && obj[key][i]) {
            result = result.concat(this._flattenObject(obj[key][i], fullKey + '[' + i + ']'));
          }
        }
      }
    }
    return result;
  },

  // ── Modal ──

  _openModal: function() {
    var modal = document.getElementById('worldbook-modal');
    if (modal) modal.classList.add('open');
    this._updateList();
  },

  _closeModal: function() {
    var modal = document.getElementById('worldbook-modal');
    if (modal) modal.classList.remove('open');
  },

  _addEmptyEntry: function() {
    this._editEntry(null);
  },

  _editEntry: function(id) {
    var existing = null;
    if (id) {
      for (var i = 0; i < this._entries.length; i++) {
        if (this._entries[i].id === id) { existing = this._entries[i]; break; }
      }
    }

    var editModal = document.getElementById('worldbook-edit-modal');
    if (!editModal) {
      editModal = document.createElement('div');
      editModal.id = 'worldbook-edit-modal';
      editModal.className = 'wb-edit-modal';
      editModal.innerHTML =
        '<div class="wb-edit-modal-panel">' +
          '<div class="wb-edit-modal-header">' +
            '<h3 id="wb-edit-title">New World Book Entry</h3>' +
            '<button class="wb-edit-modal-close" id="wb-edit-modal-close">&times;</button>' +
          '</div>' +
          '<div class="wb-edit-modal-body">' +
            '<div class="wb-edit-field">' +
              '<label class="wb-edit-label" for="wb-edit-key">Key (标题/关键词)</label>' +
              '<input type="text" id="wb-edit-key" class="wb-edit-input" placeholder="e.g. Location: Tokyo">' +
              '<span class="wb-edit-hint">Short label for this entry — helps identify each memory block</span>' +
            '</div>' +
            '<div class="wb-edit-field">' +
              '<label class="wb-edit-label" for="wb-edit-content">Content (内容)</label>' +
              '<textarea id="wb-edit-content" class="wb-edit-textarea" rows="6" placeholder="The actual text to inject into context..."></textarea>' +
            '</div>' +
            '<div class="wb-edit-row">' +
              '<div class="wb-edit-field wb-edit-field-half">' +
                '<label class="wb-edit-label" for="wb-edit-priority">Priority (权重)</label>' +
                '<select id="wb-edit-priority" class="wb-edit-select">' +
                  '<option value="0">0 — Off (关闭)</option>' +
                  '<option value="1">1 — Low (低)</option>' +
                  '<option value="2" selected>2 — Medium (中)</option>' +
                  '<option value="3">3 — High (高)</option>' +
                  '<option value="4">4 — Essential (关键)</option>' +
                '</select>' +
              '</div>' +
              '<div class="wb-edit-field wb-edit-field-half">' +
                '<label class="wb-edit-label" for="wb-edit-enabled">Enabled</label>' +
                '<select id="wb-edit-enabled" class="wb-edit-select">' +
                  '<option value="true" selected>✅ Enabled</option>' +
                  '<option value="false">❌ Disabled</option>' +
                '</select>' +
              '</div>' +
            '</div>' +
          '</div>' +
          '<div class="wb-edit-modal-footer">' +
            '<button class="btn-secondary" id="wb-edit-cancel">Cancel</button>' +
            '<button class="btn-primary" id="wb-edit-save">Save</button>' +
          '</div>' +
        '</div>';
      document.body.appendChild(editModal);

      var closeBtn = document.getElementById('wb-edit-modal-close');
      var cancelBtn = document.getElementById('wb-edit-cancel');
      if (closeBtn) closeBtn.addEventListener('click', function() { editModal.classList.remove('open'); });
      if (cancelBtn) cancelBtn.addEventListener('click', function() { editModal.classList.remove('open'); });
      editModal.addEventListener('click', function(e) { if (e.target === editModal) editModal.classList.remove('open'); });

      var saveBtn = document.getElementById('wb-edit-save');
      saveBtn.addEventListener('click', function() {
        var key = document.getElementById('wb-edit-key').value.trim();
        var content = document.getElementById('wb-edit-content').value;
        var priority = parseInt(document.getElementById('wb-edit-priority').value);
        var enabled = document.getElementById('wb-edit-enabled').value === 'true';
        if (!key) {
          UI.showToast('Please enter a key/title', 'error');
          return;
        }
        if (!content || !content.trim()) {
          UI.showToast('Please enter content', 'error');
          return;
        }
        if (id) {
          self.updateEntry(id, { key: key, content: content, priority: priority, enabled: enabled });
          UI.showToast('Entry updated', 'success');
        } else {
          self.addEntry(key, content, priority, enabled, 'manual');
          UI.showToast('Entry created', 'success');
        }
        self._updateList();
        self._updateUI();
        self._syncToDaemon();
        editModal.classList.remove('open');
      });
    }

    // Populate form if editing existing
    if (existing) {
      document.getElementById('wb-edit-title').textContent = 'Edit Entry';
      document.getElementById('wb-edit-key').value = existing.key || '';
      document.getElementById('wb-edit-content').value = existing.content || '';
      document.getElementById('wb-edit-priority').value = String(existing.priority || 2);
      document.getElementById('wb-edit-enabled').value = String(existing.enabled !== false);
    } else {
      document.getElementById('wb-edit-title').textContent = 'New World Book Entry';
      document.getElementById('wb-edit-key').value = '';
      document.getElementById('wb-edit-content').value = '';
      document.getElementById('wb-edit-priority').value = '2';
      document.getElementById('wb-edit-enabled').value = 'true';
    }

    editModal.classList.add('open');
  },

  _deleteEntry: function(id) {
    var entry = null;
    for (var i = 0; i < this._entries.length; i++) {
      if (this._entries[i].id === id) { entry = this._entries[i]; break; }
    }
    if (!entry || !confirm('Delete "' + (entry.key || 'Entry') + '"?')) return;
    var name = this.removeEntry(id);
    this._updateList();
    this._updateUI();
    this._syncToDaemon();
    UI.showToast('Removed: ' + name, 'success');
  },

  // ── UI Rendering ──

  _updateUI: function() {
    var btn = document.getElementById('btn-import-worldbook');
    var enabledCount = this.getEnabledCount();
    var total = this.count();
    if (btn) {
      if (total > 0) {
        btn.classList.add('worldbook-loaded');
        btn.title = enabledCount + '/' + total + ' entries enabled — click to manage';
      } else {
        btn.classList.remove('worldbook-loaded');
        btn.title = 'Import world book / lore';
      }
    }
  },

  _updateList: function() {
    var self = this;
    var status = document.getElementById('worldbook-status');
    var listContainer = document.getElementById('worldbook-list');
    var preview = document.getElementById('worldbook-preview');
    var previewText = document.getElementById('worldbook-preview-text');

    if (!listContainer) return;

    var totalCount = this._entries.length;
    var enabledCount = this.getEnabledCount();

    if (totalCount === 0) {
      if (status) {
        status.innerHTML = 'No world book entries. Click <strong>"New Entry"</strong> or <strong>drag files</strong> to add.';
        status.className = '';
      }
      listContainer.innerHTML = '';
      if (preview) preview.style.display = 'none';
      return;
    }

    if (status) {
      status.innerHTML = '✓ ' + enabledCount + '/' + totalCount + ' entries enabled';
      status.className = 'has-book';
    }

    // Sort: enabled first, then by priority desc, then by updatedAt desc
    var sorted = this._entries.slice().sort(function(a, b) {
      if (a.enabled !== b.enabled) return b.enabled ? 1 : -1;
      if (a.priority !== b.priority) return b.priority - a.priority;
      return new Date(b.updatedAt) - new Date(a.updatedAt);
    });

    var html = '';
    for (var i = 0; i < sorted.length; i++) {
      var e = sorted[i];
      var contentLen = (e.content || '').length;
      var contentPreview = (e.content || '').length > 120
        ? (e.content || '').substring(0, 120) + '...'
        : (e.content || '');
      var priColor = this._priorityColor(e.priority);
      var priLabel = this._priorityLabel(e.priority);
      var dateStr = new Date(e.updatedAt).toLocaleString();
      var icon = e.enabled ? 'ph-toggle-left' : 'ph-toggle-right';
      var iconClass = e.enabled ? '' : 'wb-entry-disabled';
      var disabledStyle = e.enabled ? '' : 'opacity:0.5;';

      html += '<div class="wb-entry" data-wb-id="' + e.id + '" style="' + disabledStyle + '">' +
        '<div class="wb-entry-header">' +
          '<span class="wb-entry-key" title="' + escapeHtml(e.key) + '">' + escapeHtml(e.key) + '</span>' +
          '<span class="wb-entry-priority" style="color:' + priColor + '" title="Priority ' + e.priority + '">' + priLabel + '</span>' +
        '</div>' +
        '<div class="wb-entry-content">' + escapeHtml(contentPreview) + '</div>' +
        '<div class="wb-entry-actions">' +
          '<button class="wb-action-btn wb-toggle-btn ' + (e.enabled ? 'wb-toggle-on' : '') + '" title="Toggle enable/disable" data-wb-id="' + e.id + '">' +
            '<i class="ph ' + icon + '"></i>' +
          '</button>' +
          '<button class="wb-action-btn wb-edit-btn" title="Edit" data-wb-id="' + e.id + '">' +
            '<i class="ph ph-pencil-simple"></i>' +
          '</button>' +
          '<button class="wb-action-btn wb-delete-btn" title="Delete" data-wb-id="' + e.id + '">' +
            '<i class="ph ph-trash"></i>' +
          '</button>' +
          '<span class="wb-entry-meta">' + contentLen + 'B · ' + dateStr + '</span>' +
        '</div>' +
      '</div>';
    }
    listContainer.innerHTML = html;

    // Toggle buttons
    listContainer.querySelectorAll('.wb-toggle-btn').forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        var id = btn.dataset.wbId;
        var state = self.toggleEntry(id);
        var icon = e.target.tagName === 'I' ? e.target.parentElement.querySelector('i') : btn.querySelector('i');
        if (icon) {
          icon.className = state ? 'ph ph-toggle-left' : 'ph ph-toggle-right';
        }
        btn.className = 'wb-action-btn wb-toggle-btn' + (state ? ' wb-toggle-on' : '');
      });
    });

    // Edit buttons
    listContainer.querySelectorAll('.wb-edit-btn').forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        var id = btn.dataset.wbId;
        self._editEntry(id);
      });
    });

    // Delete buttons
    listContainer.querySelectorAll('.wb-delete-btn').forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        var id = btn.dataset.wbId;
        self._deleteEntry(id);
      });
    });

    // Click to preview
    listContainer.querySelectorAll('.wb-entry').forEach(function(item) {
      item.addEventListener('click', function() {
        var id = item.dataset.wbId;
        self._showPreview(id);
      });
    });
  },

  _showPreview: function(id) {
    var entry = null;
    for (var i = 0; i < this._entries.length; i++) {
      if (this._entries[i].id === id) { entry = this._entries[i]; break; }
    }
    if (!entry) return;
    var preview = document.getElementById('worldbook-preview');
    var previewText = document.getElementById('worldbook-preview-text');
    var previewLabel = document.getElementById('worldbook-preview-label');
    if (previewLabel) previewLabel.textContent = '📖 ' + entry.key;
    if (preview) {
      preview.style.display = '';
      preview.style.borderLeft = '3px solid ' + this._priorityColor(entry.priority);
    }
    if (previewText) {
      var text = entry.content || '';
      previewText.textContent = text.length > 5000 ? text.slice(0, 5000) + '\n\n... (truncated)' : text;
    }
  },

  // ── Daemon sync — send entries as an array ──
  _syncToDaemon: function() {
    var self = this;
    var entries = [];
    for (var i = 0; i < this._entries.length; i++) {
      var e = this._entries[i];
      entries.push({
        id: e.id,
        key: e.key || '',
        content: e.content || '',
        priority: e.priority || 2,
        enabled: e.enabled !== false
      });
    }
    try {
      fetch('http://localhost:19260/api/worldbook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entries: entries }),
      }).catch(function() {});
    } catch (_) {}
  },
};

function escapeHtml(s) {
  if (!s) return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
