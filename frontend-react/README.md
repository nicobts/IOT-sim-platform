# IOT SIM Platform - React Frontend

Next.js 14 dashboard for the IOT SIM Platform with TypeScript and Tailwind CSS.

**Note**: This is part of a monorepo. See the [main README](../README.md) for full platform documentation.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: SWR
- **Charts**: Recharts
- **Icons**: Lucide React
- **HTTP Client**: Axios

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Lint code
npm run lint

# Type check
npm run type-check
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
