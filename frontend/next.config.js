/** @type {import('next').NextConfig} */
const nextConfig = {
  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ];
  },
  // Enable standalone output for Docker
  output: "standalone",
  // Disable API rewrites to prevent routing conflicts
  // async rewrites() {
  //   return [
  //     {
  //       source: "/api/:path*",
  //       destination: `${
  //         process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"
  //       }/:path*`,
  //     },
  //   ];
  // },
};

module.exports = nextConfig;
