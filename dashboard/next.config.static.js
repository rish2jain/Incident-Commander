/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable static export for S3 deployment
  output: "export",
  trailingSlash: true,
  images: {
    unoptimized: true,
    domains: ["i.pravatar.cc"],
  },
  async redirects() {
    return [
      {
        source: "/demo",
        destination: "/insights-demo",
        permanent: true,
      },
    ];
  },
  // Environment variables for static export
  env: {
    NEXT_PUBLIC_API_BASE_URL:
      "https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com",
    NEXT_PUBLIC_WS_URL:
      "wss://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/dashboard/ws",
    NEXT_PUBLIC_ENVIRONMENT: "production",
  },
};

module.exports = nextConfig;
