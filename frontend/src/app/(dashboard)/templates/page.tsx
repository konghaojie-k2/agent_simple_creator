'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { templatesApi } from '@/lib/api'
import { ExperimentTemplate } from '@/types'

const typeIcons: Record<string, string> = {
  document: '📄',
  skill_creation: '🛠️',
  problem_solving: '🧩',
  data_analysis: '📊',
  custom: '⚡',
}

const typeLabels: Record<string, string> = {
  document: 'Document',
  skill_creation: 'Skill Creation',
  problem_solving: 'Problem Solving',
  data_analysis: 'Data Analysis',
  custom: 'Custom',
}

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<ExperimentTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const data = await templatesApi.list()
      setTemplates(data)
    } catch (error) {
      console.error('Failed to load templates:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredTemplates = templates.filter(t => {
    if (!filter) return true
    return t.experiment_type === filter
  })

  const groupedTemplates = filteredTemplates.reduce((acc, template) => {
    const type = template.experiment_type
    if (!acc[type]) acc[type] = []
    acc[type].push(template)
    return acc
  }, {} as Record<string, ExperimentTemplate[]>)

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
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
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
                  Template Marketplace
                </h1>
                <p className="text-sm text-gray-500">Pre-built experiment templates</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Filter */}
          <div className="flex gap-2 mb-6 flex-wrap">
            <button
              onClick={() => setFilter('')}
              className={`px-4 py-2 rounded-lg transition-colors cursor-pointer ${
                !filter ? 'bg-purple-600 text-white' : 'bg-white text-gray-600 hover:bg-purple-50'
              }`}
            >
              All
            </button>
            {Object.entries(typeLabels).map(([value, label]) => (
              <button
                key={value}
                onClick={() => setFilter(value)}
                className={`px-4 py-2 rounded-lg transition-colors cursor-pointer flex items-center gap-2 ${
                  filter === value ? 'bg-purple-600 text-white' : 'bg-white text-gray-600 hover:bg-purple-50'
                }`}
              >
                <span>{typeIcons[value]}</span>
                <span>{label}</span>
              </button>
            ))}
          </div>

          {templates.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-12 text-center">
              <div className="text-6xl mb-4">📋</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No templates available</h3>
              <p className="text-gray-500">Templates will appear here once created</p>
            </div>
          ) : (
            <div className="space-y-8">
              {Object.entries(groupedTemplates).map(([type, typeTemplates]) => (
                <div key={type}>
                  <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <span className="text-2xl">{typeIcons[type]}</span>
                    <span>{typeLabels[type] || type}</span>
                    <span className="text-sm font-normal text-gray-500">({typeTemplates.length})</span>
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {typeTemplates.map(template => (
                      <div
                        key={template.id}
                        className="bg-white rounded-xl shadow-sm border border-purple-100 hover:shadow-md transition-shadow p-5"
                      >
                        <h3 className="font-semibold text-gray-900 mb-2">{template.name}</h3>
                        <p className="text-sm text-gray-500 mb-4 line-clamp-2">
                          {template.description || 'No description'}
                        </p>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-400">
                            {template.is_public ? '🌐 Public' : '🔒 Private'}
                          </span>
                          <Link
                            href={`/experiments/new?template=${template.id}`}
                            className="text-sm text-purple-600 hover:text-purple-700 cursor-pointer"
                          >
                            Use Template →
                          </Link>
                        </div>
                      </div>
                    ))}
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
