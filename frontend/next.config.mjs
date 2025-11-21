/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    async rewrites() {
        // 开发环境使用 127.0.0.1:8000，生产环境通过 BACKEND_URL 环境变量控制
        const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
        return [
            {
                source: "/api/:path*",
                destination: `${backendUrl}/:path*`,
            },
        ];
    },
    // 配置图片域名白名单 (用于 AI 生成的图片)
    images: {
        remotePatterns: [
            {
                protocol: 'https',
                hostname: 'oaidalleapiprodscus.blob.core.windows.net',
            },
            {
                protocol: 'https',
                hostname: '**.replicate.delivery',
            },
            {
                protocol: 'https',
                hostname: 'storage.googleapis.com',
            },
        ],
    },
};

export default nextConfig;
