'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { experiencesApi } from '@/lib/api'
import { type ExperimentExperience } from '@/types'

export default function ExperiencesPage() {
  const [experiences, setExperiences] = useState<ExperimentExperience[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [searching, setSearching] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const data = await experiencesApi.list()
      setExperiences(data)
    } catch (error) {
      console.error('Failed to load experiences:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) {
      loadData()
      return
    }
    setSearching(true)
    try {
      const results = await experiencesApi.search(searchQuery)
      setExperiences(results)
    } catch (error) {
      console.error('Failed to search:', error)
    } finally {
      setSearching(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-purple-50">
      <header className="bg-white/80 backdrop-blur-sm shadow-sm border-b border-purple-100">
        <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/experiments"
                className="p-2 hover:bg-purple-50 rounded-lg transition-colors cursor-pointer"
              >
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </Link>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
                  Experience Library
                </h1>
                <p className="text-sm text-gray-500">Lessons learned from experiments</p>
              </div>
            </div>
            <Link
              href="/experiences/user"
              className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-colors text-sm cursor-pointer"
            >
              Cross-Agent Experiences
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Search */}
          <form onSubmit={handleSearch} className="mb-6">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Search experiences..."
                  className="w-full px-4 py-3 pl-10 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                />
                <svg
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
              <button
                type="submit"
                disabled={searching}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-colors disabled:opacity-50 cursor-pointer"
              >
                {searching ? 'Searching...' : 'Search'}
              </button>
            </div>
          </form>

          {/* Experiences List */}
          {experiences.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-12 text-center">
              <div className="text-6xl mb-4">💡</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No experiences yet</h3>
              <p className="text-gray-500 mb-6">
                Run experiments and record your learnings to build your experience library
              </p>
              <Link
                href="/experiments"
                className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-colors cursor-pointer"
              >
                Go to Experiments
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {experiences.map(exp => (
                <div
                  key={exp.id}
                  className="bg-white rounded-xl shadow-sm border border-purple-100 p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="text-lg font-semibold text-gray-900">{exp.summary}</h3>
                    <span className="text-xs text-gray-400">
                      {new Date(exp.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  {exp.lessons_learned && (
                    <div className="mb-3">
                      <h4 className="text-sm font-medium text-purple-600 mb-1">📚 Lessons Learned</h4>
                      <p className="text-sm text-gray-600">{exp.lessons_learned}</p>
                    </div>
                  )}

                  {exp.improvements && (
                    <div className="mb-3">
                      <h4 className="text-sm font-medium text-indigo-600 mb-1">💡 Improvements</h4>
                      <p className="text-sm text-gray-600">{exp.improvements}</p>
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                    <span className="text-xs text-gray-400">
                      Related experiments: {exp.related_experiments?.length || 0}
                    </span>
                    <Link
                      href={`/experiments/${exp.experiment_id}`}
                      className="text-sm text-purple-600 hover:text-purple-700 cursor-pointer"
                    >
                      View Original →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
