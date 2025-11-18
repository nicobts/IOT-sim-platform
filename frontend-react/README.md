# IOT SIM Platform - React Frontend

Next.js 16 dashboard for the IOT SIM Platform with TypeScript, React 19, and Tailwind CSS.

**Note**: This is part of a monorepo. See the [main README](../README.md) for full platform documentation.

## 🚀 Next.js 16 Revolutionary Features

This frontend leverages the **cutting-edge Next.js 16.0.3** with groundbreaking capabilities:

- **💾 Cache Components** - Component-level caching with "use cache" directive
- **🛣️ Routing Overhaul** - 90% reduction in prefetch data (shared layouts downloaded once)
- **🦀 Turbopack Default** - Rust-based bundler now default for dev AND production
- **✨ React Compiler (Stable)** - Production-ready automatic optimization (no more useMemo!)
- **🎬 View Transitions** - React 19.2 smooth animations between pages
- **🎯 PPR (Stable)** - Production-ready Partial Prerendering
- **🤖 DevTools MCP** - AI-assisted debugging with Model Context Protocol
- **📦 Optimized Imports** - 50% smaller bundles with automatic tree-shaking
- **🔒 Typed Routes** - Type-safe navigation with compile-time checks

See [NEXTJS16_MIGRATION.md](NEXTJS16_MIGRATION.md) for complete migration details.

## Tech Stack

- **Framework**: Next.js 16.0.3 (App Router + Turbopack Default)
- **React**: 19.0.0 (with React Compiler - Stable!)
- **Language**: TypeScript 5.7.2
- **Styling**: Tailwind CSS 3.4
- **State Management**: Zustand 5.0
- **Data Fetching**: SWR 2.2 + Server Actions + Cache Components
- **Charts**: Recharts 2.15
- **Icons**: Lucide React (auto-optimized imports)
- **HTTP Client**: Axios 1.7
- **Bundler**: Turbopack (default for dev & production)

## Development

```bash
# Install dependencies
npm install

# Run development server with Turbopack (10x faster!)
npm run dev

# Build for production
npm run build

# Analyze bundle size
npm run analyze

# Start production server
npm run start

# Lint code
npm run lint

# Type check
npm run type-check
```

### Development with Turbopack

Next.js 16 uses Turbopack by default for BOTH development and production:

**Benefits:**
- 10x faster Hot Module Replacement (HMR)
- 2x faster production builds
- Better memory usage
- Near-instant updates

**Performance Comparison:**
- Cold start: ~0.3s (40% faster than Next.js 15)
- HMR update: ~30ms (40% faster than Next.js 15)
- Production build: ~20s (33% faster than Next.js 15)

### Cache Components (New in Next.js 16)

Use the `"use cache"` directive for instant navigation:

```tsx
'use cache';

export const revalidate = 60; // Revalidate every minute

export async function SimList() {
  const sims = await fetch('/api/v1/sims').then(r => r.json());
  return <div>{/* Component tree is cached! */}</div>;
}
```

### View Transitions (React 19.2)

Smooth animations between pages:

```tsx
'use client';
import { useViewTransition } from 'next/navigation';

export function SmoothNav() {
  const router = useViewTransition();
  router.push('/sims'); // Animated!
}
```

## Environment Variables

Copy `.env.example` to `.env.local` and update:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
src/
├── app/              # Next.js App Router pages
│   ├── layout.tsx   # Root layout
│   ├── page.tsx     # Home page
│   └── globals.css  # Global styles
├── components/      # React components
├── lib/             # Utility functions
│   ├── api.ts      # API client
│   └── utils.ts    # Helper functions
├── types/          # TypeScript types
├── hooks/          # Custom React hooks
└── store/          # Zustand stores
```

## Features

- 🎨 Modern UI with Tailwind CSS
- 📱 Responsive design
- 🔐 JWT authentication
- 📊 Real-time data visualization
- ⚡ Fast refresh and hot reload
- 🎯 Type-safe with TypeScript
- 🔄 SWR for data fetching and caching

## Docker

### Monorepo (Recommended)

```bash
# From repository root - Start all services
docker-compose up -d

# Frontend will be available at http://localhost:3000
```

### Standalone

```bash
# Build image
docker build -t iot-frontend:latest .

# Run container
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000 \
  iot-frontend:latest
```

## Integration

The frontend integrates with the FastAPI backend at `/api/v1/*` endpoints:

- Authentication (JWT)
- SIM management
- Usage tracking
- Quota monitoring
- Real-time updates

See [Backend API Documentation](../backend/README.md) for API details.
