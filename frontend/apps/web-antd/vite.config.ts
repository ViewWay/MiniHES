import { loadEnv } from 'vite';

import { defineConfig } from '@vben/vite-config';

export default defineConfig(async ({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const isMock = env.VITE_NITRO_MOCK !== 'false';
  const realApiUrl = env.VITE_REAL_API_URL || 'http://localhost:8000';

  return {
    application: {},
    vite: {
      server: {
        proxy: {
          '/api': {
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/api/, ''),
            target: isMock
              ? 'http://localhost:5320/api'
              : `${realApiUrl}/api`,
            ws: true,
          },
        },
      },
    },
  };
});
