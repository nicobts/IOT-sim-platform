'use client'

import { useEffect, useState } from 'react'
import { Activity, Database, Server, Wifi } from 'lucide-react'

export default function Home() {
  const [stats, setStats] = useState({
    totalSims: 0,
    activeSims: 0,
    totalUsage: '0 MB',
    apiStatus: 'checking...'
  })

  useEffect(() => {
    // Health check
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`)
      .then(res => res.json())
      .then(data => {
        setStats(prev => ({ ...prev, apiStatus: data.status || 'ok' }))
      })
      .catch(() => {
        setStats(prev => ({ ...prev, apiStatus: 'error' }))
      })
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Wifi className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">IOT SIM Platform</h1>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`h-2 w-2 rounded-full ${stats.apiStatus === 'ok' ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm text-gray-600">API: {stats.apiStatus}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h2>
          <p className="text-gray-600">Monitor and manage your IoT SIM cards</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={<Database className="h-6 w-6" />}
            title="Total SIMs"
            value={stats.totalSims.toString()}
            color="blue"
          />
          <StatCard
            icon={<Activity className="h-6 w-6" />}
            title="Active SIMs"
            value={stats.activeSims.toString()}
            color="green"
          />
          <StatCard
            icon={<Server className="h-6 w-6" />}
            title="Total Usage"
            value={stats.totalUsage}
            color="purple"
          />
          <StatCard
            icon={<Wifi className="h-6 w-6" />}
            title="API Status"
            value={stats.apiStatus}
            color={stats.apiStatus === 'ok' ? 'green' : 'red'}
          />
        </div>

        {/* Welcome Section */}
        <div className="bg-white rounded-lg shadow-md p-8">
          <h3 className="text-xl font-semibold mb-4">Welcome to IOT SIM Platform</h3>
          <div className="space-y-4 text-gray-600">
            <p>
              This is a full-stack platform for managing IoT SIM cards with complete 1NCE API integration.
            </p>
            <div className="grid md:grid-cols-2 gap-4 mt-6">
              <FeatureCard
                title="SIM Management"
                description="View, monitor, and manage all your IoT SIM cards in one place"
              />
              <FeatureCard
                title="Usage Tracking"
                description="Real-time data usage monitoring with TimescaleDB"
              />
              <FeatureCard
                title="Quota Management"
                description="Automated quota tracking and top-up capabilities"
              />
              <FeatureCard
                title="Real-time Monitoring"
                description="Live connectivity status and network information"
              />
            </div>
          </div>
        </div>

        {/* Quick Links */}
        <div className="mt-8 grid md:grid-cols-3 gap-4">
          <QuickLink
            title="API Documentation"
            description="View complete API documentation"
            href={`${process.env.NEXT_PUBLIC_API_URL}/docs`}
          />
          <QuickLink
            title="Grafana Dashboards"
            description="Monitor metrics and performance"
            href="http://localhost:3001"
          />
          <QuickLink
            title="Prometheus"
            description="View raw metrics data"
            href="http://localhost:9090"
          />
        </div>
      </main>
    </div>
  )
}

function StatCard({ icon, title, value, color }: {
  icon: React.ReactNode
  title: string
  value: string
  color: string
}) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    red: 'bg-red-100 text-red-600',
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className={`inline-flex p-3 rounded-lg ${colorClasses[color as keyof typeof colorClasses]} mb-4`}>
        {icon}
      </div>
      <h3 className="text-sm font-medium text-gray-600 mb-1">{title}</h3>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  )
}

function FeatureCard({ title, description }: {
  title: string
  description: string
}) {
  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <h4 className="font-semibold text-gray-900 mb-2">{title}</h4>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  )
}

function QuickLink({ title, description, href }: {
  title: string
  description: string
  href: string
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="block bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
    >
      <h4 className="font-semibold text-gray-900 mb-2">{title}</h4>
      <p className="text-sm text-gray-600">{description}</p>
    </a>
  )
}
