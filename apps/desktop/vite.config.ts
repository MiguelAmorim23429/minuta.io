import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Configuração recomendada para Tauri: porta fixa e sem limpar o ecrã (mostra erros do Rust).
export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    watch: { ignored: ["**/src-tauri/**"] },
  },
  build: {
    target: "es2022",
  },
});
