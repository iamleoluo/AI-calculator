/**
 * Frontend Configuration
 *
 * 使用说明：
 * 1. 本地开发：使用 localhost
 * 2. Cloudflare Pages 部署：修改 API_BASE_URL 为你的后端 URL
 */

const CONFIG = {
    // API Base URL - 自动检测环境
    // 本地开发: 'http://localhost:8000'
    // 生产环境 (Vercel): 'https://your-project.vercel.app'
    // 生产环境 (Railway): 'https://your-backend.railway.app'
    API_BASE_URL: (() => {
        const hostname = window.location.hostname;

        // 本地开发环境
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:8000';
        }

        // 生产环境 - 从环境变量读取或使用默认值
        // 部署到 Cloudflare Pages 时，在 Pages 设置中添加环境变量 VITE_API_URL
        if (typeof CLOUDFLARE_API_URL !== 'undefined') {
            return CLOUDFLARE_API_URL;
        }

        // 默认生产后端 URL（部署时修改）
        return 'https://your-vercel-backend.vercel.app';
    })(),

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
