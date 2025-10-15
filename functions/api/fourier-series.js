/**
 * Cloudflare Worker Proxy for V1 API
 *
 * This worker forwards requests to the Python backend (Railway)
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
    const backendUrl = `${BACKEND_URL}/api/fourier-series`;

    console.log(`[Worker] Forwarding V1 request to: ${backendUrl}`);

    const backendResponse = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    // Get response body
    const responseData = await backendResponse.json();

    // Return response with appropriate status
    return new Response(JSON.stringify(responseData), {
      status: backendResponse.status,
      headers: {
        'Content-Type': 'application/json',
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
