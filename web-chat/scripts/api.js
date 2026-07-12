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
          models = [{ id: 'local/qwen3.6-35b', name: 'Local (Llama)' }];
        }
        self._modelsCache = models;
        return models;
      })
      .catch(function () {
        return [{ id: 'local/qwen3.6-35b', name: 'Local (Llama)' }];
      });
  },

  /**
   * Stream chat via daemon proxy.
   */
  chatStream: async function (messages, settings, onToken, onComplete, onError) {
    var model = settings.model || 'local/qwen3.6-35b';
    var characterId = settings.characterId || 'natsume';
    var body = {
      model: model,
      messages: messages,
      stream: true,
      max_tokens: 4096,
      characterId: characterId,
      reasoning: settings.reasoningEnabled !== false ? 'on' : 'off',
      thinkingMode: settings.thinkingMode || 'default',
      mem0Enhanced: settings.mem0Enhanced === true,
      mem0WriteEnabled: settings.mem0WriteEnabled === true,
      mem0WriteInterval: settings.mem0WriteInterval || 10,
    };
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
        // Auto retry on llama restart (503)
        if (res.status === 503 && errText.includes('Restarting llama')) {
          showToast('llama 正在切换思考模式，稍等重试...');
          await new Promise(function(r) { setTimeout(r, 30000); });
          return this.chatStream(messages, settings, onToken, onComplete, onError);
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
    var model = settings.model || 'local/qwen3.6-35b';
    var characterId = settings.characterId || 'natsume';
    var body = {
      model: model,
      messages: messages,
      stream: false,
      max_tokens: 4096,
      characterId: characterId,
      reasoning: settings.reasoningEnabled !== false ? 'on' : 'off',
      thinkingMode: settings.thinkingMode || 'default',
      mem0Enhanced: settings.mem0Enhanced === true,
      mem0WriteEnabled: settings.mem0WriteEnabled === true,
      mem0WriteInterval: settings.mem0WriteInterval || 10,
    };
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
