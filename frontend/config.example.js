/**
 * Frontend Configuration Example
 *
 * 部署到 Cloudflare Pages 时：
 * 1. 复制此文件为 config.production.js
 * 2. 修改 API_BASE_URL 为你的 Vercel 后端 URL
 * 3. 在 HTML 文件中引用 config.production.js 而不是 config.js
 */

const CONFIG = {
    // ⚠️ 部署前必须修改这个 URL
    API_BASE_URL: 'https://your-vercel-backend.vercel.app',

    // API 端点（通常不需要修改）
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
