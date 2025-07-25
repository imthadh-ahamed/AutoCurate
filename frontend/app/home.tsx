import Link from 'next/link'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="flex justify-center mb-6">
            <span className="px-4 py-2 text-sm font-medium bg-blue-100 text-blue-800 rounded-full">
              🚀 AI-Powered Knowledge Feed
            </span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            AutoCurate
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-600 max-w-3xl mx-auto mb-8">
            Discover personalized content that matters to you. 
            Our AI learns your preferences and curates the most relevant 
            articles, insights, and knowledge from across the web.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/onboarding" className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg text-lg transition-colors">
              Get Started
            </Link>
            
            <Link href="/demo" className="border border-blue-600 text-blue-600 hover:bg-blue-50 font-semibold py-3 px-8 rounded-lg text-lg transition-colors">
              View Demo
            </Link>
          </div>
        </div>

        {/* Features Section */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
          {[
            {
              title: "AI-Powered Curation",
              description: "Advanced algorithms analyze and curate content based on your interests and reading patterns."
            },
            {
              title: "Personalized Experience", 
              description: "Tailored content recommendations that evolve with your preferences and feedback."
            },
            {
              title: "Smart Summarization",
              description: "Get concise, intelligent summaries of lengthy articles and content pieces."
            },
            {
              title: "Continuous Learning",
              description: "The system learns from your interactions to provide increasingly relevant content."
            }
          ].map((feature, index) => (
            <div key={feature.title} className="bg-white rounded-lg shadow-sm border p-6 h-full">
              <div className="mx-auto w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <span className="text-blue-600 text-xl">🧠</span>
              </div>
              <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
              <p className="text-gray-600 text-center">
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        {/* How It Works Section */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-8">How It Works</h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mb-4">
                1
              </div>
              <h3 className="text-xl font-semibold mb-2">Tell Us Your Interests</h3>
              <p className="text-gray-600">
                Complete a quick survey to help us understand your preferences and topics of interest.
              </p>
            </div>
            
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mb-4">
                2
              </div>
              <h3 className="text-xl font-semibold mb-2">AI Curates Content</h3>
              <p className="text-gray-600">
                Our AI scans thousands of sources and selects the most relevant content for you.
              </p>
            </div>
            
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mb-4">
                3
              </div>
              <h3 className="text-xl font-semibold mb-2">Enjoy Personalized Feed</h3>
              <p className="text-gray-600">
                Read curated summaries and provide feedback to improve future recommendations.
              </p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center">
          <div className="max-w-2xl mx-auto bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg p-8">
            <h3 className="text-2xl md:text-3xl font-bold mb-4">
              Ready to Transform Your Reading Experience?
            </h3>
            <p className="text-lg mb-6 opacity-90">
              Join thousands of users who have already discovered the power of personalized content curation.
            </p>
            <Link href="/onboarding" className="bg-white text-blue-600 hover:bg-gray-100 font-semibold py-3 px-8 rounded-lg text-lg transition-colors inline-block">
              Start Your Journey
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
