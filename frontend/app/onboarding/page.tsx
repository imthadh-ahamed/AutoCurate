'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

interface Preferences {
  topics: string[]
  contentTypes: string[]
  frequency: string
  sources: string[]
}

const OnboardingPage = () => {
  const [currentStep, setCurrentStep] = useState(1)
  const [preferences, setPreferences] = useState<Preferences>({
    topics: [],
    contentTypes: [],
    frequency: '',
    sources: []
  })

  const topics = [
    'Technology', 'Science', 'Business', 'Health', 'Politics', 
    'Sports', 'Entertainment', 'Education', 'Environment', 'Finance'
  ]

  const contentTypes = [
    'News Articles', 'Research Papers', 'Blog Posts', 'Tutorials', 
    'Industry Reports', 'Podcasts', 'Videos', 'White Papers'
  ]

  const frequencies = [
    { value: 'daily', label: 'Daily' },
    { value: 'weekly', label: 'Weekly' },
    { value: 'realtime', label: 'Real-time' }
  ]

  const handleTopicToggle = (topic: string) => {
    setPreferences(prev => ({
      ...prev,
      topics: prev.topics.includes(topic)
        ? prev.topics.filter(t => t !== topic)
        : [...prev.topics, topic]
    }))
  }

  const handleContentTypeToggle = (type: string) => {
    setPreferences(prev => ({
      ...prev,
      contentTypes: prev.contentTypes.includes(type)
        ? prev.contentTypes.filter(t => t !== type)
        : [...prev.contentTypes, type]
    }))
  }

  const getProgressWidth = (step: number) => {
    switch (step) {
      case 1: return 'w-1/4'
      case 2: return 'w-2/4' 
      case 3: return 'w-3/4'
      case 4: return 'w-full'
      default: return 'w-0'
    }
  }

  const handleNext = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSubmit = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/users/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(preferences)
      })
      
      if (response.ok) {
        window.location.href = '/dashboard'
      }
    } catch (error) {
      console.error('Error saving preferences:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-2xl mx-auto px-4">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <span className="text-sm font-medium text-gray-500">Step {currentStep} of 4</span>
            <span className="text-sm font-medium text-gray-500">{Math.round((currentStep / 4) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`bg-blue-600 h-2 rounded-full transition-all duration-300 ${getProgressWidth(currentStep)}`}
            />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-8">
          {currentStep === 1 && (
            <div>
              <h2 className="text-2xl font-bold mb-4">Welcome to AutoCurate!</h2>
              <p className="text-gray-600 mb-8">
                Let's personalize your experience. We'll ask you a few questions to understand your interests and preferences.
              </p>
              
              <h3 className="text-lg font-semibold mb-4">What topics interest you?</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {topics.map((topic) => (
                  <button
                    key={topic}
                    onClick={() => handleTopicToggle(topic)}
                    className={`p-3 rounded-lg border text-sm font-medium transition-colors ${
                      preferences.topics.includes(topic)
                        ? 'bg-blue-100 border-blue-500 text-blue-700'
                        : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    {topic}
                  </button>
                ))}
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div>
              <h2 className="text-2xl font-bold mb-4">Content Preferences</h2>
              <p className="text-gray-600 mb-8">
                What types of content do you prefer to read?
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {contentTypes.map((type) => (
                  <button
                    key={type}
                    onClick={() => handleContentTypeToggle(type)}
                    className={`p-4 rounded-lg border text-left transition-colors ${
                      preferences.contentTypes.includes(type)
                        ? 'bg-blue-100 border-blue-500 text-blue-700'
                        : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>
          )}

          {currentStep === 3 && (
            <div>
              <h2 className="text-2xl font-bold mb-4">Update Frequency</h2>
              <p className="text-gray-600 mb-8">
                How often would you like to receive new content?
              </p>
              
              <div className="space-y-3">
                {frequencies.map((freq) => (
                  <button
                    key={freq.value}
                    onClick={() => setPreferences(prev => ({ ...prev, frequency: freq.value }))}
                    className={`w-full p-4 rounded-lg border text-left transition-colors ${
                      preferences.frequency === freq.value
                        ? 'bg-blue-100 border-blue-500 text-blue-700'
                        : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <div className="font-medium">{freq.label}</div>
                    <div className="text-sm text-gray-500">
                      {freq.value === 'daily' && 'Get a daily digest of curated content'}
                      {freq.value === 'weekly' && 'Receive a weekly summary of top content'}
                      {freq.value === 'realtime' && 'Get notified as new relevant content is found'}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {currentStep === 4 && (
            <div>
              <h2 className="text-2xl font-bold mb-4">You're All Set!</h2>
              <p className="text-gray-600 mb-8">
                Great! We've captured your preferences. Our AI will now start curating personalized content for you.
              </p>
              
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <h4 className="font-semibold text-blue-900 mb-2">Your Preferences Summary:</h4>
                <div className="text-sm text-blue-800">
                  <p><strong>Topics:</strong> {preferences.topics.join(', ')}</p>
                  <p><strong>Content Types:</strong> {preferences.contentTypes.join(', ')}</p>
                  <p><strong>Frequency:</strong> {preferences.frequency}</p>
                </div>
              </div>
              
              <p className="text-sm text-gray-500 mb-6">
                You can always update these preferences later in your settings.
              </p>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between mt-8 pt-6 border-t">
            <Button
              onClick={handlePrevious}
              disabled={currentStep === 1}
              variant="outline"
            >
              Previous
            </Button>
            
            {currentStep < 4 ? (
              <Button
                onClick={handleNext}
                disabled={
                  (currentStep === 1 && preferences.topics.length === 0) ||
                  (currentStep === 2 && preferences.contentTypes.length === 0) ||
                  (currentStep === 3 && !preferences.frequency)
                }
              >
                Next
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
              >
                Complete Setup
              </Button>
            )}
          </div>
        </div>

        <div className="text-center mt-6">
          <Link href="/" className="text-sm text-gray-500 hover:text-gray-700">
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  )
}

export default OnboardingPage
