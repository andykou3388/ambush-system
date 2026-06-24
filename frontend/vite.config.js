import path from 'path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: [{ find: '@', replacement: path.resolve(__dirname, 'src') }]
  },
  server: {
    host: true,
    port: 3000,
    watch: {
      usePolling: true,  // 使用輪詢方式監控文件變化（解決 Windows volume 問題）
      interval: 1000
    },
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      }
    }
  }
})
