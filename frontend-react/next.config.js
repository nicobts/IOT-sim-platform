/** @type {import('next').NextConfig} */
const nextConfig = {
  // React strict mode
  reactStrictMode: true,

  // Output configuration for Docker deployment
  output: 'standalone',

  // Turbopack is now the default bundler in Next.js 16!
  // No need to specify --turbo flag
  turbo: {
    rules: {
      '*.svg': {
        loaders: ['@svgr/webpack'],
        as: '*.js',
      },
    },
  },

  // Next.js 16 features
  experimental: {
    // Partial Prerendering (PPR) - Now stable in Next.js 16
    // Can be enabled globally instead of incremental
    ppr: true,

    // Cache Components - New in Next.js 16
    // Enable the "use cache" directive for component-level caching
    cacheComponents: true,

    // View Transitions - React 19.2 feature
    // Animate elements during navigation
    viewTransitions: true,

    // Improved caching with better staleTimes
    staleTimes: {
      dynamic: 30,  // 30 seconds for dynamic pages
      static: 180,  // 3 minutes for static pages
    },

    // Server Actions improvements
    serverActions: {
      bodySizeLimit: '2mb',
      allowedOrigins: ['localhost:3000'],
    },

    // TypeScript plugin improvements
    typedRoutes: true,

    // Optimized package imports
    optimizePackageImports: ['lucide-react', 'recharts', 'date-fns'],
  },

  // React Compiler - Now STABLE in Next.js 16 (not experimental!)
  compiler: {
    // React Compiler automatically memoizes components
    reactCompiler: true,

    // Remove console logs in production
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error', 'warn'],
    } : false,
  },

  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_APP_VERSION: process.env.NEXT_PUBLIC_APP_VERSION || '2.1.0',
  },

  // Image optimization with Next.js 16 improvements
  images: {
    // Allowed domains for external images
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
    // Image formats - AVIF is default in Next.js 16
    formats: ['image/avif', 'image/webp'],
    // Disable optimization in development for faster builds
    unoptimized: process.env.NODE_ENV === 'development',
    // Device sizes for responsive images
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    // Image sizes for different viewports
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // Headers for security and performance
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()'
          }
        ],
      },
    ];
  },

  // Redirects
  async redirects() {
    return [
      {
        source: '/home',
        destination: '/',
        permanent: true,
      },
    ];
  },

  // Webpack configuration (Turbopack is preferred in Next.js 16)
  webpack: (config, { isServer }) => {
    // Fixes for Node.js modules
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
      };
    }

    // SVG support
    config.module.rules.push({
      test: /\.svg$/,
      use: ['@svgr/webpack'],
    });

    return config;
  },

  // Performance optimizations
  poweredByHeader: false,
  generateEtags: true,
  compress: true,

  // Logging - Enhanced in Next.js 16
  logging: {
    fetches: {
      fullUrl: process.env.NODE_ENV === 'development',
      hmrRefreshes: true,  // New in Next.js 16
    },
  },
}

// Bundle analyzer (conditional)
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

module.exports = withBundleAnalyzer(nextConfig)
