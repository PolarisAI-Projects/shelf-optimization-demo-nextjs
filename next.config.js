/** @type {import('next').NextConfig} */
const nextConfig = {
  // Vercelデプロイ用の設定
  // APIリダイレクトは開発環境のみ有効にする
  async rewrites() {
    // 本番環境（Vercel）では、APIは同じドメインで動作するためリライト不要
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: 'http://127.0.0.1:8000/api/:path*', // 開発時のみ外部FastAPIサーバー
        },
      ];
    }
    return []; // 本番環境ではリライトなし
  },
  env: {
    FASTAPI_URL: process.env.FASTAPI_URL || 'http://localhost:8000',
  },
};

module.exports = nextConfig; 
