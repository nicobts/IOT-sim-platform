# IOT SIM Platform - React Frontend

Next.js 15 dashboard for the IOT SIM Platform with TypeScript, React 19, and Tailwind CSS.

**Note**: This is part of a monorepo. See the [main README](../README.md) for full platform documentation.

## 🚀 Next.js 15 Features

This frontend leverages the latest Next.js 15 and React 19 capabilities:

- **⚡ Turbopack** - 10x faster development with Rust-based bundler
- **🎯 Partial Prerendering (PPR)** - Hybrid static/dynamic rendering
- **🎨 React 19 Compiler** - Automatic component optimization
- **💾 Enhanced Caching** - Improved performance with smart cache control
- **🔒 Typed Routes** - Type-safe navigation with TypeScript
- **📦 Optimized Images** - Better AVIF support and responsive images
- **🔄 Server Actions** - Simplified server-side mutations

See [NEXTJS15_MIGRATION.md](NEXTJS15_MIGRATION.md) for complete migration details.

## Tech Stack

- **Framework**: Next.js 15.1.0 (App Router + Turbopack)
- **React**: 19.0.0 (with React Compiler)
- **Language**: TypeScript 5.7.2
- **Styling**: Tailwind CSS 3.4
- **State Management**: Zustand 5.0
- **Data Fetching**: SWR 2.2 + Server Actions
- **Charts**: Recharts 2.15
- **Icons**: Lucide React
- **HTTP Client**: Axios 1.7
- **Bundler**: Turbopack (Rust-based, 10x faster)

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

Next.js 15 uses Turbopack by default for development:

**Benefits:**
- 10x faster Hot Module Replacement (HMR)
- 5x faster initial compilation
- Better memory usage
- Near-instant updates

**Performance Comparison:**
- Cold start: ~0.5s (vs ~5s with Webpack)
- HMR update: ~50ms (vs ~500ms with Webpack)

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
