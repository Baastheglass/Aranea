/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',  // Enable static export for Electron
  distDir: 'out',
  images: {
    unoptimized: true  // Required for static export
  },
  // Disable API routes in static export
  trailingSlash: true
};

export default nextConfig;


