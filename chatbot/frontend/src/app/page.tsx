import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="text-center space-y-6">
        <h1 className="text-4xl font-bold">AnswerMe</h1>
        <p className="text-gray-600 max-w-md">
          AI-powered news aggregation and summary system. Subscribe to keywords, get daily summaries, and chat with AI about the news.
        </p>
        <div className="flex gap-4 justify-center">
          <Link href="/login">
            <Button variant="outline">Login</Button>
          </Link>
          <Link href="/register">
            <Button>Get Started</Button>
          </Link>
        </div>
      </div>
    </main>
  )
}
