/** @type {import('next').NextConfig} */
module.exports = {
  // The frontend now calls the Django API directly using
  // the NEXT_PUBLIC_API_BASE environment variable. The
  // /api rewrite is no longer necessary when the backend
  // is running on a different origin, so it is disabled.
  // async rewrites() {
  //   return [
  //     {
  //       source: "/api/:path*",
  //       destination: "http://127.0.0.1:8000/api/:path*",
  //     },
  //   ];
  // },
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb'
    }
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
}; 