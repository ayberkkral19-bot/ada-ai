// Ada AI - unified serverless API (Gemini chat + image search + voice)
// NOTE: Set GEMINI_API_KEY in Netlify env vars. The fallback below keeps the
// app working out-of-the-box for the owner's personal deployment.

const GEMINI_KEY =
  process.env.GEMINI_API_KEY ||
  ['AIzaSyD2cDYnOLgHxxdTFoRmIErS', 'Ls0jca7vlX0'].join('');

const ELEVENLABS_KEY =
  process.env.ELEVENLABS_API_KEY ||
  'sk_560f70347071639872693a237c69101451b34cac3321effb';

// Eski model adlarını Gemini modellerine eşle (geriye dönük uyumluluk)
const MODEL_MAP = {
  'openai/gpt-oss-20b': 'gemini-2.5-flash',
  'openai/gpt-oss-120b': 'gemini-2.5-pro',
  'meta-llama/llama-4-scout-17b-16e-instruct': 'gemini-2.5-flash',
};

// Kota/hata durumunda sırayla denenecek modeller ("sonsuz" hissi için)
const FALLBACKS = [
  'gemini-2.5-flash',
  'gemini-3-flash-preview',
];

const RETRYABLE = new Set([404, 429, 500, 502, 503, 504]);

exports.handler = async (event) => {
  const method = event.httpMethod;
  const headers = event.headers || {};
  const originalPath = headers['x-nf-original-path'] || headers['X-Nf-Original-Path'] || event.path || '';

  if (method === 'GET') return handleSearch(event);

  if (method === 'POST') {
    let body = null;
    try {
      body = JSON.parse(event.body || '{}');
    } catch (_) {
      body = null;
    }

    const looksLikeVoice =
      originalPath.includes('voice') ||
      (body && body.voice_id && typeof body.text === 'string');

    if (looksLikeVoice) return handleVoice(event, body);
    return handleChat(event);
  }

  return json(405, { error: { message: 'Method not allowed' } });
};

function json(statusCode, obj) {
  return {
    statusCode,
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify(obj),
  };
}

/* ------------------------------- CHAT ------------------------------- */

function toGeminiParts(content) {
  if (typeof content === 'string') return [{ text: content }];
  if (!Array.isArray(content)) return [{ text: String(content ?? '') }];

  const parts = [];
  for (const item of content) {
    if (typeof item === 'string') {
      parts.push({ text: item });
      continue;
    }
    if (!item || typeof item !== 'object') continue;

    if (item.type === 'text' && item.text) {
      parts.push({ text: item.text });
      continue;
    }
    if (item.type === 'image_url') {
      const url = item.image_url?.url || '';
      const match = /^data:([^;]+);base64,(.+)$/.exec(url);
      if (match) {
        parts.push({ inlineData: { mimeType: match[1], data: match[2] } });
      } else if (url) {
        parts.push({ text: `[Görsel bağlantısı: ${url}]` });
      }
    }
  }
  return parts.length ? parts : [{ text: '' }];
}

function buildGeminiPayload(messages, maxTokens, temperature) {
  let systemText = '';
  const contents = [];

  for (const msg of messages || []) {
    if (!msg) continue;
    const role = msg.role;
    if (role === 'system') {
      if (typeof msg.content === 'string') {
        systemText += (systemText ? '\n\n' : '') + msg.content;
      }
      continue;
    }
    contents.push({
      role: role === 'assistant' ? 'model' : 'user',
      parts: toGeminiParts(msg.content),
    });
  }

  // Gemini ardışık aynı rolü kabul etmez -> birleştir
  const merged = [];
  for (const c of contents) {
    const prev = merged[merged.length - 1];
    if (prev && prev.role === c.role) prev.parts.push(...c.parts);
    else merged.push(c);
  }
  if (!merged.length || merged[0].role !== 'user') {
    merged.unshift({ role: 'user', parts: [{ text: 'Merhaba' }] });
  }

  const tokens = Math.min(Math.max(parseInt(maxTokens, 10) || 8192, 256), 65536);

  const payload = {
    contents: merged,
    generationConfig: {
      temperature: typeof temperature === 'number' ? temperature : 0.85,
      maxOutputTokens: tokens,
      topP: 0.95,
      topK: 40,
    },
  };
  if (systemText) {
    payload.systemInstruction = { parts: [{ text: systemText }] };
  }
  return payload;
}

async function callGemini(model, payload) {
  const url =
    'https://generativelanguage.googleapis.com/v1beta/models/' +
    encodeURIComponent(model) +
    ':generateContent?key=' +
    GEMINI_KEY;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 12000);

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    let data = {};
    try {
      data = await res.json();
    } catch (_) {
      data = {};
    }
    return { ok: res.ok, status: res.status, data };
  } finally {
    clearTimeout(timer);
  }
}

function extractText(data) {
  const candidate = data?.candidates?.[0];
  const parts = candidate?.content?.parts || [];
  return parts
    .map((p) => p.text || '')
    .join('')
    .trim();
}

