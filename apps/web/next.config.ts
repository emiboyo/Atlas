import type { NextConfig } from "next";

const contentSecurityPolicy = [
  "default-src 'self'",
  "base-uri 'self'",
  "object-src 'none'",
  "frame-ancestors 'none'",
  "form-action 'self'",
  "script-src 'self' 'unsafe-inline' https://js.stripe.com https://*.clerk.accounts.dev",
  "style-src 'self' 'unsafe-inline'",
  "font-src 'self' data:",
  "img-src 'self' data: blob: https://img.clerk.com",
  "connect-src 'self' https://api.stripe.com https://*.clerk.accounts.dev",
  "frame-src https://js.stripe.com https://hooks.stripe.com https://*.clerk.accounts.dev",
  "worker-src 'self' blob:",
].join("; ");

const nextConfig: NextConfig = {
  // Standalone tracing requires symlink privileges that are commonly unavailable
  // on Windows. Docker explicitly enables it for the production container image.
  output: process.env.NEXT_OUTPUT_MODE === "standalone" ? "standalone" : undefined,
  poweredByHeader: false,
  reactStrictMode: true,
  typedRoutes: true,
  headers: () =>
    Promise.resolve([
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Content-Security-Policy", value: contentSecurityPolicy },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
    ]),
};

export default nextConfig;
