exports.handler = async (event) => {
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
      body: JSON.stringify({ model, messages, max_tokens, temperature })
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
