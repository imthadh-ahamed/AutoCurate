export default function HomePage() {
  return (
    <div className="min-h-screen bg-white">
      <header className="bg-blue-600 text-white py-6">
        <div className="max-w-7xl mx-auto px-4">
          <h1 className="text-3xl font-bold">AutoCurate</h1>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-4 py-12">
        <div className="text-center">
          <h2 className="text-4xl font-bold text-gray-900 mb-6">
            Your AI-Powered Knowledge Feed
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            AutoCurate uses advanced AI to understand your interests and deliver personalized content summaries.
          </p>
          
          <div className="space-x-4">
            <a 
              href="/onboarding" 
              className="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Get Started
            </a>
            <a 
              href="/demo" 
              className="inline-block border border-blue-600 text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
            >
              View Demo
            </a>
          </div>
        </div>
        
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center p-6 border border-gray-200 rounded-lg">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="text-xl font-semibold mb-2">AI-Powered Curation</h3>
            <p className="text-gray-600">Advanced algorithms learn your preferences and curate relevant content.</p>
          </div>
          
          <div className="text-center p-6 border border-gray-200 rounded-lg">
            <div className="text-4xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold mb-2">Personalized Summaries</h3>
            <p className="text-gray-600">Get concise, AI-generated summaries tailored to your interests.</p>
          </div>
          
          <div className="text-center p-6 border border-gray-200 rounded-lg">
            <div className="text-4xl mb-4">✨</div>
            <h3 className="text-xl font-semibold mb-2">Smart Learning</h3>
            <p className="text-gray-600">The system continuously improves by learning from your feedback.</p>
          </div>
        </div>
      </main>
    </div>
  )
}
