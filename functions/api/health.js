/**
 * Health Check Endpoint
 *
 * This endpoint checks both the Cloudflare Worker and the Python backend
 */

export async function onRequest(context) {
  const { env } = context;

  // Get backend URL from environment variable
  const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8000';

  const health = {
    worker: 'healthy',
    backend: 'unknown',
    backendUrl: BACKEND_URL,
    timestamp: new Date().toISOString()
  };

  try {
    // Check backend health
    const backendResponse = await fetch(`${BACKEND_URL}/api/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (backendResponse.ok) {
      const backendHealth = await backendResponse.json();
      health.backend = 'healthy';
      health.backendDetails = backendHealth;
    } else {
      health.backend = 'unhealthy';
      health.backendStatus = backendResponse.status;
    }

  } catch (error) {
    health.backend = 'unreachable';
    health.backendError = error.message;
  }

  const isHealthy = health.worker === 'healthy' && health.backend === 'healthy';

  return new Response(JSON.stringify(health, null, 2), {
    status: isHealthy ? 200 : 503,
    headers: {
      'Content-Type': 'application/json',
    },
  });
}
