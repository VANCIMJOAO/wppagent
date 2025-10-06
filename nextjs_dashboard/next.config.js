/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['localhost'],
  },
  serverExternalPackages: ['pg', 'pg-native', 'bcryptjs'],
  reactStrictMode: true,
  poweredByHeader: false,
  compress: true,
  
  // 🔧 CONFIGURAÇÃO PARA MOSTRAR TODOS OS ERROS DE UMA VEZ
  typescript: {
    // Não parar o build no primeiro erro TypeScript
    ignoreBuildErrors: false,
  },
  eslint: {
    // Não parar o build no primeiro erro ESLint
    ignoreDuringBuilds: false,
  },
}

module.exports = nextConfig