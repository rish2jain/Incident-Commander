/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
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
  // Enable static optimization for better performance
  trailingSlash: false,
  // Configure for AWS Amplify deployment
  output: process.env.NODE_ENV === "production" ? "standalone" : undefined,
};

module.exports = nextConfig;
