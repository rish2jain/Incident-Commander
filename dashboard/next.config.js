/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',  // Enable static HTML export for CloudFront deployment
  images: {
    unoptimized: true,
    remotePatterns: [
      {
        protocol: "https",
        hostname: "i.pravatar.cc",
      },
    ],
  },
  // Note: redirects() and rewrites() are not supported with output: 'export'
  // API calls will be made directly to the API Gateway URL from the client
  // Configure for production deployment with static export
  // All path aliases have been replaced with relative imports
  // No webpack configuration needed
};

module.exports = nextConfig;