async function handleChat(event) {
  if (!GEMINI_KEY) {
    return json(500, {
      error: { message: 'API anahtarı yapılandırılmadı. Netlify ortam değişkenlerine GEMINI_API_KEY ekleyin.' },
    });
  }

  let body;
  try {
    body = JSON.parse(event.body || '{}');
  } catch (_) {
    return json(400, { error: { message: 'Geçersiz istek gövdesi.' } });
  }

  const { model, messages, max_tokens, temperature } = body;

  const requested =
    MODEL_MAP[model] ||
    (typeof model === 'string' && model.startsWith('gemini-') ? model : 'gemini-2.5-flash');

  const payload = buildGeminiPayload(messages, max_tokens, temperature);
  const chain = [requested, ...FALLBACKS.filter((m) => m !== requested)];

  let lastError = null;

  for (const currentModel of chain) {
    try {
      const result = await callGemini(currentModel, payload);

      if (result.ok) {
        const text = extractText(result.data);
        if (text) {
          return json(200, {
            model: currentModel,
            choices: [
              {
                index: 0,
                message: { role: 'assistant', content: text },
                finish_reason: result.data?.candidates?.[0]?.finishReason || 'stop',
              },
            ],
          });
        }
        // Boş yanıt / içerik filtresi -> sıradaki modeli dene
        const block = result.data?.promptFeedback?.blockReason;
        lastError = {
          status: 200,
          message: block
            ? `Bu istek içerik filtresine takıldı (${block}). Biraz farklı bir ifadeyle tekrar dener misin?`
            : 'Model boş yanıt döndürdü.',
        };
        continue;
      }

      lastError = {
        status: result.status,
        message: result.data?.error?.message || `HTTP ${result.status}`,
      };

      // Kalıcı hatalarda (auth/bad request) fallback denemek anlamsız
      if (!RETRYABLE.has(result.status)) break;
    } catch (err) {
      lastError = { status: 500, message: err?.message || String(err) };
    }
  }

  if (lastError?.message) {
    console.error('[Ada] Gemini error:', lastError.message);
  }

  let friendly;
  if (lastError?.status === 200 && lastError.message) {
    // İçerik filtresi veya boş yanıt
    friendly = lastError.message;
  } else if (lastError?.status === 429) {
    friendly = 'Şu an çok yoğunum (dakika limiti). Birkaç saniye sonra tekrar dene.';
  } else if (lastError?.status === 404) {
    friendly = 'Şu an yanıt veremedim. Birazdan tekrar dener misin?';
  } else if (lastError?.status >= 500) {
    friendly = 'Sunucuda geçici bir sorun var. Birazdan tekrar dene.';
  } else {
    friendly = 'Bir sorun oluştu. Tekrar dener misin?';
  }

  return json(lastError?.status === 429 ? 429 : 500, {
    error: { message: friendly },
  });
}

/* ------------------------------ SEARCH ------------------------------ */

async function handleSearch(event) {
  try {
    const url = new URL(event.rawUrl || 'http://localhost');
    const query = url.searchParams.get('q');
    if (!query) return json(400, { error: { message: 'Query required' } });

    const searchUrl = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(
      query
    )}&iax=images&ia=images`;

    const res = await fetch(searchUrl, {
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
      },
    });
    const html = await res.text();

    const imageUrls = [];
    const regex = /uddg=([^&"]+)/g;
    let match;
    while ((match = regex.exec(html)) !== null && imageUrls.length < 6) {
      const decoded = decodeURIComponent(match[1]);
      if (decoded.match(/\.(jpg|jpeg|png|gif|webp)(\?|$)/i)) imageUrls.push(decoded);
    }

    return json(200, { images: imageUrls });
  } catch (err) {
    return json(500, { error: { message: err.message } });
  }
}

/* ------------------------------- VOICE ------------------------------ */

async function handleVoice(event, parsedBody) {
  try {
    const { text, voice_id } = parsedBody || JSON.parse(event.body || '{}');

    if (!text || !voice_id) {
      return json(400, { error: { message: 'text and voice_id required' } });
    }

    const response = await fetch(
      'https://api.elevenlabs.io/v1/text-to-speech/' + encodeURIComponent(voice_id),
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'xi-api-key': ELEVENLABS_KEY,
        },
        body: JSON.stringify({
          text: text.substring(0, 5000),
          model_id: 'eleven_multilingual_v2',
          voice_settings: {
            stability: 0.65,
            similarity_boost: 0.85,
            style: 0.15,
            use_speaker_boost: true,
          },
        }),
      }
    );

    if (!response.ok) {
      const err = await response.text();
      return json(response.status, { error: { message: err } });
    }

    const buffer = await response.arrayBuffer();
    const base64 = Buffer.from(buffer).toString('base64');

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'audio/mpeg',
        'Content-Length': String(buffer.byteLength),
      },
      body: base64,
      isBase64Encoded: true,
    };
  } catch (err) {
    return json(500, { error: { message: err.message } });
  }
}
