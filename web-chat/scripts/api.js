// ============================================================
// api.js - Chat API client. Routes through daemon /api/chat proxy.
// Daemon reads openclaw.json providers and forwards to DeepSeek/Grok.
// ============================================================

var ApiClient = {
  base: 'http://localhost:19260',
  _modelsCache: null,
  _modelsPromise: null,

  init: function (apiBase) {
    this.base = apiBase || 'http://localhost:19260';
  },

  fetchModels: function () {
    var self = this;
    // Get models from daemon's gateway-config
    return fetch('http://localhost:19260/api/gateway-config', {
      signal: AbortSignal.timeout(5000),
    })
      .then(function (r) {
        if (!r.ok) throw new Error('Daemon returned ' + r.status);
        return r.json();
      })
      .then(function (cfg) {
        var models = (cfg.models || []).map(function (m) {
          return { id: m.id, name: m.name };
        });
        if (models.length === 0) {
          models = [{ id: 'local-model', name: 'Local (Llama)' }];
        }
        self._modelsCache = models;
        return models;
      })
      .catch(function () {
        self._modelsCache = [{ id: 'local-model', name: 'Local (Llama)' }];
        return self._modelsCache;
      });
  },

  /**
   * 返回默认模型 ID：优先已加载模型列表的第一个，
   * 否则回退到通用占位 'local-model'（daemon 会把 local/* 路由到本地 llama-server）。
   */
  getDefaultModel: function () {
    if (this._modelsCache && this._modelsCache.length) {
      return this._modelsCache[0].id;
    }
    return 'local-model';
  },

  /**
   * Stream chat via daemon proxy.
   */
  // Strip UI-only fields (media, paint, paintParams, time, ...) before sending.
  // The chat API only accepts role/content; leaking extra keys can make strict
  // backends reject the request.
  _cleanMessages: function (messages) {
    return (messages || []).map(function (m) {
      var out = { role: m.role, content: m.content || '' };
      // An image-only message has no text; give the model a short placeholder
      // so the turn is not silently empty.
      if (!out.content && m.paint) out.content = '[sent an image]';
      return out;
    });
  },

  chatStream: async function (messages, settings, onToken, onComplete, onError) {
    // If model is the fallback 'local-model' and we have real models cached,
    // use the first available one instead.
    var model = settings.model;
    if (model === 'local-model' && this._modelsCache && this._modelsCache.length > 0) {
      model = this._modelsCache[0].id;
    }
    if (!model) model = this.getDefaultModel();
    var characterId = settings.characterId || 'natsume';
    // Merge sampler params from sampler panel (SillyTavern-style permanent overrides)
    var samplerParams = {};
    if (typeof getSamplerParams === 'function') {
      samplerParams = getSamplerParams();
    }
    var body = {
      model: model,
      messages: this._cleanMessages(messages),
      stream: true,
      max_tokens: samplerParams.max_tokens || 4096,
      temperature: samplerParams.temperature ?? 0.7,
      top_p: samplerParams.top_p ?? 0.9,
      top_k: samplerParams.top_k ?? 40,
      min_p: samplerParams.min_p ?? 0.05,
      frequency_penalty: samplerParams.frequency_penalty ?? 0.0,
      presence_penalty: samplerParams.presence_penalty ?? 0.0,
      repeat_penalty: samplerParams.repeat_penalty ?? 1.1,
      characterId: characterId,
      reasoning: settings.reasoningEnabled !== false ? 'on' : 'off',
      thinkingMode: settings.thinkingMode || 'default',
      mem0Enhanced: settings.mem0Enhanced === true,
      mem0WriteEnabled: settings.mem0WriteEnabled === true,
      mem0WriteInterval: settings.mem0WriteInterval || 10,
      language: settings.language || 'zh',
    };
    // Headroom 配置（前端面板调参）
    if (typeof getHeadroomConfig === 'function') {
      body.headroom_config = getHeadroomConfig();
    }
    if (settings.systemPrompt) body.systemPrompt = settings.systemPrompt;
    try {
      var res = await fetch('http://localhost:19260/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(180000),
      });

      if (!res.ok) {
        var errText = '';
        try { var ej = await res.json(); errText = ej.error || res.statusText; } catch (_) {}
        // Auto retry on llama restart (503) — poll every 3s, up to 90s
        if (res.status === 503 && errText.includes('Restarting llama')) {
          showToast('llama 正在切换思考模式，请稍候...');
          var maxRetries = 30, delay = 3000;
          for (var ri = 0; ri < maxRetries; ri++) {
            await new Promise(function(r) { setTimeout(r, delay); });
            try {
              var probe = await fetch('http://localhost:8080/health', { signal: AbortSignal.timeout(2000) });
              if (probe.ok) {
                showToast('llama 就绪，继续对话', 2000);
                return this.chatStream(messages, settings, onToken, onComplete, onError);
              }
            } catch (_) {}
          }
          throw new Error('llama 重启超时，请手动重试');
        }
        throw new Error('API ' + res.status + ': ' + errText);
      }

      var contentType = res.headers.get('content-type') || '';
      if (contentType.includes('text/event-stream')) {
        await this._readSSE(res, onToken, onComplete, onError);
      } else {
        // Non-streaming mode — collect reasoning_content as well
        var data = await res.json();
        var msg = data.choices?.[0]?.message || {};
        var text = msg.content || '';
        var reasonText = msg.reasoning_content || '';
        var showReasoning = getSettings().reasoningEnabled !== false;
        if (reasonText && showReasoning) onToken(reasonText, 'reasoning');
        if (text) onToken(text, 'content');
        onComplete({ text: text, reasoningText: reasonText, media: null });
      }
    } catch (err) {
      if (onError) onError(err);
      else console.warn('API error:', err.message);
    }
  },

  _readSSE: async function (response, onToken, onComplete, onError) {
    var reader = response.body.getReader();
    var decoder = new TextDecoder('utf-8');
    var fullText = '';
    var reasoningText = '';
    var buffer = '';
    var showReasoning = getSettings().reasoningEnabled !== false;

    try {
      while (true) {
        var _a = await reader.read(),
          done = _a.done,
          value = _a.value;
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        var lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (var i = 0; i < lines.length; i++) {
          var trimmed = lines[i].trim();
          if (!trimmed || trimmed.startsWith(':')) continue;

          if (trimmed.startsWith('data: ')) {
            var raw = trimmed.slice(6);
            if (raw === '[DONE]') {
              onComplete({ text: fullText, reasoningText: reasoningText, media: null });
              return;
            }
            try {
              var json = JSON.parse(raw);
              var delta = json.choices?.[0]?.delta;
              var reasoningDelta = delta?.reasoning_content;
              var contentDelta = delta?.content;
              if (reasoningDelta) {
                reasoningText += reasoningDelta;
                if (showReasoning) onToken(reasoningDelta, 'reasoning');
              }
              if (contentDelta) {
                fullText += contentDelta;
                onToken(contentDelta, 'content');
              }
              if (json.choices?.[0]?.finish_reason) {
                onComplete({ text: fullText, reasoningText: reasoningText, media: null });
                return;
              }
            } catch (_) {}
          }
        }
      }
      onComplete({ text: fullText, reasoningText: reasoningText, media: null });
    } catch (err) {
      if (onError) onError(err);
    } finally {
      reader.releaseLock();
    }
  },

  nonStreamChat: function (messages, settings) {
    // If model is the fallback 'local-model' and we have real models cached,
    // use the first available one instead.
    var model = settings.model;
    if (model === 'local-model' && this._modelsCache && this._modelsCache.length > 0) {
      model = this._modelsCache[0].id;
    }
    if (!model) model = this.getDefaultModel();
    var characterId = settings.characterId || 'natsume';
    var body = {
      model: model,
      messages: this._cleanMessages(messages),
      stream: false,
      max_tokens: 4096,
      characterId: characterId,
      reasoning: settings.reasoningEnabled !== false ? 'on' : 'off',
      thinkingMode: settings.thinkingMode || 'default',
      mem0Enhanced: settings.mem0Enhanced === true,
      mem0WriteEnabled: settings.mem0WriteEnabled === true,
      mem0WriteInterval: settings.mem0WriteInterval || 10,
      language: settings.language || 'zh',
    };
    // Headroom 配置（前端面板调参）
    if (typeof getHeadroomConfig === 'function') {
      body.headroom_config = getHeadroomConfig();
    }
    if (settings.systemPrompt) body.systemPrompt = settings.systemPrompt;
    return fetch('http://localhost:19260/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(180000),
    })
      .then(function (res) {
        if (!res.ok) throw new Error('API ' + res.status);
        return res.json();
      })
      .then(function (data) {
        return data.choices?.[0]?.message?.content || '';
      });
  },

  checkStatus: function () {
    return fetch('http://localhost:19260/api/status', {
      signal: AbortSignal.timeout(3000),
    })
      .then(function (r) { return r.ok; })
      .catch(function () { return false; });
  },

  /**
   * Fetch session history from OpenClaw session store.
   * @param {string} sessionKey - e.g. "main", "qqbot", etc.
   * @param {number} limit - number of recent messages
   * @returns {Promise<{ok: boolean, history: Array}>}
   */
  fetchSessionHistory: function (sessionKey, limit) {
    sessionKey = sessionKey || 'main';
    limit = limit || 10;
    return fetch(
      'http://localhost:19260/api/session-history?sessionKey=' + encodeURIComponent(sessionKey) + '&limit=' + limit,
      {
        signal: AbortSignal.timeout(10000),
      }
    )
      .then(function (r) {
        if (!r.ok) throw new Error('Session history returned ' + r.status);
        return r.json();
      })
      .catch(function (err) {
        console.warn('Session history fetch failed:', err.message);
        return { ok: false, history: [], source: 'session-history', error: err.message };
      });
  },

  /**
   * Search mem0 memories.
   * @param {string} query - search query
   * @param {number} limit - number of results
   * @returns {Promise<{ok: boolean, results: Array}>}
   */
  mem0Search: function (query, limit) {
    query = query || '';
    limit = limit || 20;
    return fetch(
      'http://localhost:19260/api/mem0-search?query=' + encodeURIComponent(query) + '&limit=' + limit,
      {
        signal: AbortSignal.timeout(10000),
      }
    )
      .then(function (r) {
        if (!r.ok) throw new Error('Mem0 search returned ' + r.status);
        return r.json();
      })
      .catch(function (err) {
        console.warn('Mem0 search fetch failed:', err.message);
        return { ok: false, results: [], source: 'mem0', error: err.message };
      });
  },
};
