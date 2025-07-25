'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

interface SearchResult {
  id: number
  title: string
  summary: string
  url: string
  source: string
  published_at: string
  relevance_score: number
}

interface SearchFilters {
  dateRange: string
  contentType: string
  source: string
}

const SearchPage = () => {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState<SearchFilters>({
    dateRange: '',
    contentType: '',
    source: ''
  })

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    try {
      const searchParams = new URLSearchParams({
        query,
        ...filters
      })
      
      const response = await fetch(`http://localhost:8000/api/search?${searchParams}`)
      if (response.ok) {
        const data = await response.json()
        setResults(data.results || [])
      }
    } catch (error) {
      console.error('Search error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFeedback = async (contentId: number, feedback: 'like' | 'dislike') => {
    try {
      await fetch('http://localhost:8000/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content_id: contentId,
          interaction_type: feedback
        })
      })
    } catch (error) {
      console.error('Error submitting feedback:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <Link href="/dashboard" className="text-2xl font-bold text-blue-600">
              AutoCurate
            </Link>
            <nav className="flex items-center space-x-6">
              <Link href="/dashboard" className="text-gray-600 hover:text-gray-900">
                Dashboard
              </Link>
              <Link href="/settings" className="text-gray-600 hover:text-gray-900">
                Settings
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Search Form */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">Search Content</h1>
          
          <form onSubmit={handleSearch} className="mb-6">
            <div className="flex gap-4">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search for articles, topics, or keywords..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <Button
                type="submit"
                disabled={loading || !query.trim()}
                className="px-6 py-3"
              >
                {loading ? 'Searching...' : 'Search'}
              </Button>
            </div>
          </form>

          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            <select
              value={filters.dateRange}
              onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-lg"
              aria-label="Filter by date range"
            >
              <option value="">Any time</option>
              <option value="today">Today</option>
              <option value="week">This week</option>
              <option value="month">This month</option>
            </select>

            <select
              value={filters.contentType}
              onChange={(e) => setFilters(prev => ({ ...prev, contentType: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-lg"
              aria-label="Filter by content type"
            >
              <option value="">All content</option>
              <option value="news">News</option>
              <option value="research">Research</option>
              <option value="blog">Blog posts</option>
            </select>

            <input
              type="text"
              value={filters.source}
              onChange={(e) => setFilters(prev => ({ ...prev, source: e.target.value }))}
              placeholder="Filter by source..."
              className="px-3 py-2 border border-gray-300 rounded-lg"
              aria-label="Filter by source"
            />
          </div>
        </div>

        {/* Results */}
        <div>
          {loading && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Searching...</p>
            </div>
          )}

          {!loading && results.length > 0 && (
            <div>
              <p className="text-gray-600 mb-6">
                Found {results.length} results for "{query}"
              </p>
              
              <div className="space-y-6">
                {results.map((result) => (
                  <div key={result.id} className="bg-white rounded-lg shadow-sm border p-6">
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="text-xl font-semibold text-gray-900">
                        {result.title}
                      </h3>
                      <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {Math.round(result.relevance_score * 100)}% match
                      </span>
                    </div>
                    
                    <p className="text-gray-700 mb-4 line-clamp-3">
                      {result.summary}
                    </p>
                    
                    <div className="flex justify-between items-center">
                      <div className="flex items-center text-sm text-gray-500">
                        <span className="font-medium">{result.source}</span>
                        <span className="mx-2">•</span>
                        <span>{new Date(result.published_at).toLocaleDateString()}</span>
                      </div>
                      
                      <div className="flex items-center space-x-3">
                        <button
                          onClick={() => handleFeedback(result.id, 'like')}
                          className="p-2 rounded-full hover:bg-green-100 text-green-600"
                          title="Like"
                        >
                          👍
                        </button>
                        <button
                          onClick={() => handleFeedback(result.id, 'dislike')}
                          className="p-2 rounded-full hover:bg-red-100 text-red-600"
                          title="Dislike"
                        >
                          👎
                        </button>
                        <a
                          href={result.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 font-medium"
                        >
                          Read Article →
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!loading && query && results.length === 0 && (
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">
                <span className="text-4xl">🔍</span>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No results found
              </h3>
              <p className="text-gray-600">
                Try adjusting your search terms or filters.
              </p>
            </div>
          )}

          {!loading && !query && (
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">
                <span className="text-4xl">🔍</span>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Search for content
              </h3>
              <p className="text-gray-600">
                Enter keywords to find relevant articles and summaries.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SearchPage
