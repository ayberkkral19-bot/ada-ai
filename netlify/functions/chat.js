exports.handler = async (event) => {
  if (event.httpMethod === 'POST' && event.path === '/api/voice') {
    return handleVoice(event);
  }
  if (event.httpMethod === 'POST') {
    return handleChat(event);
  }
  if (event.httpMethod === 'GET' && event.path === '/api/search') {
    return handleSearch(event);
  }
  return { statusCode: 405, body: JSON.stringify({ error: 'Method not allowed' }) };
};

async function handleChat(event) {
  const API_KEY = process.env.GROQ_API_KEY;
  if (!API_KEY) {
    return { statusCode: 500, body: JSON.stringify({ error: 'API key not configured' }) };
  }

  try {
    const body = JSON.parse(event.body);
    const { model, messages, max_tokens, temperature } = body;

    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`
      },
      body: JSON.stringify({ model, messages, max_tokens, temperature, tool_choice: 'none', tools: [] })
    });

    const data = await response.json();

    if (!response.ok) {
      return { statusCode: response.status, body: JSON.stringify(data) };
    }

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    };
  } catch (err) {
    return { statusCode: 500, body: JSON.stringify({ error: err.message }) };
  }
}

async function handleSearch(event) {
  try {
    const url = new URL(event.rawUrl || 'http://localhost');
    const query = url.searchParams.get('q');
    if (!query) {
      return { statusCode: 400, body: JSON.stringify({ error: 'Query required' }) };
    }

    const searchUrl = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}&iax=images&ia=images`;
    const res = await fetch(searchUrl, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' }
    });
    const html = await res.text();

    const imageUrls = [];
    const regex = /uddg=([^&"]+)/g;
    let match;
    while ((match = regex.exec(html)) !== null && imageUrls.length < 5) {
      const decoded = decodeURIComponent(match[1]);
      if (decoded.match(/\.(jpg|jpeg|png|gif|webp)/i)) {
        imageUrls.push(decoded);
      }
    }

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ images: imageUrls })
    };
  } catch (err) {
    return { statusCode: 500, body: JSON.stringify({ error: err.message }) };
  }
}

async function handleVoice(event) {
  try {
    const ELEVENLABS_KEY = process.env.ELEVENLABS_API_KEY || 'sk_560f70347071639872693a237c69101451b34cac3321effb';
    const { text, voice_id } = JSON.parse(event.body);

    if (!text || !voice_id) {
      return { statusCode: 400, body: JSON.stringify({ error: 'text and voice_id required' }) };
    }

    const response = await fetch('https://api.elevenlabs.io/v1/text-to-speech/' + voice_id, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'xi-api-key': ELEVENLABS_KEY
      },
      body: JSON.stringify({
        text: text.substring(0, 5000),
        model_id: 'eleven_multilingual_v2',
        voice_settings: { stability: 0.65, similarity_boost: 0.85, style: 0.15, use_speaker_boost: true }
      })
    });

    if (!response.ok) {
      const err = await response.text();
      return { statusCode: response.status, body: JSON.stringify({ error: err }) };
    }

    const buffer = await response.arrayBuffer();
    const base64 = Buffer.from(buffer).toString('base64');

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'audio/mpeg', 'Content-Length': String(buffer.byteLength) },
      body: base64,
      isBase64Encoded: true
    };
  } catch (err) {
    return { statusCode: 500, body: JSON.stringify({ error: err.message }) };
  }
}
