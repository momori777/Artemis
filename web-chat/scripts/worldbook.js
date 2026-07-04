// ============================================================
// worldbook.js - Plural world books / lore (persisted in localStorage)
// Independent of character switching — follows user, not character.
// Synchronized to daemon via API for injection into system prompt.
// Supports multiple world books with batch management.
// ============================================================

var WorldBook = {
  _books: [],    // Array of { id, name, content, type, updatedAt }

  init: function() {
    var self = this;
    // Load from localStorage
    self._load();
    // Run initial UI check
    self._updateUI();
    // Sync existing world books to daemon on startup
    self._syncToDaemon();

    // Import button
    var importBtn = document.getElementById('btn-import-worldbook');
    if (importBtn) {
      importBtn.addEventListener('click', function() {
        self._openModal();
      });
    }

    // File input — supports multiple files
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
                UI.showToast('Imported ' + files.length + ' world book(s)', 'success');
              }
            });
          }
        }
        fileInput.value = '';
      });
    }

    // Modal
    var modal = document.getElementById('worldbook-modal');
    var closeBtn = document.getElementById('worldbook-modal-close');
    var cancelBtn = document.getElementById('worldbook-modal-cancel');
    if (modal) {
      modal.addEventListener('click', function(e) {
        if (e.target === modal) self._closeModal();
      });
    }
    if (closeBtn) closeBtn.addEventListener('click', function() { self._closeModal(); });
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
                UI.showToast('Imported ' + files.length + ' world book(s)', 'success');
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
        if (self._books.length === 0) return;
        if (confirm('Remove ALL ' + self._books.length + ' world book(s)? This is permanent.')) {
          self.removeAll();
          self._updateList();
          self._updateUI();
          self._closeModal();
          UI.showToast('All world books removed', 'success');
        }
      });
    }
  },

  _load: function() {
    try {
      var raw = localStorage.getItem('ai-gf-worldbooks');
      if (raw) this._books = JSON.parse(raw);
    } catch (e) { this._books = []; }
    // Migrate old single-worldbook format
    try {
      var old = localStorage.getItem('ai-gf-worldbook');
      if (old) {
        var oldData = JSON.parse(old);
        if (oldData && oldData.content) {
          this.add(oldData.name || 'Legacy World Book', oldData.content, oldData.type || 'text');
          localStorage.removeItem('ai-gf-worldbook');
          this._save();
        }
      }
    } catch (e) {}
  },

  _save: function() {
    try {
      localStorage.setItem('ai-gf-worldbooks', JSON.stringify(this._books));
    } catch (e) {
      UI.showToast('World books too large for localStorage — try removing some', 'error');
    }
  },

  _genId: function() {
    return 'wb-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 7);
  },

  // ---- CRUD ----
  add: function(name, content, type, id) {
    id = id || this._genId();
    // If same name exists, replace it
    var existingIdx = -1;
    for (var i = 0; i < this._books.length; i++) {
      if (this._books[i].name === name) { existingIdx = i; break; }
    }
    var entry = {
      id: id,
      name: name,
      content: content,
      type: type || 'text',
      updatedAt: new Date().toISOString()
    };
    if (existingIdx >= 0) {
      entry.id = this._books[existingIdx].id;
      this._books[existingIdx] = entry;
    } else {
      this._books.push(entry);
    }
    this._save();
    return entry;
  },

  removeOne: function(id) {
    var name = '';
    this._books = this._books.filter(function(b) {
      if (b.id === id) { name = b.name; return false; }
      return true;
    });
    this._save();
    return name;
  },

  removeAll: function() {
    this._books = [];
    this._save();
  },

  getAll: function() {
    return this._books;
  },

  hasBooks: function() {
    return this._books.length > 0;
  },

  count: function() {
    return this._books.length;
  },

  // ---- File handling ----
  _handleFile: function(file, done) {
    var self = this;
    var reader = new FileReader();
    reader.onload = function(e) {
      var content = e.target.result;
      var ext = file.name.toLowerCase().split('.').pop();
      var type = 'text';
      var name = file.name.replace(/\.[^.]+$/, '');

      if (ext === 'json') {
        type = 'json';
        try {
          var parsed = JSON.parse(content);
          if (typeof parsed === 'string') { content = parsed; type = 'text'; }
          else if (parsed.content) { content = parsed.content; if (parsed.name) name = parsed.name; }
          else if (parsed.text) { content = parsed.text; }
          else if (parsed.description) { content = parsed.description; }
          else if (parsed.lore || parsed.world || parsed.worldbook) {
            var lore = parsed.lore || parsed.world || parsed.worldbook;
            if (Array.isArray(lore)) {
              content = lore.map(function(e) { return (e.key || e.name || '') + ': ' + (e.content || e.text || ''); }).join('\n\n');
            } else if (typeof lore === 'string') {
              content = lore;
            } else { content = JSON.stringify(parsed, null, 2); }
          } else { content = JSON.stringify(parsed, null, 2); }
        } catch (_) { type = 'text'; }
      } else if (ext === 'md') {
        type = 'markdown';
      }

      self.add(name, content, type);
      if (done) done();
    };
    reader.readAsText(file, 'utf-8');
  },

  // ---- UI ----
  _openModal: function() {
    var modal = document.getElementById('worldbook-modal');
    if (modal) modal.classList.add('open');
    this._updateList();
  },

  _closeModal: function() {
    var modal = document.getElementById('worldbook-modal');
    if (modal) modal.classList.remove('open');
  },

  _updateUI: function() {
    var btn = document.getElementById('btn-import-worldbook');
    var count = this.count();
    if (btn) {
      if (count > 0) {
        btn.classList.add('worldbook-loaded');
        btn.title = count + ' world book(s) loaded — click to manage';
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

    if (this._books.length === 0) {
      if (status) {
        status.textContent = 'No world books loaded.';
        status.className = '';
      }
      listContainer.innerHTML = '';
      if (preview) preview.style.display = 'none';
      return;
    }

    if (status) {
      status.textContent = '✓ ' + this._books.length + ' world book(s) loaded';
      status.className = 'has-book';
    }

    listContainer.innerHTML = this._books.map(function(b, i) {
      var size = (b.content || '').length;
      var sizeStr = size > 1000 ? Math.round(size / 1000) + 'KB' : size + 'B';
      var dateStr = new Date(b.updatedAt).toLocaleString();
      return '<div class="wb-item" data-wb-id="' + b.id + '">' +
        '<div class="wb-item-header">' +
          '<span class="wb-item-name">' + escapeHtml(b.name) + '</span>' +
          '<span class="wb-item-meta">' + sizeStr + ' · ' + b.type + '</span>' +
        '</div>' +
        '<div class="wb-item-actions">' +
          '<button class="wb-action-btn wb-preview-btn" title="Preview" data-wb-id="' + b.id + '"><i class="ph ph-eye"></i></button>' +
          '<button class="wb-action-btn wb-delete-btn" title="Delete" data-wb-id="' + b.id + '"><i class="ph ph-trash"></i></button>' +
        '</div>' +
      '</div>';
    }).join('');

    // Click handlers
    listContainer.querySelectorAll('.wb-preview-btn').forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        var id = btn.dataset.wbId;
        self._showPreview(id);
      });
    });
    listContainer.querySelectorAll('.wb-delete-btn').forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        var id = btn.dataset.wbId;
        var name = self.removeOne(id);
        self._updateList();
        self._updateUI();
        self._syncToDaemon();
        UI.showToast('Removed: ' + name, 'success');
      });
    });
    // Click item to preview
    listContainer.querySelectorAll('.wb-item').forEach(function(item) {
      item.addEventListener('click', function() {
        var id = item.dataset.wbId;
        self._showPreview(id);
      });
    });
  },

  _showPreview: function(id) {
    var book = null;
    for (var i = 0; i < this._books.length; i++) {
      if (this._books[i].id === id) { book = this._books[i]; break; }
    }
    if (!book) return;
    var preview = document.getElementById('worldbook-preview');
    var previewText = document.getElementById('worldbook-preview-text');
    var previewLabel = document.getElementById('worldbook-preview-label');
    if (previewLabel) previewLabel.textContent = '📖 ' + book.name;
    if (preview) preview.style.display = '';
    if (previewText) {
      var text = book.content || '';
      previewText.textContent = text.length > 3000 ? text.slice(0, 3000) + '\n\n... (truncated)' : text;
    }
  },

  // ---- Daemon sync (sends merged content) ----
  _mergeContent: function() {
    if (this._books.length === 0) return null;
    return this._books.map(function(b) {
      return '## ' + b.name + '\n\n' + (b.content || '');
    }).join('\n\n---\n\n');
  },

  _syncToDaemon: function() {
    var merged = this._mergeContent();
    try {
      fetch('http://localhost:19260/api/worldbook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          worldbook: merged ? { name: 'World Books (' + this._books.length + ')', content: merged } : null
        }),
      }).catch(function() {});
    } catch (_) {}
  },
};

function escapeHtml(s) {
  if (!s) return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
