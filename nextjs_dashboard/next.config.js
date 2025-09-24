/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['localhost'],
  },
  serverExternalPackages: ['pg', 'pg-native', 'bcryptjs'],
  reactStrictMode: true,
  poweredByHeader: false,
  compress: true,
}

module.exports = nextConfig