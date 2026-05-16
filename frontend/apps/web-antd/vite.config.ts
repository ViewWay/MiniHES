import { defineConfig } from '@vben/vite-config';

export default defineConfig(async () => {
  const isMock = process.env.VITE_NITRO_MOCK !== 'false';
  const realApiUrl =
    process.env.VITE_REAL_API_URL || 'http://localhost:8000';

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
