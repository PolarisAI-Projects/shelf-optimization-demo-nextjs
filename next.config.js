/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    FASTAPI_URL: process.env.FASTAPI_URL || 'http://localhost:8000',
  },
};

module.exports = nextConfig; 
