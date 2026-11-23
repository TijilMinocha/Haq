/// <reference types="vitest/config" />
import { fileURLToPath, URL } from 'node:url';

import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';

const apiProxy = { '/api': process.env.API_PROXY_TARGET ?? 'http://localhost:8000' };
const tunnelHosts = ['.trycloudflare.com'];

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'Haq',
        short_name: 'Haq',
        description: 'Find the insurance your family is owed',
        lang: 'hi',
        theme_color: '#0f766e',
        background_color: '#ffffff',
        display: 'standalone',
        start_url: '/',
        icons: [{ src: 'favicon.svg', sizes: 'any', type: 'image/svg+xml' }],
      },
    }),
  ],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  // With VITE_API_BASE_URL=/api/v1 the app calls its own origin and these proxies forward to
  // the server, so one Cloudflare tunnel URL serves both on demo day.
  server: { proxy: apiProxy, allowedHosts: tunnelHosts },
  preview: { proxy: apiProxy, allowedHosts: tunnelHosts },
  test: {
    environment: 'jsdom',
  },
});
