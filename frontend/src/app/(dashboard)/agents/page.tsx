'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { agentsApi, providersApi } from '@/lib/api'
import { Agent, LLMProvider } from '@/types'

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [providers, setProviders] = useState<LLMProvider[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [newAgent, setNewAgent] = useState({
    name: '',
    description: '',
    system_prompt: '',
    provider_id: '',
    model: '',
    max_steps: 50,
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [agentsData, providersData] = await Promise.all([
        agentsApi.list(),
        providersApi.list(),
      ])
      setAgents(agentsData)
      setProviders(providersData.filter(p => p.is_active))
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await agentsApi.create(newAgent)
      setShowCreate(false)
      setNewAgent({
        name: '',
        description: '',
        system_prompt: '',
        provider_id: '',
        model: '',
        max_steps: 50,
      })
      loadData()
    } catch (error) {
      console.error('Failed to create agent:', error)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this agent?')) return
    try {
      await agentsApi.delete(id)
      loadData()
    } catch (error) {
      console.error('Failed to delete agent:', error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">Agents</h1>
            <Link
              href="/providers"
              className="text-primary-600 hover:text-primary-700"
            >
              Manage Providers
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-end mb-4">
            <button
              onClick={() => setShowCreate(!showCreate)}
              className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors"
            >
              {showCreate ? 'Cancel' : 'Create Agent'}
            </button>
          </div>

          {showCreate && (
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4">Create New Agent</h2>
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Name</label>
                  <input
                    type="text"
                    required
                    value={newAgent.name}
                    onChange={e => setNewAgent({ ...newAgent, name: e.target.value })}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Description</label>
                  <textarea
                    value={newAgent.description}
                    onChange={e => setNewAgent({ ...newAgent, description: e.target.value })}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    rows={2}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">System Prompt</label>
                  <textarea
                    value={newAgent.system_prompt}
                    onChange={e => setNewAgent({ ...newAgent, system_prompt: e.target.value })}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    rows={4}
                    placeholder="You are a helpful AI assistant..."
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Provider</label>
                    <select
                      required
                      value={newAgent.provider_id}
                      onChange={e => setNewAgent({ ...newAgent, provider_id: e.target.value })}
                      className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    >
                      <option value="">Select provider</option>
                      {providers.map(p => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({p.provider_type})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Model</label>
                    <input
                      type="text"
                      required
                      value={newAgent.model}
                      onChange={e => setNewAgent({ ...newAgent, model: e.target.value })}
                      className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                      placeholder="deepseek-chat"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Max Steps</label>
                  <input
                    type="number"
                    value={newAgent.max_steps}
                    onChange={e => setNewAgent({ ...newAgent, max_steps: parseInt(e.target.value) })}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    min={1}
                    max={100}
                  />
                </div>
                <button
                  type="submit"
                  className="w-full bg-primary-600 text-white py-2 px-4 rounded-md hover:bg-primary-700 transition-colors"
                >
                  Create Agent
                </button>
              </form>
            </div>
          )}

          {agents.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-4">No agents yet</p>
              <button
                onClick={() => setShowCreate(true)}
                className="text-primary-600 hover:text-primary-700"
              >
                Create your first agent
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {agents.map(agent => (
                <div key={agent.id} className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
                  <p className="text-sm text-gray-500 mt-1">{agent.description || 'No description'}</p>
                  <div className="mt-4 text-sm text-gray-600">
                    <p>Model: {agent.model}</p>
                    <p>Max Steps: {agent.max_steps}</p>
                  </div>
                  <div className="mt-4 flex gap-2">
                    <Link
                      href={`/agents/${agent.id}`}
                      className="flex-1 text-center bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 transition-colors"
                    >
                      Details
                    </Link>
                    <Link
                      href={`/chat/${agent.id}`}
                      className="flex-1 text-center bg-primary-600 text-white py-2 px-4 rounded-md hover:bg-primary-700 transition-colors"
                    >
                      Chat
                    </Link>
                    <button
                      onClick={() => handleDelete(agent.id)}
                      className="text-red-600 hover:text-red-700 px-3"
                    >
                      Delete
                    </button>
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
