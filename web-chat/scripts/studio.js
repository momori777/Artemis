// ============================================================
// studio.js - Artemis Studio embedded in web-chat
// Bridges to Artemis Bridge API (localhost:19250)
// ============================================================

var Studio = {
  bridgeUrl: 'http://localhost:19250',
  polling: {},

  init: function() {
    var self = this;
    this.bridgeUrl = getSettings().bridgeUrl || 'http://localhost:19250';
    this.initTabs();
    this.initTTs();
    this.initComfy();
    this.initDashboard();
    this.initBridgeStatus();
    this.initDebug();
  },

  initTabs: function() {
    var self = this;
    // Main tabs
    document.querySelectorAll('.main-tab').forEach(function(tab) {
      tab.addEventListener('click', function() {
        document.querySelectorAll('.main-tab').forEach(function(t) { t.classList.remove('active'); });
        document.querySelectorAll('.tab-panel').forEach(function(p) { p.classList.remove('active'); });
        tab.classList.add('active');
        document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
        if (tab.dataset.tab === 'studio') {
          self.checkBridge();
        }
      });
    });

    // Studio sub-tabs
    document.querySelectorAll('.studio-subtab').forEach(function(tab) {
      tab.addEventListener('click', function() {
        document.querySelectorAll('.studio-subtab').forEach(function(t) { t.classList.remove('active'); });
        document.querySelectorAll('.stab-panel').forEach(function(p) { p.classList.remove('active'); });
        tab.classList.add('active');
        var panel = document.getElementById('stab-' + tab.dataset.stab);
        if (panel) panel.classList.add('active');
      });
    });

    // Sidebar studio toggle
    document.getElementById('btn-studio-toggle').addEventListener('click', function() {
      document.querySelector('.main-tab[data-tab="studio"]').click();
    });

    document.getElementById('btn-bridge-refresh').addEventListener('click', function() {
      self.checkBridge();
    });
  },

  // ================================================================
  // Bridge Status
  // ================================================================
  checkBridge: function() {
    var self = this;
    var el = document.getElementById('bridge-status');
    el.textContent = 'Bridge: checking...';
    el.className = 'studio-bridge-status';

    fetch(this.bridgeUrl + '/api/status', { signal: AbortSignal.timeout(3000) })
      .then(function(res) { return res.json(); })
      .then(function(data) {
        var llamaStatus = data.llama || 'unknown';
        el.textContent = 'Bridge: online | LLM: ' + llamaStatus;
        el.className = 'studio-bridge-status online';
        self.updateLlamaStatus(llamaStatus);
        self.populateCharacters(data.characters || []);
      })
      .catch(function() {
        el.textContent = 'Bridge: offline';
        el.className = 'studio-bridge-status offline';
      });
  },

  updateLlamaStatus: function(status) {
    var el = document.getElementById('bridge-status');
    if (status === 'offline') {
      el.innerHTML = 'Bridge: online | LLM: <span class="llama-offline">offline</span> <button class="btn-llama-restart" id="btn-llama-restart" title="Restart LLM"><i class="ph ph-arrows-clockwise"></i> Restart</button>';
      setTimeout(function() {
        var btn = document.getElementById('btn-llama-restart');
        if (btn) {
          btn.addEventListener('click', function() {
            Studio.restartLlama();
          });
        }
      }, 100);
    }
  },

  restartLlama: function() {
    var self = this;
    var el = document.getElementById('bridge-status');
    el.textContent = 'Bridge: online | LLM: restarting...';
    el.className = 'studio-bridge-status online';

    fetch(this.bridgeUrl + '/api/restart-llama', {
      method: 'POST',
      signal: AbortSignal.timeout(300000),
    })
      .then(function(res) { return res.json(); })
      .then(function(data) {
        if (data.ok) {
          showToast('LLM restarted!');
        } else {
          showToast('LLM restart failed: ' + (data.error || 'unknown'));
        }
        self.checkBridge();
      })
      .catch(function(err) {
        showToast('LLM restart error: ' + err.message);
        self.checkBridge();
      });
  },

  initBridgeStatus: function() {
    this.checkBridge();
  },

  populateCharacters: function(chars) {
    var sel = document.getElementById('tts-character');
    if (!sel) return;
    sel.innerHTML = chars.map(function(c) {
      return '<option value="' + c + '">' + c.charAt(0).toUpperCase() + c.slice(1) + '</option>';
    }).join('');
  },

  // ================================================================
  // TTS
  // ================================================================
  initTTs: function() {
    var self = this;
    document.getElementById('btn-tts-generate').addEventListener('click', function() {
      self.ttsGenerate();
    });
  },

  ttsGenerate: function() {
    var self = this;
    var text = document.getElementById('tts-text').value.trim();
    if (!text) { showToast('Please enter text'); return; }

    var lang = document.getElementById('tts-lang').value;
    var mood = document.getElementById('tts-mood').value;
    var character = document.getElementById('tts-character').value;

    var btn = document.getElementById('btn-tts-generate');
    btn.disabled = true;
    btn.innerHTML = '<i class="ph ph-spinner"></i> Synthesizing...';

    var progress = document.getElementById('tts-progress');
    var fill = document.getElementById('tts-progress-fill');
    var textEl = document.getElementById('tts-progress-text');
    progress.style.display = 'block';
    fill.style.width = '10%';
    textEl.textContent = 'Queued...';

    fetch(this.bridgeUrl + '/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text, lang: lang, mood: mood, character: character }),
      signal: AbortSignal.timeout(5000),
    })
      .then(function(res) { return res.json(); })
      .then(function(data) {
        if (data.job_id) {
          fill.style.width = '20%';
          textEl.textContent = 'Processing...';
          self.pollJob(data.job_id, 'tts');
        } else {
          throw new Error(data.error || 'Unknown error');
        }
      })
      .catch(function(err) {
        progress.style.display = 'none';
        btn.disabled = false;
        btn.innerHTML = '<i class="ph ph-microphone"></i> Synthesize';
        showToast('TTS failed: ' + err.message);
      });
  },

  // ================================================================
  // ComfyUI
  // ================================================================
  initComfy: function() {
    var self = this;
    document.getElementById('btn-comfy-generate').addEventListener('click', function() {
      self.comfyGenerate();
    });

    // Llama management toggle in ComfyUI panel
    var llamaToggleLabel1 = document.getElementById('toggle-llama-manage-label');
    var llamaToggleCheck1 = document.getElementById('comfy-manage-llama');
    var llamaToggleSwitch1 = document.getElementById('toggle-llama-manage-switch');
    if (llamaToggleLabel1 && llamaToggleCheck1 && llamaToggleSwitch1) {
      llamaToggleLabel1.addEventListener('click', function() {
        llamaToggleCheck1.checked = !llamaToggleCheck1.checked;
        if (llamaToggleCheck1.checked) {
          llamaToggleSwitch1.classList.add('on');
        } else {
          llamaToggleSwitch1.classList.remove('on');
        }
      });
    }

    // Quick presets
    this.loadComfyPresets();
  },

  loadComfyPresets: function() {
    var presets = [
      { name: 'Natsume', prompt: 'masterpiece, best quality, 1girl, natsume, white hair, red eyes, school uniform, standing, cherry blossom, soft lighting, detailed' },
      { name: 'Sakura', prompt: 'masterpiece, best quality, 1girl, sakura, silver pink hair, light blue eyes, school uniform, serious expression, moonlight' },
      { name: 'Atori', prompt: 'masterpiece, best quality, 1girl, atori, silver hair, red eyes, white dress, barefoot, seaside sunset, warm light, detailed' },
      { name: 'Enola', prompt: 'masterpiece, best quality, 1girl, enola, brown hair, gentle smile, casual clothes, soft lighting, warm atmosphere' },
    ];

    var row = document.getElementById('comfy-presets');
    row.innerHTML = presets.map(function(p) {
      return '<button class="preset-btn" data-prompt="' + p.prompt.replace(/"/g, '&quot;') + '">' + p.name + '</button>';
    }).join('');

    row.querySelectorAll('.preset-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        document.getElementById('comfy-pos').value = btn.dataset.prompt;
      });
    });
  },

  comfyGenerate: function() {
    var self = this;
    var positive = document.getElementById('comfy-pos').value.trim();
    if (!positive) { showToast('Please enter a positive prompt'); return; }

    var params = {
      positive: positive,
      negative: document.getElementById('comfy-neg').value.trim(),
      width: parseInt(document.getElementById('comfy-width').value) || 1200,
      height: parseInt(document.getElementById('comfy-height').value) || 1500,
      steps: parseInt(document.getElementById('comfy-steps').value) || 30,
      cfg: parseFloat(document.getElementById('comfy-cfg').value) || 6.0,
      checkpoint: document.getElementById('comfy-ckpt').value,
      manage_llama: document.getElementById('comfy-manage-llama').checked,
    };

    var btn = document.getElementById('btn-comfy-generate');
    btn.disabled = true;
    btn.innerHTML = '<i class="ph ph-spinner"></i> Generating...';

    var progress = document.getElementById('comfy-progress');
    var fill = document.getElementById('comfy-progress-fill');
    var textEl = document.getElementById('comfy-progress-text');
    progress.style.display = 'block';
    fill.style.width = '5%';
    textEl.textContent = 'Queued...';

    fetch(this.bridgeUrl + '/api/comfyui', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
      signal: AbortSignal.timeout(5000),
    })
      .then(function(res) { return res.json(); })
      .then(function(data) {
        if (data.job_id) {
          fill.style.width = '10%';
          textEl.textContent = 'Processing...';
          self.pollJob(data.job_id, 'comfy');
        } else {
          throw new Error(data.error || 'Unknown error');
        }
      })
      .catch(function(err) {
        progress.style.display = 'none';
        btn.disabled = false;
        btn.innerHTML = '<i class="ph ph-image"></i> Generate';
        showToast('ComfyUI failed: ' + err.message);
      });
  },

  // ================================================================
  // Job polling
  // ================================================================
  pollJob: function(jobId, type) {
    var self = this;
    var fillId = type === 'tts' ? 'tts-progress-fill' : 'comfy-progress-fill';
    var textId = type === 'tts' ? 'tts-progress-text' : 'comfy-progress-text';
    var btnId = type === 'tts' ? 'btn-tts-generate' : 'btn-comfy-generate';
    var previewId = type === 'tts' ? 'tts-preview' : 'comfy-preview';
    var progressId = type === 'tts' ? 'tts-progress' : 'comfy-progress';

    var attempt = 0;
    var maxAttempts = 120; // 120 * 3s = 6min for comfyui

    var interval = setInterval(function() {
      attempt++;
      var fill = document.getElementById(fillId);
      var progress = Math.min(10 + (attempt / maxAttempts) * 80, 90);
      if (fill) fill.style.width = progress + '%';

      fetch(self.bridgeUrl + '/api/jobs/' + jobId, { signal: AbortSignal.timeout(3000) })
        .then(function(res) { return res.json(); })
        .then(function(job) {
          var textEl = document.getElementById(textId);
          if (job.status === 'done') {
            clearInterval(interval);
            if (fill) fill.style.width = '100%';
            if (textEl) textEl.textContent = 'Done (' + Math.round(job.elapsed || 0) + 's)';
            self.showResult(type, job.path);
            self.resetButton(type);
            setTimeout(function() {
              var p = document.getElementById(progressId);
              if (p) p.style.display = 'none';
            }, 2000);
          } else if (job.status === 'failed') {
            clearInterval(interval);
            if (textEl) textEl.textContent = 'Failed: ' + (job.error || '');
            self.resetButton(type);
            showToast(type.toUpperCase() + ' failed');
          } else {
            var elapsed = Math.round(job.elapsed || (attempt * 3));
            if (textEl) textEl.textContent = 'Processing... (' + elapsed + 's)';
          }
        })
        .catch(function() {
          // bridge may be slow, keep polling
        });

      if (attempt >= maxAttempts) {
        clearInterval(interval);
        var textEl = document.getElementById(textId);
        if (textEl) textEl.textContent = 'Timeout';
        self.resetButton(type);
        showToast(type.toUpperCase() + ' timed out');
      }
    }, 3000);
  },

  showResult: function(type, filePath) {
    var previewId = type === 'tts' ? 'tts-preview' : 'comfy-preview';
    var preview = document.getElementById(previewId);
    if (!preview) return;

    preview.innerHTML = '';

    if (type === 'tts') {
      // Audio player
      var container = document.createElement('div');
      container.style.display = 'flex';
      container.style.flexDirection = 'column';
      container.style.alignItems = 'center';
      container.style.justifyContent = 'center';
      container.style.flex = '1';
      container.style.width = '100%';

      var label = document.createElement('p');
      label.textContent = filePath.split(/[\\/]/).pop();
      label.style.color = 'var(--text-secondary)';
      label.style.fontSize = '12px';
      label.style.marginBottom = '12px';
      container.appendChild(label);

      var audio = document.createElement('audio');
      audio.controls = true;
      audio.src = this.bridgeUrl + '/api/media/' + filePath.replace(/\\/g, '/');
      audio.style.width = '90%';
      container.appendChild(audio);
      preview.appendChild(container);
    } else {
      // Image
      var imgUrl = this.bridgeUrl + '/api/media/' + filePath.replace(/\\/g, '/');
      var img = document.createElement('img');
      img.src = imgUrl;
      img.style.width = '100%';
      img.style.height = '100%';
      img.style.objectFit = 'contain';
      img.style.cursor = 'pointer';
      img.addEventListener('click', function() { window.open(imgUrl, '_blank'); });
      preview.appendChild(img);

      // Action buttons
      var actions = document.createElement('div');
      actions.className = 'preview-actions';
      var openBtn = document.createElement('button');
      openBtn.className = 'preview-action';
      openBtn.innerHTML = '<i class="ph ph-arrows-out"></i>';
      openBtn.title = 'Open full size';
      openBtn.addEventListener('click', function() { window.open(imgUrl, '_blank'); });
      actions.appendChild(openBtn);
      preview.appendChild(actions);
    }
  },

  resetButton: function(type) {
    var btnId = type === 'tts' ? 'btn-tts-generate' : 'btn-comfy-generate';
    var btn = document.getElementById(btnId);
    if (!btn) return;
    btn.disabled = false;
    if (type === 'tts') {
      btn.innerHTML = '<i class="ph ph-microphone"></i> Synthesize';
    } else {
      btn.innerHTML = '<i class="ph ph-image"></i> Generate';
    }
  },

  // ================================================================
  // Dashboard (embedded, uses daemon API on port 19260)
  // ================================================================
  dashboardUrl: 'http://localhost:19260',

  initDashboard: function() {
    var self = this;
    var btnStart = document.getElementById('btn-dash-start');
    var btnStop = document.getElementById('btn-dash-stop');
    var dashWebchat = document.getElementById('dash-open-webchat');
    if (btnStart) btnStart.addEventListener('click', function() { self.callDaemon('start'); });
    if (btnStop) btnStop.addEventListener('click', function() {
      if (!confirm('Stop all services?')) return;
      self.callDaemon('stop');
    });
    if (dashWebchat) dashWebchat.addEventListener('click', function(e) {
      e.preventDefault();
      document.querySelector('.main-tab[data-tab="chat"]').click();
    });

    self.refreshDashboard();
    setInterval(function() { self.refreshDashboard(); }, 10000);
  },

  callDaemon: function(cmd) {
    var self = this;
    var log = document.getElementById('dash-log');
    log.textContent = cmd === 'start' ? 'Starting all services...' : 'Stopping all services...';
    fetch(this.dashboardUrl + '/api/' + cmd, { method: 'POST', signal: AbortSignal.timeout(5000) })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        log.textContent = JSON.stringify(data.results || data.message || data);
        setTimeout(function() { self.refreshDashboard(); }, 3000);
        setTimeout(function() { self.refreshDashboard(); }, 8000);
      })
      .catch(function(err) {
        log.textContent = 'Error: ' + err.message;
      });
  },

  refreshDashboard: function() {
    var self = this;
    var list = document.getElementById('dash-services');
    if (!list) return;
    list.innerHTML = '<div style="padding:16px;text-align:center;color:var(--text-muted);font-size:13px">Loading...</div>';

    var xhr = new XMLHttpRequest();
    xhr.open('GET', this.dashboardUrl + '/api/status', true);
    xhr.timeout = 8000;
    xhr.onload = function() {
      if (xhr.status !== 200) {
        list.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:13px">Daemon error: HTTP ' + xhr.status + '</div>';
        return;
      }
      try {
        var services = JSON.parse(xhr.responseText);
      } catch(e) {
        list.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:13px">Invalid response</div>';
        return;
      }
      if (!Array.isArray(services) || services.length === 0) {
        list.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:13px">No services registered</div>';
        return;
      }
      list.innerHTML = services.map(function(s) {
        var cls = s.online ? 'online' : 'offline';
        var icon = s.online ? 'ph ph-check-circle' : 'ph ph-circle';
        var btns = '';
        if (s.online) {
          btns = '<button class="dash-service-action" title="Stop" onclick="Studio.stopDaemonService(\'' + s.name + '\')"><i class="ph ph-stop-circle"></i></button>';
          btns += '<button class="dash-service-action" title="Restart" onclick="Studio.restartDaemonService(\'' + s.name + '\')"><i class="ph ph-arrows-clockwise"></i></button>';
        } else {
          btns = '<button class="dash-service-action" title="Start" onclick="Studio.startDaemonService(\'' + s.name + '\')"><i class="ph ph-play-circle"></i></button>';
        }
        return '<div class="dash-service-row">' +
          '<i class="dash-service-status ' + cls + ' ' + icon + '"></i>' +
          '<span class="dash-service-name">' + s.name + '</span>' +
          '<span class="dash-service-port">:' + s.port + '</span>' +
          btns +
        '</div>';
      }).join('');
    };
    xhr.onerror = function() {
      list.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:13px">Daemon not reachable at ' + self.dashboardUrl + '</div>';
    };
    xhr.ontimeout = function() {
      list.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:13px">Daemon timeout at ' + self.dashboardUrl + '</div>';
    };
    xhr.send();
  },

  restartDaemonService: function(name) {
    var self = this;
    var log = document.getElementById('dash-log');
    log.textContent = 'Restarting ' + name + '...';
    var url = this.dashboardUrl + '/api/restart-service?name=' + encodeURIComponent(name);
    fetch(url, { signal: AbortSignal.timeout(5000) })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        log.textContent = name + ': ' + (data.result || 'ok');
        setTimeout(function() { self.refreshDashboard(); }, 2000);
      })
      .catch(function(err) {
        log.textContent = 'Error: ' + err.message;
      });
  },

  stopDaemonService: function(name) {
    var self = this;
    var log = document.getElementById('dash-log');
    log.textContent = 'Stopping ' + name + '...';
    fetch(this.dashboardUrl + '/api/stop-service', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name }),
      signal: AbortSignal.timeout(10000),
    })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        log.textContent = name + ': ' + (data.result || data.error || 'done');
        setTimeout(function() { self.refreshDashboard(); }, 2000);
      })
      .catch(function(err) {
        log.textContent = 'Error: ' + err.message;
      });
  },

  startDaemonService: function(name) {
    var self = this;
    var log = document.getElementById('dash-log');
    log.textContent = 'Starting ' + name + '...';
    fetch(this.dashboardUrl + '/api/start-service', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name }),
      signal: AbortSignal.timeout(120000),
    })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        log.textContent = name + ': ' + (data.result || data.error || 'done');
        setTimeout(function() { self.refreshDashboard(); }, 2000);
      })
      .catch(function(err) {
        log.textContent = 'Error: ' + err.message;
      });
  },

  // ============================================================
  // Model Debug
  // ============================================================
  initDebug: function() {
    var self = this;

    document.getElementById('debug-logprobs').addEventListener('change', function() {
      var field = document.getElementById('debug-top-logprobs-field');
      field.style.display = this.checked ? 'block' : 'none';
    });

    document.getElementById('btn-debug-send').addEventListener('click', function() {
      self.sendDebug();
    });

    document.getElementById('btn-debug-clear').addEventListener('click', function() {
      document.getElementById('debug-output').innerHTML = '<span class="debug-placeholder">Cleared</span>';
    });

    // Enter to send in user textarea
    document.getElementById('debug-user').addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        self.sendDebug();
      }
    });
  },

  sendDebug: function() {
    var self = this;
    var systemText = document.getElementById('debug-system').value.trim();
    var userText = document.getElementById('debug-user').value.trim();
    if (!userText) return;

    var output = document.getElementById('debug-output');
    var progress = document.getElementById('debug-progress');
    var fill = document.getElementById('debug-progress-fill');
    var progressText = document.getElementById('debug-progress-text');

    progress.hidden = false;
    fill.style.width = '30%';
    progressText.textContent = 'Sending...';

    var messages = [];
    if (systemText) {
      messages.push({ role: 'system', content: systemText });
    }
    messages.push({ role: 'user', content: userText });

    var body = {
      model: document.getElementById('debug-model').value,
      messages: messages,
      stream: false,
      max_tokens: parseInt(document.getElementById('debug-max-tokens').value) || 2048,
      temperature: parseFloat(document.getElementById('debug-temp').value) || 0.7,
      top_p: parseFloat(document.getElementById('debug-top-p').value) || 0.9,
      top_k: parseInt(document.getElementById('debug-top-k').value) || 40,
      frequency_penalty: parseFloat(document.getElementById('debug-freq-pen').value) || 0.0,
      presence_penalty: parseFloat(document.getElementById('debug-pres-pen').value) || 0.0,
      repeat_penalty: parseFloat(document.getElementById('debug-repeat-pen').value) || 1.1,
      min_p: parseFloat(document.getElementById('debug-min-p').value) || 0.05,
    };

    var logprobs = document.getElementById('debug-logprobs').checked;
    if (logprobs) {
      body.logprobs = true;
      body.top_logprobs = parseInt(document.getElementById('debug-top-logprobs').value) || 3;
    }

    fill.style.width = '60%';
    progressText.textContent = 'Waiting for response...';

    fetch('http://127.0.0.1:19260/api/debug-llama', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(60000),
    })
      .then(function(r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function(data) {
        fill.style.width = '100%';
        progressText.textContent = 'Done';

        var showRaw = document.getElementById('debug-toggle-raw').checked;
        if (showRaw) {
          output.textContent = JSON.stringify(data, null, 2);
        } else {
          var text = '';
          var usage = data.usage || {};
          var c = (data.choices || [])[0] || {};
          if (c.message && c.message.content) {
            text = c.message.content;
          } else if (c.text) {
            text = c.text;
          }
          var formatted = text;
          if (usage.prompt_tokens || usage.completion_tokens) {
            formatted += '\n\n---\nPrompt: ' + (usage.prompt_tokens || '?') + ' | Completion: ' + (usage.completion_tokens || '?') + ' | Total: ' + (usage.total_tokens || '?') + ' tokens';
          }
          if (c.finish_reason) {
            formatted += '\nStop reason: ' + c.finish_reason;
          }
          output.innerHTML = '<div style="color:var(--text);white-space:pre-wrap;word-break:break-word">' + self._escapeHtml(formatted) + '</div>';
        }

        setTimeout(function() { progress.hidden = true; }, 800);
      })
      .catch(function(err) {
        fill.style.width = '0%';
        progressText.textContent = 'Error: ' + err.message;
        output.textContent = '';
        output.innerHTML = '<div style="color:#e74c3c;font-weight:600">⚠ ' + self._escapeHtml(err.message) + '</div>';
        setTimeout(function() { progress.hidden = true; }, 2000);
      });
  },

  _escapeHtml: function(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  },
};
