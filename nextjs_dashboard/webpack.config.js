// Configuração webpack adicional para Next.js
const path = require('path');

module.exports = {
  resolve: {
    fallback: {
      fs: false,
      net: false,
      tls: false,
      crypto: false,
      stream: false,
      util: false,
      buffer: false,
      process: false,
    },
    alias: {
      'react': require.resolve('react'),
      'react-dom': require.resolve('react-dom'),
    },
  },
  optimization: {
    splitChunks: {
      cacheGroups: {
        default: {
          minChunks: 1,
        },
      },
    },
  },
};