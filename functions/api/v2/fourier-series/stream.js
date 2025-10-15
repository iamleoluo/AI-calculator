/**
 * Cloudflare Worker Proxy for V2 Streaming API
 *
 * This worker forwards requests to the Python backend (Railway)
 * and streams the response back to the client.
 *
 * Benefits:
 * - No CORS issues (same origin)
 * - Edge caching (future enhancement)
 * - Request/response logging
 * - Rate limiting (future enhancement)
 */

export async function onRequest(context) {
  const { request, env } = context;

  // Get backend URL from environment variable
  const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8000';

  // Only allow POST requests
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  try {
    // Get request body
    const body = await request.json();

    // Forward request to Python backend
    const backendUrl = `${BACKEND_URL}/api/v2/fourier-series/stream`;

    console.log(`[Worker] Forwarding request to: ${backendUrl}`);

    const backendResponse = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    // Check if backend is available
    if (!backendResponse.ok) {
      console.error(`[Worker] Backend error: ${backendResponse.status}`);
      return new Response(JSON.stringify({
        error: 'Backend unavailable',
        status: backendResponse.status,
        message: 'The calculation service is temporarily unavailable. Please try again later.'
      }), {
        status: 502,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Stream the response from backend to client
    // This maintains the SSE (Server-Sent Events) format
    return new Response(backendResponse.body, {
      status: backendResponse.status,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    console.error('[Worker] Error:', error);

    return new Response(JSON.stringify({
      error: 'Proxy error',
      message: error.message,
      details: 'Failed to communicate with the backend service'
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
