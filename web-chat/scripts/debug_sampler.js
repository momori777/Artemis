/**
 * debug_sampler.js — SillyTavern-style sampler debug panel injector
 * Appends to existing Model Debug tab without touching index.html
 */
(function() {
  'use strict';

  // Make sure Studio exists
  if (typeof Studio === 'undefined') { console.error('Studio not found'); return; }

  // ============================================================
  // Sampler presets (SillyTavern-aligned)
  // ============================================================
  Studio.samplerPresets = {
    roleplay:  { temp:0.90, top_p:0.95, top_k:40, min_p:0.08, rep_pen:1.10, rep_range:512, rep_slope:0.70, freq_pen:0.05, pres_pen:0.0 },
    creative:  { temp:1.20, top_p:0.98, top_k:80, min_p:0.02, rep_pen:1.05, rep_range:256, rep_slope:0.90, freq_pen:0.10, pres_pen:0.05 },
    precise:   { temp:0.50, top_p:0.70, top_k:15, min_p:0.10, rep_pen:1.05, rep_range:1024, rep_slope:0.60, freq_pen:0.0, pres_pen:0.0 },
    neutral:   { temp:0.70, top_p:0.85, top_k:30, min_p:0.05, rep_pen:1.08, rep_range:512, rep_slope:0.80, freq_pen:0.0, pres_pen:0.0 },
    coding:    { temp:0.30, top_p:0.60, top_k:10, min_p:0.15, rep_pen:1.02, rep_range:2048, rep_slope:0.50, freq_pen:0.0, pres_pen:0.0 }
  };

  // ============================================================
  // Enhanced initDebug
  // ============================================================
  var _origInitDebug = Studio.initDebug;
  Studio.initDebug = function() {
    var self = this;
    _origInitDebug.call(this);

    // Populate debug model dropdown from backend (dynamic, no hardcoded model ids)
    if (typeof ApiClient !== 'undefined' && typeof ApiClient.fetchModels === 'function') {
      ApiClient.fetchModels().then(function(models) {
        var select = document.getElementById('debug-model');
        if (!select || !models || !models.length) return;
        var current = select.value;
        var html = models.map(function(m) {
          var sel = (current && m.id === current) ? ' selected' : '';
          return '<option value="' + m.id + '"' + sel + '>' + m.name + ' (' + m.id + ')</option>';
        }).join('');
        if (!html) return;
        select.innerHTML = html;
        // 保留用户已选中的模型（若还在列表中）
        var stillExists = models.some(function(m) { return m.id === current; });
        if (current && stillExists) select.value = current;
      }).catch(function() { /* keep hardcoded fallback options */ });
    }

    // Inject preset buttons
    this._injectPresets();
    // Enhance sliders
    this._enhanceSliders();
    // Add timing + export
    this._addExtras();
    // Load saved config
    this._loadSamplerConfig();
  };

  // ============================================================
  // Inject preset button row
  // ============================================================
  Studio._injectPresets = function() {
    var self = this;
    var left = document.querySelector('#stab-debug .studio-left');
    if (!left || document.getElementById('debug-presets-row')) return;

    var row = document.createElement('div');
    row.id = 'debug-presets-row';
    row.style.cssText = 'margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid var(--border-subtle)';
    row.innerHTML = '<label class="studio-label" style="margin-bottom:4px;display:block">Presets</label>';

    var btns = document.createElement('div');
    btns.className = 'preset-row';
    btns.id = 'debug-presets';
    btns.style.cssText = 'display:flex;flex-wrap:wrap;gap:4px';

    Object.keys(this.samplerPresets).forEach(function(name) {
      var btn = document.createElement('button');
      btn.className = 'preset-btn';
      btn.textContent = name.charAt(0).toUpperCase() + name.slice(1);
      btn.dataset.preset = name;
      btn.style.cssText = 'padding:3px 10px;border-radius:12px;border:1px solid var(--border-subtle);background:transparent;color:var(--text-muted);font-size:11px;cursor:pointer;transition:all .15s;font-family:var(--font-sans)';
      btn.addEventListener('mouseenter', function() { if (!this.classList.contains('active')) { this.style.background='var(--bg-elevated)'; this.style.color='var(--text-secondary)'; } });
      btn.addEventListener('mouseleave', function() { if (!this.classList.contains('active')) { this.style.background='transparent'; this.style.color='var(--text-muted)'; } });
      btn.addEventListener('click', function() {
        document.querySelectorAll('#debug-presets .preset-btn').forEach(function(b) { b.classList.remove('active'); b.style.background='transparent'; b.style.color='var(--text-muted)'; b.style.borderColor='var(--border-subtle)'; });
        this.classList.add('active');
        this.style.background = 'var(--accent-soft)';
        this.style.color = 'var(--accent)';
        this.style.borderColor = 'var(--accent)';
        self._applySamplerPreset(name);
      });
      btns.appendChild(btn);
    });

    row.appendChild(btns);
    // Insert at top of studio-left
    var firstField = left.querySelector('.studio-field');
    if (firstField) left.insertBefore(row, firstField);
    else left.appendChild(row);
  };

  // ============================================================
  // Enhance existing number inputs with range sliders
  // ============================================================
  Studio._enhanceSliders = function() {
    var self = this;
    // Add value labels next to each input
    ['debug-temp','debug-top-p','debug-min-p','debug-freq-pen','debug-pres-pen','debug-repeat-pen'].forEach(function(id) {
      var input = document.getElementById(id);
      if (!input || input.dataset.enhanced) return;
      input.dataset.enhanced = '1';
      var label = document.createElement('span');
      label.className = 'debug-val';
      label.style.cssText = 'font-size:10px;font-family:var(--font-mono);color:var(--accent);margin-left:4px;background:var(--accent-glow);padding:0 4px;border-radius:3px';
      input.parentNode.appendChild(label);
      input.addEventListener('input', function() { label.textContent = parseFloat(this.value).toFixed(2); });
      label.textContent = parseFloat(input.value).toFixed(2);
    });
    ['debug-top-k','debug-max-tokens'].forEach(function(id) {
      var input = document.getElementById(id);
      if (!input || input.dataset.enhanced) return;
      input.dataset.enhanced = '1';
      var label = document.createElement('span');
      label.className = 'debug-val';
      label.style.cssText = 'font-size:10px;font-family:var(--font-mono);color:var(--accent);margin-left:4px;background:var(--accent-glow);padding:0 4px;border-radius:3px';
      input.parentNode.appendChild(label);
      input.addEventListener('input', function() { label.textContent = parseInt(this.value)||0; });
      label.textContent = parseInt(input.value)||0;
    });
    // Also update from slider drags
    document.querySelectorAll('#stab-debug input[type="number"]').forEach(function(inp) {
      inp.addEventListener('input', function() {
        self._saveSamplerConfig();
      });
    });
  };

  // ============================================================
  // Add timing display + export button
  // ============================================================
  Studio._addExtras = function() {
    var self = this;
    // Timing span in output header
    var outputHeader = document.querySelector('#stab-debug .debug-output-header');
    if (outputHeader && !document.getElementById('debug-timing')) {
      var timing = document.createElement('span');
      timing.id = 'debug-timing';
      timing.style.cssText = 'font-size:10px;font-family:var(--font-mono);color:var(--text-muted)';
      outputHeader.appendChild(timing);
    }

    // Export button
    var actions = document.querySelector('#stab-debug .studio-actions');
    if (actions && !document.getElementById('btn-debug-export')) {
      var exp = document.createElement('button');
      exp.id = 'btn-debug-export';
      exp.className = 'btn-secondary';
      exp.innerHTML = '<i class="ph ph-download-simple"></i> Export';
      exp.style.cssText = 'margin-left:8px';
      exp.addEventListener('click', function() { self._exportSamplerConfig(); });
      actions.appendChild(exp);
    }

    // Rebind send button to enhanced version
    var sendBtn = document.getElementById('btn-debug-send');
    if (sendBtn && !sendBtn.dataset.enhanced) {
      sendBtn.dataset.enhanced = '1';
      var clone = sendBtn.cloneNode(true);
      sendBtn.parentNode.replaceChild(clone, sendBtn);
      clone.addEventListener('click', function() { self._sendDebugEnhanced(); });
    }
  };

  // ============================================================
  // Apply preset
  // ============================================================
  Studio._applySamplerPreset = function(name) {
    var p = this.samplerPresets[name];
    if (!p) return;
    var map = {
      'debug-temp':p.temp,'debug-top-p':p.top_p,'debug-top-k':p.top_k,'debug-min-p':p.min_p,
      'debug-repeat-pen':p.rep_pen,'debug-freq-pen':p.freq_pen,'debug-pres-pen':p.pres_pen
    };
    var self = this;
    Object.keys(map).forEach(function(id) {
      var el = document.getElementById(id);
      if (!el) return;
      el.value = map[id];
      el.dispatchEvent(new Event('input', {bubbles:true}));
      el.dispatchEvent(new Event('change', {bubbles:true}));
      // Refresh value label
      var lbl = el.nextElementSibling;
      if (lbl && lbl.classList.contains('debug-val')) {
        lbl.textContent = (id==='debug-top-k'||id==='debug-max-tokens') ? Math.round(map[id]) : map[id].toFixed(2);
      }
    });
    this._saveSamplerConfig();
    if (typeof showToast === 'function') showToast('Sampler preset: ' + name);
  };

  // ============================================================
  // Enhanced send with timing + token stats
  // ============================================================
  Studio._sendDebugEnhanced = function() {
    var self = this;
    var systemText = (document.getElementById('debug-system')?.value || '').trim();
    var userText = (document.getElementById('debug-user')?.value || '').trim();
    if (!userText) return;

    var output = document.getElementById('debug-output');
    var timing = document.getElementById('debug-timing');
    var progress = document.getElementById('debug-progress');
    var fill = document.getElementById('debug-progress-fill');
    var progressText = document.getElementById('debug-progress-text');

    if (progress) progress.hidden = false;
    if (fill) fill.style.width = '20%';
    if (progressText) progressText.textContent = 'Sending...';
    if (timing) timing.textContent = '';

    var messages = [];
    if (systemText) messages.push({role:'system',content:systemText});
    messages.push({role:'user',content:userText});

    var body = {
      model: (document.getElementById('debug-model')?.value) || ApiClient.getDefaultModel(),
      messages: messages,
      stream: false,
      max_tokens: parseInt((document.getElementById('debug-max-tokens')?.value)||2048),
      temperature: parseFloat((document.getElementById('debug-temp')?.value)||0.7),
      top_p: parseFloat((document.getElementById('debug-top-p')?.value)||0.9),
      top_k: parseInt((document.getElementById('debug-top-k')?.value)||40),
      min_p: parseFloat((document.getElementById('debug-min-p')?.value)||0.05),
      frequency_penalty: parseFloat((document.getElementById('debug-freq-pen')?.value)||0),
      presence_penalty: parseFloat((document.getElementById('debug-pres-pen')?.value)||0),
      repetition_penalty: parseFloat((document.getElementById('debug-repeat-pen')?.value)||1.1)
    };

    if (fill) fill.style.width = '50%';
    if (progressText) progressText.textContent = 'Waiting...';

    var startTime = Date.now();

    fetch('http://127.0.0.1:19260/api/debug-llama', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(body),
      signal:AbortSignal.timeout(120000)
    }).then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);return r.json();})
    .then(function(data){
      var elapsed = ((Date.now()-startTime)/1000).toFixed(1);
      if (fill) fill.style.width = '100%';
      if (progressText) progressText.textContent = 'Done in '+elapsed+'s';

      var c = (data.choices||[])[0]||{};
      var text = (c.message&&c.message.content) ? c.message.content : (c.text||'');
      var usage = data.usage||{};
      var stats = [];
      if (usage.prompt_tokens) stats.push('P:'+usage.prompt_tokens);
      if (usage.completion_tokens) {
        var tps = (usage.completion_tokens/parseFloat(elapsed)).toFixed(1);
        stats.push('C:'+usage.completion_tokens+' ('+tps+' tok/s)');
      }
      if (usage.total_tokens) stats.push('T:'+usage.total_tokens);
      if (c.finish_reason) stats.push('Stop:'+c.finish_reason);
      stats.push(elapsed+'s');

      if (timing) timing.textContent = stats.join(' | ');

      var showRaw = document.getElementById('debug-toggle-raw')?.checked;
      if (showRaw && output) {
        output.textContent = JSON.stringify(data,null,2);
      } else if (output) {
        output.innerHTML = '<div style="color:var(--text);white-space:pre-wrap;word-break:break-word">'+self._escapeHtml(text+(stats.length?'\n\n---\n'+stats.join(' | '):''))+'</div>';
      }

      setTimeout(function(){if(progress)progress.hidden=true},1500);
      self._saveSamplerConfig();
    }).catch(function(err){
      var elapsed = ((Date.now()-startTime)/1000).toFixed(1);
      if (fill) fill.style.width = '0%';
      if (progressText) progressText.textContent = 'Error: '+err.message;
      if (timing) timing.textContent = 'Failed after '+elapsed+'s';
      if (output) output.innerHTML = '<div style="color:#e74c3c;font-weight:600">⚠ '+self._escapeHtml(err.message)+'</div>';
      setTimeout(function(){if(progress)progress.hidden=true},2500);
    });
  };

  // ============================================================
  // Config persistence
  // ============================================================
  Studio._saveSamplerConfig = function() {
    var cfg = {};
    ['debug-model','debug-system','debug-temp','debug-top-p','debug-top-k','debug-min-p','debug-repeat-pen','debug-freq-pen','debug-pres-pen','debug-max-tokens'].forEach(function(id){
      var el = document.getElementById(id);
      if (el) cfg[id] = el.value;
    });
    try { localStorage.setItem('artemis_sampler_v3', JSON.stringify(cfg)); } catch(e){}
  };

  Studio._loadSamplerConfig = function() {
    var self = this;
    try {
      var raw = localStorage.getItem('artemis_sampler_v3');
      if (!raw) return;
      var cfg = JSON.parse(raw);
      Object.keys(cfg).forEach(function(k){
        var el = document.getElementById(k);
        if (!el) return;
        el.value = cfg[k];
        el.dispatchEvent(new Event('input', {bubbles:true}));
      });
    } catch(e){}
  };

  Studio._exportSamplerConfig = function() {
    var cfg = { model:(document.getElementById('debug-model')?.value), samplers:{} };
    ['temp','top_p','top_k','min_p','repeat_pen','freq_pen','pres_pen','max_tokens'].forEach(function(key){
      var el = document.getElementById('debug-'+key);
      if (el) cfg.samplers[key] = parseFloat(el.value);
    });
    var blob = new Blob([JSON.stringify(cfg,null,2)],{type:'application/json'});
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'sampler-config-'+new Date().toISOString().slice(0,10)+'.json';
    a.click();
    URL.revokeObjectURL(a.href);
    if (typeof showToast === 'function') showToast('Sampler config exported!');
  };

  console.log('[debug_sampler.js] Loaded — SillyTavern-style sampler presets + timing + persistence');
})();
