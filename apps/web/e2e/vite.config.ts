import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  root: path.resolve(__dirname, "harness"),
  plugins: [react()],
  define: {
    "process.env.NEXT_PUBLIC_API_URL": JSON.stringify("http://atlas.test/api/v1"),
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "../src"),
      "@clerk/nextjs": path.resolve(__dirname, "harness/clerk-test-shim.tsx"),
      "next/link": path.resolve(__dirname, "harness/next-link-test-shim.tsx"),
    },
  },
  server: {
    strictPort: true,
  },
});
