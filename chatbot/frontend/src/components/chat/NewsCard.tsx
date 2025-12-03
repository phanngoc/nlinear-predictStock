'use client'

import ReactMarkdown from 'react-markdown'

export function NewsCard({ content, role, isDailySummary = false }: { content: string; role: string; isDailySummary?: boolean }) {
  if (role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="bg-blue-600 text-white px-4 py-2 rounded-2xl rounded-br-md max-w-[70%]">
          {content}
        </div>
      </div>
    )
  }

  // For Daily News Summary, show full content without truncation
  if (isDailySummary) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
        <p className="text-gray-700 whitespace-pre-wrap">{content}</p>
      </div>
    )
  }

  // For AI Response, render markdown content directly
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
      <div className="prose prose-sm max-w-none text-gray-700">
        <ReactMarkdown
          components={{
            h1: ({ children }) => <h1 className="text-xl font-bold text-gray-900 mb-3 mt-4 first:mt-0">{children}</h1>,
            h2: ({ children }) => <h2 className="text-lg font-bold text-gray-900 mb-2 mt-3 first:mt-0">{children}</h2>,
            h3: ({ children }) => <h3 className="text-base font-semibold text-gray-900 mb-2 mt-3 first:mt-0">{children}</h3>,
            p: ({ children }) => <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>,
            ul: ({ children }) => <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>,
            li: ({ children }) => <li className="ml-2">{children}</li>,
            strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
            em: ({ children }) => <em className="italic">{children}</em>,
            a: ({ href, children }) => (
              <a 
                href={href} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 underline"
              >
                {children}
              </a>
            ),
            code: ({ children }) => (
              <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800">
                {children}
              </code>
            ),
            blockquote: ({ children }) => (
              <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600 my-3">
                {children}
              </blockquote>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  )
}
