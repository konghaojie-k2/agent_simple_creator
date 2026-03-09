'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { skillsApi } from '@/lib/api'
import { Skill } from '@/types'

const categoryLabels: Record<string, string> = {
  tool: 'Tool',
  template: 'Template',
  prompt: 'Prompt',
  custom: 'Custom',
}

type TabType = 'all' | 'public' | 'private'

interface FilesystemSkill {
  name: string
  description: string
  category: string
  tags: string[]
  allowed_tools: string[]
  folder_name: string
}

export default function SkillsMarketPage() {
  const [skills, setSkills] = useState<Skill[]>([])
  const [builtinSkills, setBuiltinSkills] = useState<FilesystemSkill[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [activeTab, setActiveTab] = useState<TabType>('all')

  const loadBuiltinSkills = async () => {
    try {
      const data = await skillsApi.listFilesystem()
      setBuiltinSkills(data)
    } catch (error) {
      console.error('Failed to load built-in skills:', error)
      setBuiltinSkills([])
    }
  }

  const loadSkills = async () => {
    // Private tab only shows user's private skills (no builtin)
    // All and Public tabs always include builtin skills
    if (activeTab === 'private') {
      setLoading(true)
      try {
        const data = await skillsApi.list({ is_public: false })
        setSkills(data)
      } catch (error) {
        console.error('Failed to load skills:', error)
      } finally {
        setLoading(false)
      }
    } else {
      // All and Public: load database skills + builtin skills
      setLoading(true)
      try {
        // Load all database skills
        const data = await skillsApi.list({})
        setSkills(data)
      } catch (error) {
        console.error('Failed to load skills:', error)
      } finally {
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    loadSkills()
    loadBuiltinSkills()
  }, [activeTab])

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this skill?')) return
    try {
      await skillsApi.delete(id)
      loadSkills()
    } catch (error) {
      console.error('Failed to delete skill:', error)
    }
  }

  const handleToggleVisibility = async (skill: Skill) => {
    try {
      await skillsApi.updateVisibility(skill.id, !skill.is_public)
      loadSkills()
    } catch (error) {
      console.error('Failed to update visibility:', error)
    }
  }

  // For "all" and "public" tabs, also show builtin skills
  const showBuiltin = activeTab === 'all' || activeTab === 'public'

  const filteredDbSkills = skills.filter(s =>
    s.name.toLowerCase().includes(filter.toLowerCase()) ||
    s.description?.toLowerCase().includes(filter.toLowerCase())
  )

  // Filter public database skills for public tab
  const filteredPublicDbSkills = activeTab === 'public'
    ? filteredDbSkills.filter(s => s.is_public)
    : filteredDbSkills

  // Combine with builtin skills if needed
  const filteredBuiltin = showBuiltin
    ? builtinSkills.filter(s =>
        s.name.toLowerCase().includes(filter.toLowerCase()) ||
        s.description.toLowerCase().includes(filter.toLowerCase())
      )
    : []

  const tabs: { key: TabType; label: string }[] = [
    { key: 'all', label: 'All' },
    { key: 'public', label: 'Public' },
    { key: 'private', label: 'Private' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-purple-50">
      <header className="bg-white/80 backdrop-blur-sm shadow-sm border-b border-purple-100">
        <div className="max-w-6xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
                Skill Market
              </h1>
              <p className="text-sm text-gray-500">Manage your reusable skills</p>
            </div>
            <Link
              href="/markets/skills/new"
              className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-colors cursor-pointer"
            >
              Create Skill
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 sm:px-0">
          {/* Tabs */}
          <div className="flex gap-2 mb-6">
            {tabs.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab.key
                    ? 'bg-purple-600 text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Filters */}
          <div className="mb-6">
            <input
              type="text"
              placeholder="Search skills..."
              value={filter}
              onChange={e => setFilter(e.target.value)}
              className="w-full max-w-md px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
            />
          </div>

          {/* Skills Grid */}
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
            </div>
          ) : (filteredDbSkills.length === 0 && filteredBuiltin.length === 0) ? (
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-12 text-center">
              <div className="text-6xl mb-4">🛠️</div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">No Skills Found</h2>
              <p className="text-gray-500 mb-6">
                {activeTab === 'all'
                  ? 'Create your first skill to get started'
                  : activeTab === 'public'
                  ? 'No public skills available (including built-in)'
                  : 'You have no private skills yet'}
              </p>
              <Link
                href="/markets/skills/new"
                className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-colors cursor-pointer"
              >
                Create Skill
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Built-in Skills */}
              {filteredBuiltin.map(skill => (
                <div
                  key={`builtin-${skill.folder_name}`}
                  className="bg-white rounded-xl shadow-sm border border-purple-100 p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900">{skill.name}</h3>
                      <div className="flex gap-2 mt-1">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          {categoryLabels[skill.category] || skill.category}
                        </span>
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                          Built-in
                        </span>
                      </div>
                    </div>
                  </div>
                  {skill.description && (
                    <p className="text-sm text-gray-500 mb-3 line-clamp-2">{skill.description}</p>
                  )}
                  {skill.tags && skill.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {skill.tags.map((tag: string) => (
                        <span key={tag} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="flex gap-2">
                    <button
                      className="flex-1 text-center px-3 py-1.5 text-sm border border-purple-200 text-purple-600 rounded-lg hover:bg-purple-50 transition-colors cursor-pointer"
                    >
                      View
                    </button>
                  </div>
                </div>
              ))}
              {/* Database Skills */}
              {filteredDbSkills.map(skill => (
                <div
                  key={skill.id}
                  className="bg-white rounded-xl shadow-sm border border-purple-100 p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900">{skill.name}</h3>
                      <div className="flex gap-2 mt-1">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          {categoryLabels[skill.category] || skill.category}
                        </span>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          skill.is_public
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {skill.is_public ? 'Public' : 'Private'}
                        </span>
                      </div>
                    </div>
                  </div>
                  {skill.description && (
                    <p className="text-sm text-gray-500 mb-3 line-clamp-2">{skill.description}</p>
                  )}
                  <div className="flex items-center justify-between text-xs text-gray-400 mb-4">
                    <span>{skill.usage_count} uses</span>
                    <span>{new Date(skill.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex gap-2">
                    <Link
                      href={`/markets/skills/${skill.id}`}
                      className="flex-1 text-center px-3 py-1.5 text-sm border border-purple-200 text-purple-600 rounded-lg hover:bg-purple-50 transition-colors cursor-pointer"
                    >
                      View
                    </Link>
                    {skill.source === 'database' && (
                      <button
                        onClick={() => handleToggleVisibility(skill)}
                        className="px-3 py-1.5 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        {skill.is_public ? 'Make Private' : 'Make Public'}
                      </button>
                    )}
                    {skill.source === 'database' && (
                      <button
                        onClick={() => handleDelete(skill.id)}
                        className="px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        Delete
                      </button>
                    )}
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
