import type { Metadata } from 'next'
import './globals.css'
import './globals.scss'

export const metadata: Metadata = {
  title: 'AI Real Estate Deals Finder',
  description: 'Find the best real estate deals with AI-powered analysis',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">{children}</body>
    </html>
  )
}
