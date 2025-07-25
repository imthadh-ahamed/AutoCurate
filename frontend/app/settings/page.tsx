'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

interface UserPreferences {
  topics: string[]
  contentTypes: string[]
  frequency: string
  sources: string[]
}

const SettingsPage = () => {
  const [preferences, setPreferences] = useState<UserPreferences>({
    topics: [],
    contentTypes: [],
    frequency: '',
    sources: []
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

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

  useEffect(() => {
    fetchPreferences()
  }, [])

  const fetchPreferences = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/users/preferences')
      if (response.ok) {
        const data = await response.json()
        setPreferences(data)
      }
    } catch (error) {
      console.error('Error fetching preferences:', error)
    } finally {
      setLoading(false)
    }
  }

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

  const handleSave = async () => {
    setSaving(true)
    try {
      const response = await fetch('http://localhost:8000/api/users/preferences', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(preferences)
      })
      
      if (response.ok) {
        setSaved(true)
        setTimeout(() => setSaved(false), 3000)
      }
    } catch (error) {
      console.error('Error saving preferences:', error)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading settings...</p>
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
            <Link href="/dashboard" className="text-2xl font-bold text-blue-600">
              AutoCurate
            </Link>
            <nav className="flex items-center space-x-6">
              <Link href="/dashboard" className="text-gray-600 hover:text-gray-900">
                Dashboard
              </Link>
              <Link href="/search" className="text-gray-600 hover:text-gray-900">
                Search
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
          <p className="text-gray-600">
            Customize your content preferences and account settings.
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border">
          {/* Content Preferences Section */}
          <div className="p-6 border-b">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Content Preferences
            </h2>
            
            {/* Topics */}
            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-3">
                Topics of Interest
              </h3>
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

            {/* Content Types */}
            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-3">
                Content Types
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {contentTypes.map((type) => (
                  <button
                    key={type}
                    onClick={() => handleContentTypeToggle(type)}
                    className={`p-3 rounded-lg border text-left transition-colors ${
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

            {/* Frequency */}
            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-3">
                Update Frequency
              </h3>
              <div className="space-y-2">
                {frequencies.map((freq) => (
                  <label key={freq.value} className="flex items-center" aria-label={`Select ${freq.label} frequency`}>
                    <input
                      type="radio"
                      name="frequency"
                      value={freq.value}
                      checked={preferences.frequency === freq.value}
                      onChange={(e) => setPreferences(prev => ({ 
                        ...prev, 
                        frequency: e.target.value 
                      }))}
                      className="mr-3 text-blue-600"
                      aria-describedby={`freq-${freq.value}-description`}
                    />
                    <div>
                      <div className="font-medium">{freq.label}</div>
                      <div id={`freq-${freq.value}-description`} className="text-sm text-gray-500">
                        {freq.value === 'daily' && 'Get a daily digest of curated content'}
                        {freq.value === 'weekly' && 'Receive a weekly summary of top content'}
                        {freq.value === 'realtime' && 'Get notified as new relevant content is found'}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Account Settings Section */}
          <div className="p-6 border-b">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Account Settings
            </h2>
            
            <div className="space-y-4">
              <div>
                <div className="block text-sm font-medium text-gray-700 mb-2">
                  Email Notifications
                </div>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      className="mr-2 text-blue-600"
                    />
                    <span className="text-sm">Daily summary emails</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      className="mr-2 text-blue-600"
                    />
                    <span className="text-sm">Breaking news alerts</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      className="mr-2 text-blue-600"
                    />
                    <span className="text-sm">Weekly digest</span>
                  </label>
                </div>
              </div>

              <div>
                <div className="block text-sm font-medium text-gray-700 mb-2">
                  Privacy Settings
                </div>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      className="mr-2 text-blue-600"
                      defaultChecked
                    />
                    <span className="text-sm">Allow data collection for personalization</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      className="mr-2 text-blue-600"
                    />
                    <span className="text-sm">Share anonymized usage data</span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* Data Management Section */}
          <div className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Data Management
            </h2>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div>
                  <h4 className="font-medium text-gray-900">Export Data</h4>
                  <p className="text-sm text-gray-600">
                    Download your reading history and preferences
                  </p>
                </div>
                <Button variant="outline">
                  Export
                </Button>
              </div>

              <div className="flex justify-between items-center p-4 bg-red-50 rounded-lg">
                <div>
                  <h4 className="font-medium text-red-900">Delete Account</h4>
                  <p className="text-sm text-red-600">
                    Permanently delete your account and all data
                  </p>
                </div>
                <Button variant="destructive">
                  Delete
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="mt-6 flex justify-end">
          {saved && (
            <div className="mr-4 py-2 px-4 bg-green-100 text-green-800 rounded-lg">
              Settings saved successfully!
            </div>
          )}
          <Button
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage
