'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { experimentsApi, agentsApi } from '@/lib/api'
import { type Experiment, type Agent } from '@/types'

const statusColors = {
  pending: 'bg-gray-100 text-gray-800',
  running: 'bg-blue-100 text-blue-800',
  success: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
}

const typeLabels = {
  skill_creation: 'Skill Creation',
  document: 'Document',
  document_generation: 'Document Generation',
  problem_solving: 'Problem Solving',
  data_analysis: 'Data Analysis',
  collaboration: 'Multi-Agent Collaboration',
  custom: 'Custom',
}

export default function ExperimentsPage() {
  const [experiments, setExperiments] = useState<Experiment[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState({ type: '', status: '' })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [experimentsData, agentsData] = await Promise.all([
        experimentsApi.list(),
        agentsApi.list(),
      ])
      setExperiments(experimentsData)
      setAgents(agentsData)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredExperiments = experiments.filter(exp => {
    if (filter.type && exp.experiment_type !== filter.type) return false
    if (filter.status && exp.status !== filter.status) return false
    return true
  })

  const getAgentName = (agentId: string) => {
    const agent = agents.find(a => a.id === agentId)
    return agent?.name || 'Unknown Agent'
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this experiment?')) return
    try {
      await experimentsApi.delete(id)
      loadData()
    } catch (error) {
      console.error('Failed to delete experiment:', error)
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
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
                Experiment Arena
              </h1>
              <p className="text-sm text-gray-500 mt-1">Run AI experiments and document your learnings</p>
            </div>
            <div className="flex gap-3">
              <Link
                href="/templates"
                className="px-4 py-2 bg-white border border-purple-200 text-purple-600 rounded-lg hover:bg-purple-50 transition-colors cursor-pointer"
              >
                Templates
              </Link>
              <Link
                href="/experiences"
                className="px-4 py-2 bg-white border border-purple-200 text-purple-600 rounded-lg hover:bg-purple-50 transition-colors cursor-pointer"
              >
                Experiences
              </Link>
              <Link
                href="/experiments/new-collaboration"
                className="px-4 py-2 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors cursor-pointer"
              >
                Multi-Agent
              </Link>
              <Link
                href="/experiments/new"
                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-colors shadow-md cursor-pointer"
              >
                New Experiment
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Filters */}
          <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-4 mb-6">
            <div className="flex gap-4 flex-wrap">
              <select
                value={filter.type}
                onChange={e => setFilter({ ...filter, type: e.target.value })}
                className="px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 cursor-pointer"
              >
                <option value="">All Types</option>
                <option value="document">Document</option>
                <option value="document_generation">Document Generation</option>
                <option value="skill_creation">Skill Creation</option>
                <option value="problem_solving">Problem Solving</option>
                <option value="data_analysis">Data Analysis</option>
                <option value="collaboration">Multi-Agent Collaboration</option>
                <option value="custom">Custom</option>
              </select>
              <select
                value={filter.status}
                onChange={e => setFilter({ ...filter, status: e.target.value })}
                className="px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 cursor-pointer"
              >
                <option value="">All Status</option>
                <option value="pending">Pending</option>
                <option value="running">Running</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
              </select>
            </div>
          </div>

          {/* Experiments Grid */}
          {filteredExperiments.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-12 text-center">
              <div className="text-6xl mb-4">🧪</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No experiments yet</h3>
              <p className="text-gray-500 mb-6">Create your first experiment to get started</p>
              <Link
                href="/experiments/new"
                className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-colors cursor-pointer"
              >
                Create Experiment
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredExperiments.map(exp => (
                <div
                  key={exp.id}
                  className="bg-white rounded-xl shadow-sm border border-purple-100 hover:shadow-md transition-shadow"
                >
                  <div className="p-5">
                    <div className="flex justify-between items-start mb-3">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[exp.status as keyof typeof statusColors]}`}>
                        {exp.status}
                      </span>
                      <span className="text-xs text-gray-500">
                        {typeLabels[exp.experiment_type as keyof typeof typeLabels] || exp.experiment_type}
                      </span>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">{exp.name}</h3>
                    <p className="text-sm text-gray-500 mb-3 line-clamp-2">
                      {exp.description || 'No description'}
                    </p>
                    <div className="flex items-center text-xs text-gray-400 mb-4">
                      <span className="bg-purple-50 text-purple-600 px-2 py-0.5 rounded">
                        {getAgentName(exp.agent_id)}
                      </span>
                      <span className="mx-2">• {new Date(exp.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex gap-2">
                      <Link
                        href={`/experiments/${exp.id}`}
                        className="flex-1 text-center px-3 py-2 bg-purple-50 text-purple-600 rounded-lg hover:bg-purple-100 transition-colors text-sm cursor-pointer"
                      >
                        View
                      </Link>
                      {exp.status === 'pending' && (
                        <button
                          onClick={() => experimentsApi.run(exp.id)}
                          className="flex-1 text-center px-3 py-2 bg-green-50 text-green-600 rounded-lg hover:bg-green-100 transition-colors text-sm cursor-pointer"
                        >
                          Run
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(exp.id)}
                        className="px-3 py-2 text-red-400 hover:text-red-600 transition-colors cursor-pointer"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
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
