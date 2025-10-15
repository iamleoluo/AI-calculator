/**
 * Frontend Configuration
 *
 * 使用说明：
 * 1. 本地开发：使用 localhost
 * 2. Cloudflare Pages 部署：修改 API_BASE_URL 为你的后端 URL
 */

const CONFIG = {
    // API Base URL - 根据环境修改
    // 本地开发: 'http://localhost:8000'
    // 生产环境: 'https://your-backend.railway.app' (或其他后端 URL)
    API_BASE_URL: window.location.hostname === 'localhost'
        ? 'http://localhost:8000'
        : 'https://your-backend-url.com',  // 部署时修改这里

    // API 端点
    API_ENDPOINTS: {
        V1: '/api/fourier-series',
        V2_STREAM: '/api/v2/fourier-series/stream',
        V2_SYNC: '/api/v2/fourier-series',
        HEALTH: '/api/health'
    }
};

// 导出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
