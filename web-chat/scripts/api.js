// ============================================================
// api.js - OpenClaw Gateway API client (SSE streaming)
// ============================================================

const ApiClient = {
  base: '',

  init(apiBase) {
    this.base = apiBase || '';
  },

  /**
   * Stream chat completion via SSE
   * Returns { text: string, media: string|null }
   */
  async chatStream(messages, settings = {}, onToken, onComplete, onError) {
    const base = settings.apiBase || this.base || '';
    const endpoint = base + '/api/v1/chat/completions';
    const model = settings.model || 'local-model';

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model,
          messages,
          stream: true,
          max_tokens: 4096,
        }),
        signal: AbortSignal.timeout(60000),
      });

      if (!res.ok) {
        throw new Error(`API ${res.status}: ${res.statusText}`);
      }

      // Check if SSE or plain JSON
      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('text/event-stream')) {
        await this._readSSE(res, onToken, onComplete, onError);
      } else {
        // Fallback to non-streaming parse
        const data = await res.json();
        const text = data.choices?.[0]?.message?.content || '';
        onToken(text);
        onComplete({ text, media: null });
      }
    } catch (err) {
      if (onError) onError(err);
      else console.warn('API error:', err.message);
    }
  },

  async _readSSE(response, onToken, onComplete, onError) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let fullText = '';
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || trimmed.startsWith(':')) continue;

          if (trimmed.startsWith('data: ')) {
            const data = trimmed.slice(6);
            if (data === '[DONE]') {
              onComplete({ text: fullText, media: null });
              return;
            }

            try {
              const json = JSON.parse(data);
              const delta = json.choices?.[0]?.delta?.content;
              if (delta) {
                fullText += delta;
                onToken(delta);
              }
              // Check for finish_reason
              if (json.choices?.[0]?.finish_reason) {
                onComplete({ text: fullText, media: null });
                return;
              }
            } catch {
              // skip malformed chunks
            }
          }
        }
      }
      // stream ended without [DONE]
      onComplete({ text: fullText, media: null });
    } catch (err) {
      if (onError) onError(err);
    } finally {
      reader.releaseLock();
    }
  },

  /**
   * Check if Gateway is online
   */
  async checkStatus() {
    try {
      const res = await fetch((this.base || '') + '/api/v1/models', {
        signal: AbortSignal.timeout(3000),
      });
      return res.ok;
    } catch {
      return false;
    }
  },
};
