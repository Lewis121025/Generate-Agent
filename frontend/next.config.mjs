/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    async rewrites() {
        // In Docker Compose, use service name; in local dev, use localhost
        // Default to localhost for local development
        const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
        return [
            {
                source: "/api/:path*",
                destination: `${backendUrl}/:path*`,
            },
        ];
    },
};

export default nextConfig;
