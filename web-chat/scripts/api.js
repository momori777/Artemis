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
        throw new Error('API ' + res.status + ': ' + errText);
      }

      var contentType = res.headers.get('content-type') || '';
      if (contentType.includes('text/event-stream')) {
        await this._readSSE(res, onToken, onComplete, onError);
      } else {
        var data = await res.json();
        var text = data.choices?.[0]?.message?.content || '';
        onToken(text);
        onComplete({ text: text, media: null });
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
    var buffer = '';

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
              onComplete({ text: fullText, media: null });
              return;
            }
            try {
              var json = JSON.parse(raw);
              var delta = json.choices?.[0]?.delta?.content;
              if (delta) {
                fullText += delta;
                onToken(delta);
              }
              if (json.choices?.[0]?.finish_reason) {
                onComplete({ text: fullText, media: null });
                return;
              }
            } catch (_) {}
          }
        }
      }
      onComplete({ text: fullText, media: null });
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
};
