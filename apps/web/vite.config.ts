import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// The web app never hardcodes an API host: it always calls relative `/api/...`
// paths (see src/api/client.ts). In Docker the dev server proxies those to the
// `api` service by name. The target is overridable for running the dev server
// outside compose, but defaults to the compose service address per the brief.
const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? 'http://api:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    include: ['src/**/*.test.{ts,tsx}'],
  },
});
