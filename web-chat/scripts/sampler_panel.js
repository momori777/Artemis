/**
 * sampler_panel.js — SillyTavern-style sampler control panel for Artemis Chat
 * Injects a right-side drawer with temperature/top_p/top_k/min_p etc.
 * Parameters persist in localStorage and apply to every chat message.
 * 
 * Usage: Add <script src="scripts/sampler_panel.js?v=1"></script> in index.html
 */
(function() {
  'use strict';

  var ST_KEY = 'artemis_sampler_panel';
  var DEFAULTS = {
    temperature: 0.7,    top_p: 0.9,    top_k: 40,    min_p: 0.05,
    freq_penalty: 0.0,   pres_penalty: 0.0,   repeat_penalty: 1.1,
    max_tokens: 4096,
    open: false
  };

  var _state = loadState();

  function loadState() {
    try { var s = JSON.parse(localStorage.getItem(ST_KEY)); return Object.assign({}, DEFAULTS, s||{}); }
    catch(e) { return Object.assign({}, DEFAULTS); }
  }
  function saveState() { try { localStorage.setItem(ST_KEY, JSON.stringify(_state)); } catch(e){} }

  // ============================================================
  // Build panel HTML
  // ============================================================
  function buildPanel() {
    var p = document.createElement('div');
    p.id = 'sampler-panel';
    p.style.cssText = 'position:fixed;top:0;right:0;width:300px;height:100vh;background:var(--bg-surface);border-left:1px solid var(--border-subtle);z-index:100;transform:translateX(100%);transition:transform .25s ease;display:flex;flex-direction:column;overflow:hidden;box-shadow:-4px 0 24px rgba(0,0,0,.3)';
    
    // Header
    p.innerHTML = '<div style="display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid var(--border-subtle);flex-shrink:0">'+
      '<span style="font-size:13px;font-weight:600;color:var(--text-primary);font-family:var(--font-sans)"><i class="ph ph-sliders-horizontal"></i> Sampler</span>'+
      '<button id="sampler-panel-close" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:16px;padding:2px">✕</button>'+
      '</div>'+
      '<div style="flex:1;overflow-y:auto;padding:12px 16px" id="sampler-panel-body"></div>';

    
    document.body.appendChild(p);

    // Close button
    document.getElementById('sampler-panel-close').addEventListener('click', function() {
      _state.open = false; saveState();
      p.style.transform = 'translateX(100%)';
      // Also untoggle the button
      var btn = document.getElementById('sampler-toggle');
      if (btn) btn.classList.remove('active');
    });

    if (_state.open) { p.style.transform = 'translateX(0)'; }
    buildSliders();
  }

  // ============================================================
  // Build slider rows
  // ============================================================
  function buildSliders() {
    var body = document.getElementById('sampler-panel-body');
    if (!body) return;
    body.innerHTML = '';

    // Preset row
    var presets = [
      ['Roleplay', {temp:0.90,top_p:0.95,top_k:40,min_p:0.08,rep_pen:1.10,freq_pen:0.05,pres_pen:0.0}],
      ['Creative', {temp:1.20,top_p:0.98,top_k:80,min_p:0.02,rep_pen:1.05,freq_pen:0.10,pres_pen:0.05}],
      ['Precise',  {temp:0.50,top_p:0.70,top_k:15,min_p:0.10,rep_pen:1.05,freq_pen:0.0,pres_pen:0.0}],
      ['Neutral',  {temp:0.70,top_p:0.85,top_k:30,min_p:0.05,rep_pen:1.08,freq_pen:0.0,pres_pen:0.0}],
      ['Coding',   {temp:0.30,top_p:0.60,top_k:10,min_p:0.15,rep_pen:1.02,freq_pen:0.0,pres_pen:0.0}]
    ];

    var presetRow = document.createElement('div');
    presetRow.style.cssText = 'display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid var(--border-subtle)';
    presets.forEach(function(entry) {
      var btn = document.createElement('button');
      btn.textContent = entry[0];
      btn.style.cssText = 'padding:3px 10px;border-radius:12px;border:1px solid var(--border-subtle);background:transparent;color:var(--text-muted);font-size:11px;cursor:pointer;transition:all .15s;font-family:var(--font-sans)';
      btn.addEventListener('mouseenter', function() { btn.style.background='var(--bg-elevated)'; btn.style.color='var(--text-secondary)'; });
      btn.addEventListener('mouseleave', function() { btn.style.background='transparent'; btn.style.color='var(--text-muted)'; });
      btn.addEventListener('click', function() {
        Object.assign(_state, {
          temperature: entry[1].temp, top_p: entry[1].top_p, top_k: entry[1].top_k,
          min_p: entry[1].min_p, repeat_penalty: entry[1].rep_pen,
          freq_penalty: entry[1].freq_pen, pres_penalty: entry[1].pres_pen
        });
        saveState();
        syncAllSliders();
        if (typeof showToast === 'function') showToast('Sampler preset: '+entry[0]);
      });
      presetRow.appendChild(btn);
    });
    body.appendChild(presetRow);

    // Sliders
    var sliders = [
      {id:'temperature',   label:'Temperature',       min:0, max:2, step:0.01, v:_state.temperature},
      {id:'top_p',         label:'Top P',              min:0, max:1, step:0.01, v:_state.top_p},
      {id:'top_k',         label:'Top K',              min:1, max:200, step:1,  v:_state.top_k, int:true},
      {id:'min_p',         label:'Min P',              min:0, max:1, step:0.01, v:_state.min_p},
      {id:'repeat_penalty',label:'Repeat Penalty',     min:1, max:2, step:0.01, v:_state.repeat_penalty},
      {id:'freq_penalty',  label:'Freq Penalty',       min:-2, max:2, step:0.01,v:_state.freq_penalty},
      {id:'pres_penalty',  label:'Pres Penalty',       min:-2, max:2, step:0.01,v:_state.pres_penalty},
      {id:'max_tokens',    label:'Max Tokens',         min:64, max:32768, step:64, v:_state.max_tokens, int:true}
    ];

    sliders.forEach(function(s) {
      var row = document.createElement('div');
      row.style.cssText = 'margin-bottom:10px';

      var header = document.createElement('div');
      header.style.cssText = 'display:flex;justify-content:space-between;align-items:center;margin-bottom:2px';
      header.innerHTML = '<span style="font-size:11px;color:var(--text-secondary);font-family:var(--font-sans)">'+s.label+'</span>'+
        '<span id="sampler-val-'+s.id+'" style="font-size:11px;font-family:var(--font-mono);color:var(--accent);background:var(--accent-glow);padding:0 4px;border-radius:3px">'+ (s.int ? Math.round(s.v) : s.v.toFixed(2)) +'</span>';

      var inp = document.createElement('input');
      inp.type = 'range';
      inp.min = s.min; inp.max = s.max; inp.step = s.step;
      inp.value = s.v;
      inp.style.cssText = 'width:100%;height:4px;-webkit-appearance:none;appearance:none;background:var(--bg-overlay);border-radius:2px;outline:none;cursor:pointer;margin-top:2px';
      inp.addEventListener('input', function() {
        var val = parseFloat(this.value);
        _state[s.id] = val;
        saveState();
        var disp = document.getElementById('sampler-val-'+s.id);
        if (disp) disp.textContent = s.int ? Math.round(val) : val.toFixed(2);
      });

      row.appendChild(header);
      row.appendChild(inp);
      body.appendChild(row);
    });
  }

  function syncAllSliders() {
    ['temperature','top_p','top_k','min_p','repeat_penalty','freq_penalty','pres_penalty','max_tokens'].forEach(function(k) {
      var inp = document.querySelector('#sampler-panel-body input[type=range]');
      // Rebuild entire panel for simplicity — could be optimized
    });
    buildSliders();
    // Re-open if was open
    if (_state.open) {
      var p = document.getElementById('sampler-panel');
      if (p) p.style.transform = 'translateX(0)';
    }
  }

  // ============================================================
  // Toggle button — injects into chat header
  // ============================================================
  function injectToggle() {
    if (document.getElementById('sampler-toggle')) return;
    var header = document.querySelector('.chat-header-actions');
    if (!header) return;
    var btn = document.createElement('button');
    btn.id = 'sampler-toggle';
    btn.className = 'header-action';
    btn.title = 'Sampler Parameters';
    btn.innerHTML = '<i class="ph ph-sliders-horizontal"></i>';
    btn.style.cssText = 'position:relative';
    btn.addEventListener('click', function() {
      _state.open = !_state.open;
      saveState();
      var p = document.getElementById('sampler-panel');
      if (p) {
        p.style.transform = _state.open ? 'translateX(0)' : 'translateX(100%)';
        btn.classList.toggle('active', _state.open);
        if (_state.open) buildSliders();
      }
    });
    header.insertBefore(btn, header.firstChild);
  }

  // ============================================================
  // API: get current sampler params for chat request
  // ============================================================
  window.getSamplerParams = function() {
    return {
      temperature: _state.temperature,
      top_p: _state.top_p,
      top_k: _state.top_k,
      min_p: _state.min_p,
      frequency_penalty: _state.freq_penalty,
      presence_penalty: _state.pres_penalty,
      repeat_penalty: _state.repeat_penalty,
      max_tokens: _state.max_tokens
    };
  };

  // ============================================================
  // Init on DOM ready
  // ============================================================
  function init() {
    buildPanel();
    injectToggle();
    console.log('[sampler_panel] Initialized');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
