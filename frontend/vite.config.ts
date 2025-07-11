import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // 청크 크기 경고 한계값 증가
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        // 수동 청크 분리로 번들 최적화
        manualChunks: {
          // React 관련 라이브러리
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // Redux 관련
          'redux-vendor': ['@reduxjs/toolkit', 'react-redux'],
          // UI 라이브러리
          'mui-vendor': ['@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled'],
          // 차트 라이브러리
          'chart-vendor': ['recharts'],
          // 유틸리티
          'util-vendor': ['date-fns', 'socket.io-client', 'framer-motion'],
        },
      },
    },
  },
  // 개발 서버 최적화
  server: {
    port: 3000,
    open: true,
  },
})
