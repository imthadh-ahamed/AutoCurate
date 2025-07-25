'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface ContentItem {
  id: number
  title: string
  summary: string
  url: string
  source: string
  published_at: string
  read_time_minutes: number
}

interface UserSummary {
  id: number
  title: string
  summary_text: string
  content_count: number
  created_at: string
  read_time_minutes: number
}

const DashboardPage = () => {
  const [summaries, setSummaries] = useState<UserSummary[]>([])
  const [recentContent, setRecentContent] = useState<ContentItem[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('summaries')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      
      // Fetch user summaries
      const userId = localStorage.getItem('user_id') || '1'; // Default to 1 if not set
      const summariesResponse = await fetch(`http://localhost:8000/api/users/${userId}/summaries`)
      if (summariesResponse.ok) {
        const summariesData = await summariesResponse.json()
        setSummaries(summariesData)
      }

      // Fetch recent content
      const contentResponse = await fetch('http://localhost:8000/api/content/recent')
      if (contentResponse.ok) {
        const contentData = await contentResponse.json()
        setRecentContent(contentData)
      }
    } catch (error) {
      console.error('Error fetching data:', error)
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
      // Optionally refresh data or show success message
    } catch (error) {
      console.error('Error submitting feedback:', error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your personalized content...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-blue-600">AutoCurate</h1>
              <span className="ml-2 text-sm text-gray-500">Dashboard</span>
            </div>
            
            <nav className="flex items-center space-x-6">
              <Link href="/search" className="text-gray-600 hover:text-gray-900">
                Search
              </Link>
              <Link href="/settings" className="text-gray-600 hover:text-gray-900">
                Settings
              </Link>
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 font-medium">U</span>
              </div>
            </nav>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Good morning! 👋
          </h2>
          <p className="text-gray-600">
            Here's your personalized content feed for today.
          </p>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('summaries')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'summaries'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                AI Summaries ({summaries.length})
              </button>
              <button
                onClick={() => setActiveTab('content')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'content'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Recent Articles ({recentContent.length})
              </button>
            </nav>
          </div>
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            {activeTab === 'summaries' && (
              <div className="space-y-6">
                {summaries.length > 0 ? (
                  summaries.map((summary) => (
                    <div key={summary.id} className="bg-white rounded-lg shadow-sm border p-6">
                      <div className="flex justify-between items-start mb-4">
                        <h3 className="text-xl font-semibold text-gray-900">
                          {summary.title}
                        </h3>
                        <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                          {summary.read_time_minutes} min read
                        </span>
                      </div>
                      
                      <p className="text-gray-700 leading-relaxed mb-4">
                        {summary.summary_text}
                      </p>
                      
                      <div className="flex justify-between items-center text-sm text-gray-500">
                        <span>
                          Based on {summary.content_count} articles
                        </span>
                        <span>
                          {new Date(summary.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-12">
                    <div className="text-gray-400 mb-4">
                      <span className="text-4xl">📄</span>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      No summaries yet
                    </h3>
                    <p className="text-gray-600">
                      Your AI-generated summaries will appear here once content is processed.
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'content' && (
              <div className="space-y-4">
                {recentContent.length > 0 ? (
                  recentContent.map((item) => (
                    <div key={item.id} className="bg-white rounded-lg shadow-sm border p-6">
                      <div className="flex justify-between items-start mb-3">
                        <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
                          {item.title}
                        </h3>
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded ml-2">
                          {item.read_time_minutes} min
                        </span>
                      </div>
                      
                      <p className="text-gray-700 text-sm mb-4 line-clamp-3">
                        {item.summary}
                      </p>
                      
                      <div className="flex justify-between items-center">
                        <div className="flex items-center text-sm text-gray-500">
                          <span className="font-medium">{item.source}</span>
                          <span className="mx-2">•</span>
                          <span>{new Date(item.published_at).toLocaleDateString()}</span>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleFeedback(item.id, 'like')}
                            className="p-2 rounded-full hover:bg-green-100 text-green-600"
                            title="Like"
                          >
                            👍
                          </button>
                          <button
                            onClick={() => handleFeedback(item.id, 'dislike')}
                            className="p-2 rounded-full hover:bg-red-100 text-red-600"
                            title="Dislike"
                          >
                            👎
                          </button>
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                          >
                            Read More →
                          </a>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-12">
                    <div className="text-gray-400 mb-4">
                      <span className="text-4xl">📰</span>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      No content yet
                    </h3>
                    <p className="text-gray-600">
                      We're still gathering content based on your preferences. Check back soon!
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Today's Stats
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">New Articles</span>
                  <span className="font-semibold">{recentContent.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">AI Summaries</span>
                  <span className="font-semibold">{summaries.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Reading Time</span>
                  <span className="font-semibold">
                    {recentContent.reduce((acc, item) => acc + item.read_time_minutes, 0)} min
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Quick Actions
              </h3>
              <div className="space-y-3">
                <button
                  onClick={fetchData}
                  className="w-full text-left p-3 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors"
                >
                  🔄 Refresh Feed
                </button>
                <Link
                  href="/search"
                  className="block w-full text-left p-3 rounded-lg bg-gray-50 text-gray-700 hover:bg-gray-100 transition-colors"
                >
                  🔍 Search Content
                </Link>
                <Link
                  href="/settings"
                  className="block w-full text-left p-3 rounded-lg bg-gray-50 text-gray-700 hover:bg-gray-100 transition-colors"
                >
                  ⚙️ Update Preferences
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
