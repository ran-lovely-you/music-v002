import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // 家族が同じ家庭内LANの別端末（スマホ・タブレット等）からもアクセスできるように、
    // localhostだけでなく全ネットワークインターフェースで待ち受ける。
    host: true,
    proxy: {
      "/api": "http://localhost:8000",
      "/outputs": "http://localhost:8000",
    },
  },
});
