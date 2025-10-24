/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    unoptimized: true,
    remotePatterns: [
      {
        protocol: "https",
        hostname: "i.pravatar.cc",
      },
    ],
  },
  async redirects() {
    return [];
  },
  async rewrites() {
    // Use AWS API Gateway in production, localhost in development
    const apiDestination =
      process.env.NODE_ENV === "production"
        ? "https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com"
        : "http://localhost:8000";

    return [
      {
        source: "/api/:path*",
        destination: `${apiDestination}/:path*`,
      },
    ];
  },
  // Configure for production deployment with full SSR support
  // Remove 'output' to enable server-side rendering
};

module.exports = nextConfig;
