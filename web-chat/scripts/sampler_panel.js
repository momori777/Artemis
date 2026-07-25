/**
 * sampler_panel.js — SillyTavern-style sampler control panel for Artemis Chat
 * Injects a right-side drawer with temperature/top_p/top_k/min_p etc.
 * Parameters persist in localStorage and apply to every chat message.
 * v3: Full i18n support via window.i18n()
 */

(function() {
  'use strict';

  var ST_KEY = 'artemis_sampler_panel';
  var DEFAULTS = {
    temperature: 0.7,    top_p: 0.9,    top_k: 40,    min_p: 0.05,
    freq_penalty: 0.0,   pres_penalty: 0.0,   repeat_penalty: 1.1,
    max_tokens: 4096,
    open: false,
    hr_recent_rounds: 4, hr_max_items: 10, hr_max_msgs: 24, hr_max_chars: 40000
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
    if (document.getElementById('sampler-panel')) return;
    var p = document.createElement('div');
    p.id = 'sampler-panel';
    p.style.cssText = 'position:fixed;top:0;right:0;width:300px;height:100vh;background:var(--bg-surface);border-left:1px solid var(--border-subtle);z-index:100;transform:translateX(100%);transition:transform .25s ease;display:flex;flex-direction:column;overflow:hidden;box-shadow:-4px 0 24px rgba(0,0,0,.3)';
    
    p.innerHTML = '<div style="display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid var(--border-subtle);flex-shrink:0">'+
      '<span style="font-size:13px;font-weight:600;color:var(--text-primary);font-family:var(--font-sans)"><i class="ph ph-sliders-horizontal"></i> <span data-i18n="sampler_title">Sampler + Headroom</span></span>'+
      '<div style="display:flex;gap:8px;align-items:center">'+
      '<button id="sampler-help-btn" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:14px;padding:2px 4px;border-radius:4px;transition:all .15s">\u2753</button>'+
      '<button id="sampler-panel-close" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:16px;padding:2px">\u2715</button>'+
      '</div>'+
      '</div>'+
      '<div style="flex:1;overflow-y:auto;padding:12px 16px" id="sampler-panel-body"></div>';

    document.body.appendChild(p);

    document.getElementById('sampler-panel-close').addEventListener('click', function() {
      _state.open = false; saveState();
      p.style.transform = 'translateX(100%)';
      var btn = document.getElementById('sampler-toggle');
      if (btn) btn.classList.remove('active');
    });

    document.getElementById('sampler-help-btn').addEventListener('click', function(e) {
      e.stopPropagation();
      showHelpPopup();
    });

    if (_state.open) { p.style.transform = 'translateX(0)'; }
    buildSliders();
    buildHelpPopup();
  }

  // ============================================================
  // Build slider rows
  // ============================================================
  function buildSliders() {
    var body = document.getElementById('sampler-panel-body');
    if (!body) return;
    body.innerHTML = '';

    var presets = [
      ['sampler_preset_rp',  {temp:0.90,top_p:0.95,top_k:40,min_p:0.08,rep_pen:1.10,freq_pen:0.05,pres_pen:0.0}],
      ['sampler_preset_creative', {temp:1.20,top_p:0.98,top_k:80,min_p:0.02,rep_pen:1.05,freq_pen:0.10,pres_pen:0.05}],
      ['sampler_preset_precise',  {temp:0.50,top_p:0.70,top_k:15,min_p:0.10,rep_pen:1.05,freq_pen:0.0,pres_pen:0.0}],
      ['sampler_preset_neutral',  {temp:0.70,top_p:0.85,top_k:30,min_p:0.05,rep_pen:1.08,freq_pen:0.0,pres_pen:0.0}],
      ['sampler_preset_coding',   {temp:0.30,top_p:0.60,top_k:10,min_p:0.15,rep_pen:1.02,freq_pen:0.0,pres_pen:0.0}]
    ];

    var presetRow = document.createElement('div');
    presetRow.style.cssText = 'display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid var(--border-subtle)';
    presets.forEach(function(entry) {
      var btn = document.createElement('button');
      btn.textContent = i18n(entry[0]);
      btn.setAttribute('data-i18n', entry[0]);
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
        if (typeof showToast === 'function') showToast(i18n('sampler_preset_toast') + ' ' + i18n(entry[0]));
      });
      presetRow.appendChild(btn);
    });
    body.appendChild(presetRow);

    var sliders = [
      {id:'temperature',   i18n:'sp_temp',            min:0, max:2, step:0.01, v:_state.temperature},
      {id:'top_p',         i18n:'sp_top_p',           min:0, max:1, step:0.01, v:_state.top_p},
      {id:'top_k',         i18n:'sp_top_k',           min:1, max:200, step:1,  v:_state.top_k, int:true},
      {id:'min_p',         i18n:'sp_min_p',           min:0, max:1, step:0.01, v:_state.min_p},
      {id:'repeat_penalty',i18n:'sp_rep_pen',         min:1, max:2, step:0.01, v:_state.repeat_penalty},
      {id:'freq_penalty',  i18n:'sp_freq_pen',        min:-2, max:2, step:0.01,v:_state.freq_penalty},
      {id:'pres_penalty',  i18n:'sp_pres_pen',        min:-2, max:2, step:0.01,v:_state.pres_penalty},
      {id:'max_tokens',    i18n:'sp_max_tokens',      min:64, max:32768, step:64, v:_state.max_tokens, int:true}
    ];

    sliders.forEach(function(s) {
      var row = document.createElement('div');
      row.style.cssText = 'margin-bottom:10px';

      var header = document.createElement('div');
      header.style.cssText = 'display:flex;justify-content:space-between;align-items:center;margin-bottom:2px';
      header.innerHTML = '<span style="font-size:11px;color:var(--text-secondary);font-family:var(--font-sans)">'+i18n(s.i18n)+'</span>'+
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

    // ── Divider ──
    var div = document.createElement('div');
    div.style.cssText = 'border-top:1px solid var(--border-subtle);margin:8px 0;padding-top:4px';
    div.innerHTML = '<span style="font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--text-muted);font-weight:600" data-i18n="sampler_headroom_label">\uD83E\uDDE0 Headroom</span>';
    body.appendChild(div);

    var hrParams = [
      {id:'hr_recent_rounds', label:'sampler_hr_recent',  hint:'sampler_hr_recent_hint',  min:1, max:20,  step:1, v:_state.hr_recent_rounds, int:true},
      {id:'hr_max_items',    label:'sampler_hr_items',    hint:'sampler_hr_items_hint',   min:3, max:30,  step:1, v:_state.hr_max_items, int:true},
      {id:'hr_max_msgs',     label:'sampler_hr_msgs',     hint:'sampler_hr_msgs_hint',    min:4, max:100, step:1, v:_state.hr_max_msgs, int:true},
      {id:'hr_max_chars',    label:'sampler_hr_chars',    hint:'sampler_hr_chars_hint',   min:4000, max:200000, step:1000, v:_state.hr_max_chars, int:true}
    ];

    hrParams.forEach(function(p) {
      var row = document.createElement('div');
      row.style.cssText = 'margin-bottom:8px';

      var header = document.createElement('div');
      header.style.cssText = 'display:flex;justify-content:space-between;align-items:center;margin-bottom:1px';
      header.innerHTML = '<span style="font-size:10px;color:var(--text-secondary);font-family:var(--font-sans)">'+i18n(p.label)+
        ' <span style="color:var(--text-muted);opacity:0.6">'+i18n(p.hint)+'</span></span>';

      var inp = document.createElement('input');
      inp.type = 'range';
      inp.min = p.min; inp.max = p.max; inp.step = p.step;
      inp.value = p.v;
      inp.style.cssText = 'width:100%;height:3px;-webkit-appearance:none;appearance:none;background:var(--bg-overlay);border-radius:2px;outline:none;cursor:pointer';
      inp.addEventListener('input', function() {
        var val = p.int ? Math.round(parseFloat(this.value)) : parseFloat(this.value);
        _state[p.id] = val;
        saveState();
      });

      var wrapper = document.createElement('div');
      wrapper.style.cssText = 'display:flex;align-items:center;gap:8px';
      
      var badge = document.createElement('span');
      badge.id = 'hr-badge-'+p.id;
      badge.style.cssText = 'font-size:10px;font-family:var(--font-mono);color:var(--success);min-width:40px;text-align:right';
      badge.textContent = p.int ? Math.round(p.v) : p.v.toFixed(1);

      inp.addEventListener('input', function() {
        var val = p.int ? Math.round(parseFloat(inp.value)) : parseFloat(inp.value);
        badge.textContent = val;
      });

      wrapper.appendChild(inp);
      wrapper.appendChild(badge);
      row.appendChild(header);
      row.appendChild(wrapper);
      body.appendChild(row);
    });

    var resetBtn = document.createElement('button');
    resetBtn.textContent = i18n('sampler_hr_reset');
    resetBtn.setAttribute('data-i18n', 'sampler_hr_reset');
    resetBtn.style.cssText = 'padding:4px 10px;border-radius:12px;border:1px solid var(--border-subtle);background:transparent;color:var(--text-muted);font-size:10px;cursor:pointer;margin-top:4px;transition:all .15s;font-family:var(--font-sans)';
    resetBtn.addEventListener('mouseenter', function() { resetBtn.style.background='var(--bg-elevated)'; resetBtn.style.color='var(--danger)'; });
    resetBtn.addEventListener('mouseleave', function() { resetBtn.style.background='transparent'; resetBtn.style.color='var(--text-muted)'; });
    resetBtn.addEventListener('click', function() {
      _state.hr_recent_rounds = 4;
      _state.hr_max_items = 10;
      _state.hr_max_msgs = 24;
      _state.hr_max_chars = 40000;
      saveState();
      buildSliders();
      var p2 = document.getElementById('sampler-panel');
      if (p2 && _state.open) p2.style.transform = 'translateX(0)';
      if (typeof showToast === 'function') showToast(i18n('sampler_hr_reset_toast'));
    });
    body.appendChild(resetBtn);
  }

  function syncAllSliders() {
    buildSliders();
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
    btn.title = i18n('sampler_toggle_title');
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

  window.getHeadroomConfig = function() {
    return {
      recent_full_rounds: _state.hr_recent_rounds || 4,
      max_items_after_crush: _state.hr_max_items || 10,
      max_messages: _state.hr_max_msgs || 24,
      max_chars: _state.hr_max_chars || 40000,
      first_fraction: 0.3,
      last_fraction: 0.15,
      system_always_keep: true,
      variance_threshold: 2.0,
      min_tokens_to_crush: 150,
      ccr_ttl: 300,
      preserve_change_points: true,
      dedup_identical_items: true,
      use_feedback_hints: true,
    };
  };

  // ============================================================
  // Help Popup — full i18n
  // ============================================================
  function buildHelpPopup() {
    if (document.getElementById('sampler-help-popup')) return;

    var overlay = document.createElement('div');
    overlay.id = 'sampler-help-popup';
    overlay.style.cssText = 'display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.6);z-index:200;justify-content:center;align-items:flex-start;padding-top:60px';
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) overlay.style.display = 'none';
    });

    overlay.innerHTML = '<div style="background:var(--bg-surface);border:1px solid var(--border-subtle);border-radius:12px;width:520px;max-width:95vw;max-height:80vh;overflow-y:auto;padding:0">'+
      '<div style="display:flex;align-items:center;justify-content:space-between;padding:14px 18px;border-bottom:1px solid var(--border-subtle);position:sticky;top:0;background:var(--bg-surface);z-index:1">'+
      '<span style="font-size:14px;font-weight:600;color:var(--text-primary)" data-i18n="sampler_help_title">Sampler &amp; Headroom</span>'+
      '<button id="sampler-help-close" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:16px;padding:2px">\u2715</button>'+
      '</div>'+
      '<div style="padding:16px 18px;font-size:12px;line-height:1.7;color:var(--text-secondary)">'+

      '<div style="margin-bottom:16px">'+
      '<div style="font-weight:600;color:var(--text-primary);margin-bottom:6px" data-i18n="sampler_help_sampler">Sampler</div>'+
      '<table style="width:100%;border-collapse:collapse;font-size:11px">'+
      '<tr><td style="padding:4px 8px;color:var(--accent);white-space:nowrap;vertical-align:top">Temperature</td><td style="padding:4px 0">'+i18n('sampler_help_temp')+'</td></tr>'+
      '<tr><td style="padding:4px 8px;color:var(--accent);white-space:nowrap;vertical-align:top">Top P</td><td style="padding:4px 0">'+i18n('sampler_help_top_p')+'</td></tr>'+
      '<tr><td style="padding:4px 8px;color:var(--accent);white-space:nowrap;vertical-align:top">Top K</td><td style="padding:4px 0">'+i18n('sampler_help_top_k')+'</td></tr>'+
      '<tr><td style="padding:4px 8px;color:var(--accent);white-space:nowrap;vertical-align:top">Min P</td><td style="padding:4px 0">'+i18n('sampler_help_min_p')+'</td></tr>'+
      '<tr><td style="padding:4px 8px;color:var(--accent);white-space:nowrap;vertical-align:top">Repeat Penalty</td><td style="padding:4px 0">'+i18n('sampler_help_rep_pen')+'</td></tr>'+
      '<tr><td style="padding:4px 8px;color:var(--accent);white-space:nowrap;vertical-align:top">Freq Penalty</td><td style="padding:4px 0">'+i18n('sampler_help_freq_pen')+'</td></tr>'+
      '<tr><td style="padding:4px 8px;color:var(--accent);white-space:nowrap;vertical-align:top">Pres Penalty</td><td style="padding:4px 0">'+i18n('sampler_help_pres_pen')+'</td></tr>'+
      '<tr><td style="padding:4px 8px;color:var(--accent);white-space:nowrap;vertical-align:top">Max Tokens</td><td style="padding:4px 0">'+i18n('sampler_help_max_tk')+'</td></tr>'+
      '</table></div>'+

      '<div style="margin-bottom:16px">'+
      '<div style="font-weight:600;color:var(--text-primary);margin-bottom:6px" data-i18n="sampler_help_hr_title">Headroom</div>'+
      '<div style="margin-bottom:10px;padding:8px 12px;background:var(--accent-glow);border-radius:6px;border-left:3px solid var(--accent)">'+
      '<span style="font-weight:600;color:var(--accent)" data-i18n="sampler_help_hr_core">' + i18n('sampler_help_hr_core') + '</span>' +
      '<span data-i18n="sampler_help_hr_desc">' + i18n('sampler_help_hr_desc') + '</span>'+
      '</div>'+

      '<div style="font-weight:600;color:var(--text-primary);margin-bottom:4px" data-i18n="sampler_help_smartcrusher">SmartCrusher</div>'+
      '<ol style="margin-top:4px;padding-left:18px">'+
      '<li style="margin-bottom:2px" data-i18n="sampler_help_sc1">'+i18n('sampler_help_sc1')+'</li>'+
      '<li style="margin-bottom:2px" data-i18n="sampler_help_sc2">'+i18n('sampler_help_sc2')+'</li>'+
      '<li style="margin-bottom:2px" data-i18n="sampler_help_sc3">'+i18n('sampler_help_sc3')+'</li>'+
      '<li style="margin-bottom:2px" data-i18n="sampler_help_sc4">'+i18n('sampler_help_sc4')+'</li>'+
      '<li style="margin-bottom:2px" data-i18n="sampler_help_sc5">'+i18n('sampler_help_sc5')+'</li>'+
      '</ol>'+

      '<table style="width:100%;border-collapse:collapse;font-size:11px;margin-top:10px">'+
      '<tr><td style="padding:4px 8px;color:var(--success);white-space:nowrap;vertical-align:top"><span data-i18n="sampler_hr_recent">'+i18n('sampler_hr_recent')+'</span></td><td style="padding:4px 0">'+i18n('sampler_help_hr_r1')+'</td></tr>'+
      '<tr><td style="padding:4px 8px;color:var(--success);white-space:nowrap;vertical-align:top"><span data-i18n="sampler_hr_items">'+i18n('sampler_hr_items')+'</span></td><td style="padding:4px 0">'+i18n('sampler_help_hr_r2')+'</td></tr>'+
      '<tr><td style="padding:4px 8px;color:var(--success);white-space:nowrap;vertical-align:top"><span data-i18n="sampler_hr_msgs">'+i18n('sampler_hr_msgs')+'</span></td><td style="padding:4px 0">'+i18n('sampler_help_hr_r3')+'</td></tr>'+
      '<tr><td style="padding:4px 8px;color:var(--success);white-space:nowrap;vertical-align:top"><span data-i18n="sampler_hr_chars">'+i18n('sampler_hr_chars')+'</span></td><td style="padding:4px 0">'+i18n('sampler_help_hr_r4')+'</td></tr>'+
      '</table></div>'+

      '<div style="padding:10px 14px;background:var(--bg-elevated);border-radius:8px;margin-top:4px">'+
      '<span style="font-weight:600" data-i18n="sampler_help_tips">'+i18n('sampler_help_tips')+'</span><br>'+
      '<span data-i18n="sampler_help_tip1">'+i18n('sampler_help_tip1')+'</span><br>'+
      '<span data-i18n="sampler_help_tip2">'+i18n('sampler_help_tip2')+'</span><br>'+
      '<span data-i18n="sampler_help_tip3">'+i18n('sampler_help_tip3')+'</span><br>'+
      '<span data-i18n="sampler_help_tip4">'+i18n('sampler_help_tip4')+'</span><br>'+
      '<span style="font-size:10px;color:var(--text-muted);margin-top:4px;display:inline-block" data-i18n="sampler_help_footer">'+i18n('sampler_help_footer')+'</span>'+
      '</div>'+

      '</div></div>';

    document.body.appendChild(overlay);

    document.getElementById('sampler-help-close').addEventListener('click', function() {
      overlay.style.display = 'none';
    });
  }

  function showHelpPopup() {
    var popup = document.getElementById('sampler-help-popup');
    if (!popup) { buildHelpPopup(); popup = document.getElementById('sampler-help-popup'); }
    if (popup) { popup.style.display = 'flex'; }
  }

  // ============================================================
  // Rebuild hook — called by setLang() in i18n.js
  // ============================================================
  window._samplerPanelRebuild = function() {
    buildSliders();
    // Remove old help popup so it gets rebuilt with new language
    var old = document.getElementById('sampler-help-popup');
    if (old) old.remove();
    buildHelpPopup();
    var toggle = document.getElementById('sampler-toggle');
    if (toggle) toggle.title = i18n('sampler_toggle_title');
  };

  // ============================================================
  // Init on DOM ready
  // ============================================================
  function init() {
    buildPanel();
    injectToggle();
    console.log('[sampler_panel] Initialized (v3 + i18n)');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
