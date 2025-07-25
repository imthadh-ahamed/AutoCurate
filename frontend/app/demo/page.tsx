import Link from 'next/link'

export default function DemoPage() {
  const sampleSummaries = [
    {
      id: 1,
      title: "AI Breakthrough in Healthcare",
      summary: "Recent advances in artificial intelligence are revolutionizing medical diagnosis and treatment. Researchers have developed new algorithms that can detect diseases earlier and more accurately than traditional methods.",
      readTime: "5 min read",
      contentCount: 12,
      date: "Today"
    },
    {
      id: 2,
      title: "Climate Change Solutions",
      summary: "Scientists and engineers worldwide are developing innovative solutions to combat climate change. From carbon capture technology to renewable energy breakthroughs, these developments offer hope for a sustainable future.",
      readTime: "7 min read",
      contentCount: 8,
      date: "Yesterday"
    },
    {
      id: 3,
      title: "Space Exploration Updates",
      summary: "The latest missions to Mars and beyond are providing unprecedented insights into our solar system. New discoveries about potential life on other planets continue to captivate scientists and the public alike.",
      readTime: "4 min read",
      contentCount: 15,
      date: "2 days ago"
    }
  ]

  const sampleContent = [
    {
      id: 1,
      title: "Quantum Computing Reaches New Milestone",
      source: "TechNews Daily",
      excerpt: "Researchers at MIT have achieved a significant breakthrough in quantum computing, demonstrating error correction capabilities that bring practical quantum computers closer to reality.",
      date: "2 hours ago",
      readTime: "3 min"
    },
    {
      id: 2,
      title: "Revolutionary Gene Therapy Shows Promise",
      source: "Medical Journal",
      excerpt: "A new gene therapy approach has shown remarkable success in treating previously incurable genetic disorders, offering hope to millions of patients worldwide.",
      date: "4 hours ago",
      readTime: "6 min"
    }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <Link href="/" className="text-2xl font-bold text-blue-600">
              AutoCurate
            </Link>
            <div className="flex items-center space-x-4">
              <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm font-medium">
                DEMO MODE
              </span>
              <Link href="/" className="text-gray-600 hover:text-gray-900">
                Back to Home
              </Link>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Demo Notice */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-blue-900 mb-2">
            Welcome to the AutoCurate Demo! 🎉
          </h2>
          <p className="text-blue-800">
            This is a preview of how your personalized dashboard would look. 
            The content below is sample data to demonstrate the features and layout.
          </p>
        </div>

        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Good morning, Demo User! 👋
          </h1>
          <p className="text-gray-600">
            Here's your personalized content feed for today.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            {/* AI Summaries Section */}
            <div className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">
                AI-Generated Summaries
              </h2>
              
              <div className="space-y-6">
                {sampleSummaries.map((summary) => (
                  <div key={summary.id} className="bg-white rounded-lg shadow-sm border p-6">
                    <div className="flex justify-between items-start mb-4">
                      <h3 className="text-xl font-semibold text-gray-900">
                        {summary.title}
                      </h3>
                      <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {summary.readTime}
                      </span>
                    </div>
                    
                    <p className="text-gray-700 leading-relaxed mb-4">
                      {summary.summary}
                    </p>
                    
                    <div className="flex justify-between items-center text-sm text-gray-500">
                      <span>
                        Based on {summary.contentCount} articles
                      </span>
                      <span>
                        {summary.date}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Articles Section */}
            <div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">
                Recent Articles
              </h2>
              
              <div className="space-y-4">
                {sampleContent.map((article) => (
                  <div key={article.id} className="bg-white rounded-lg shadow-sm border p-6">
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {article.title}
                      </h3>
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded ml-2">
                        {article.readTime}
                      </span>
                    </div>
                    
                    <p className="text-gray-700 text-sm mb-4">
                      {article.excerpt}
                    </p>
                    
                    <div className="flex justify-between items-center">
                      <div className="flex items-center text-sm text-gray-500">
                        <span className="font-medium">{article.source}</span>
                        <span className="mx-2">•</span>
                        <span>{article.date}</span>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <button className="p-2 rounded-full hover:bg-green-100 text-green-600">
                          👍
                        </button>
                        <button className="p-2 rounded-full hover:bg-red-100 text-red-600">
                          👎
                        </button>
                        <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                          Read More →
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Stats */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Today's Stats
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">New Articles</span>
                  <span className="font-semibold">24</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">AI Summaries</span>
                  <span className="font-semibold">3</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Reading Time</span>
                  <span className="font-semibold">16 min</span>
                </div>
              </div>
            </div>

            {/* Demo Actions */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Try AutoCurate
              </h3>
              <div className="space-y-3">
                <Link
                  href="/onboarding"
                  className="block w-full text-center p-3 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                >
                  🚀 Get Started
                </Link>
                <div className="block w-full text-center p-3 rounded-lg bg-gray-50 text-gray-400 cursor-not-allowed">
                  🔍 Search (Demo)
                </div>
                <div className="block w-full text-center p-3 rounded-lg bg-gray-50 text-gray-400 cursor-not-allowed">
                  ⚙️ Settings (Demo)
                </div>
              </div>
            </div>

            {/* Features */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Features
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>AI-powered content curation</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Personalized summaries</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Smart content filtering</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Learning from feedback</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Multi-source aggregation</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-12 text-center">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg p-8 max-w-2xl mx-auto">
            <h3 className="text-2xl font-bold mb-4">
              Ready to Experience Personalized Content?
            </h3>
            <p className="text-lg mb-6 opacity-90">
              Start your journey with AutoCurate and never miss important content again.
            </p>
            <Link 
              href="/onboarding"
              className="bg-white text-blue-600 hover:bg-gray-100 font-semibold py-3 px-8 rounded-lg text-lg transition-colors inline-block"
            >
              Create Your Account
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
