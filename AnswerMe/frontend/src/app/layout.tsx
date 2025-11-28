import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AnswerMe - News Summary Chatbot',
  description: 'AI-powered news aggregation and summary system',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">{children}</body>
    </html>
  )
}
