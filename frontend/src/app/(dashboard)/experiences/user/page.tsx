'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { experiencesApi } from '@/lib/api'
import { UserExperience, ExperienceStatus } from '@/types'

export default function UserExperiencesPage() {
  const [experiences, setExperiences] = useState<UserExperience[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<ExperienceStatus | ''>('verified')
  const [limit, setLimit] = useState(20)

  useEffect(() => {
    loadExperiences()
  }, [statusFilter, limit])

  const loadExperiences = async () => {
    try {
      const token = document.cookie
        .split('; ')
        .find(row => row.startsWith('access_token='))
        ?.split('=')[1]

      if (!token) {
        console.error('No auth token found')
        return
      }

      const payload = JSON.parse(atob(token.split('.')[1]))
      const userId = payload.sub || payload.user_id

      const params: { status?: ExperienceStatus; limit?: number } = {}
      if (statusFilter) params.status = statusFilter
      if (limit) params.limit = limit

      const data = await experiencesApi.listUserExperiences(userId, params)
      setExperiences(data)
    } catch (error) {
      console.error('Failed to load experiences:', error)
    } finally {
      setLoading(false)
    }
  }

  const statusColors = {
    verified: 'bg-green-100 text-green-800',
    draft: 'bg-yellow-100 text-yellow-800',
    deprecated: 'bg-red-100 text-red-800',
  }

  const statusLabels = {
    verified: '已验证',
    draft: '草稿',
    deprecated: '已废弃',
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4">
            <Link
              href="/experiences"
              className="text-gray-600 hover:text-gray-900"
            >
              Back to Experiences
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">
              Cross-Agent Experiences
            </h1>
          </div>
          <p className="text-gray-500 mt-2">
            View experiences from all your agents and find reusable solutions
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white rounded-lg shadow p-4 mb-6">
            <div className="flex flex-wrap gap-4 items-center">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status Filter
                </label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as ExperienceStatus | '')}
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm"
                >
                  <option value="">All</option>
                  <option value="verified">Verified</option>
                  <option value="draft">Draft</option>
                  <option value="deprecated">Deprecated</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Limit
                </label>
                <select
                  value={limit}
                  onChange={(e) => setLimit(parseInt(e.target.value))}
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm"
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </div>
              <div className="ml-auto">
                <span className="text-sm text-gray-500">
                  {experiences.length} experiences
                </span>
              </div>
            </div>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <p className="text-gray-500">Loading...</p>
            </div>
          ) : experiences.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">No experiences found</p>
              <Link
                href="/experiments"
                className="mt-4 inline-block text-primary-600 hover:text-primary-700"
              >
                Run experiments to generate experiences
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {experiences.map((exp) => (
                <div key={exp.id} className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            statusColors[exp.status]
                          }`}
                        >
                          {statusLabels[exp.status]}
                        </span>
                        <span className="text-sm text-gray-500">
                          Agent: {exp.source_agent_id.slice(0, 8)}...
                        </span>
                        {exp.applied_count > 0 && (
                          <span className="text-sm text-gray-500">
                            Applied {exp.applied_count}x
                            {exp.success_count > 0 && ` (${exp.success_count} success)`}
                          </span>
                        )}
                      </div>

                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {exp.lesson}
                      </h3>

                      <div className="space-y-2 text-sm">
                        {exp.situation && (
                          <div>
                            <span className="font-medium text-gray-700">Situation:</span>
                            <span className="text-gray-600"> {exp.situation}</span>
                          </div>
                        )}
                        {exp.action && (
                          <div>
                            <span className="font-medium text-gray-700">Action:</span>
                            <span className="text-gray-600"> {exp.action}</span>
                          </div>
                        )}
                        {exp.result && (
                          <div>
                            <span className="font-medium text-gray-700">Result:</span>
                            <span className="text-gray-600"> {exp.result}</span>
                          </div>
                        )}
                        {exp.solution && (
                          <div className="mt-3 p-3 bg-blue-50 rounded-md">
                            <span className="font-medium text-gray-700">Solution:</span>
                            <p className="text-gray-700 mt-1">{exp.solution}</p>
                          </div>
                        )}

                        {exp.skills_used.length > 0 && (
                          <div className="mt-2">
                            <span className="font-medium text-gray-700">Skills Used:</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {exp.skills_used.map((skill, i) => (
                                <span
                                  key={i}
                                  className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                                >
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="mt-3 text-xs text-gray-500">
                        Created {new Date(exp.created_at).toLocaleString()}
                        {exp.last_applied_at && (
                          <span>
                            , last applied {new Date(exp.last_applied_at).toLocaleString()}
                          </span>
                        )}
                      </div>
                    </div>
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
