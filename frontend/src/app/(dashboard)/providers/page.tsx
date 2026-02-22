'use client'

import { useEffect, useState } from 'react'
import { providersApi } from '@/lib/api'
import { LLMProvider } from '@/types'

// Default API bases for common providers
const PROVIDER_DEFAULTS: Record<string, { api_base: string; default_model: string }> = {
  deepseek: {
    api_base: 'https://api.deepseek.com/v1',
    default_model: 'deepseek-chat',
  },
  qwen: {
    api_base: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    default_model: 'qwen-plus',
  },
  openai: {
    api_base: 'https://api.openai.com/v1',
    default_model: 'gpt-4',
  },
}

export default function ProvidersPage() {
  const [providers, setProviders] = useState<LLMProvider[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [newProvider, setNewProvider] = useState({
    name: '',
    provider_type: 'deepseek',
    api_base: '',
    api_key: '',
    default_model: '',
    is_active: true,
  })

  useEffect(() => {
    loadProviders()
  }, [])

  const loadProviders = async () => {
    try {
      const data = await providersApi.list()
      setProviders(data)
    } catch (error) {
      console.error('Failed to load providers:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleProviderTypeChange = (type: string) => {
    const defaults = PROVIDER_DEFAULTS[type] || { api_base: '', default_model: '' }
    setNewProvider({
      ...newProvider,
      provider_type: type,
      api_base: defaults.api_base,
      default_model: defaults.default_model,
    })
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await providersApi.create(newProvider)
      setShowCreate(false)
      setNewProvider({
        name: '',
        provider_type: 'deepseek',
        api_base: '',
        api_key: '',
        default_model: '',
        is_active: true,
      })
      loadProviders()
    } catch (error) {
      console.error('Failed to create provider:', error)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this provider?')) return
    try {
      await providersApi.delete(id)
      loadProviders()
    } catch (error) {
      console.error('Failed to delete provider:', error)
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
            <h1 className="text-3xl font-bold text-gray-900">LLM Providers</h1>
            <Link
              href="/agents"
              className="text-primary-600 hover:text-primary-700"
            >
              Back to Agents
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
              {showCreate ? 'Cancel' : 'Add Provider'}
            </button>
          </div>

          {showCreate && (
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4">Add New Provider</h2>
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Provider Name</label>
                  <input
                    type="text"
                    required
                    value={newProvider.name}
                    onChange={e => setNewProvider({ ...newProvider, name: e.target.value })}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    placeholder="My DeepSeek API"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Provider Type</label>
                  <select
                    value={newProvider.provider_type}
                    onChange={e => handleProviderTypeChange(e.target.value)}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                  >
                    <option value="deepseek">DeepSeek</option>
                    <option value="qwen">Qwen (Alibaba)</option>
                    <option value="openai">OpenAI</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">API Base URL</label>
                  <input
                    type="url"
                    required
                    value={newProvider.api_base}
                    onChange={e => setNewProvider({ ...newProvider, api_base: e.target.value })}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    placeholder="https://api.example.com/v1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">API Key</label>
                  <input
                    type="password"
                    required
                    value={newProvider.api_key}
                    onChange={e => setNewProvider({ ...newProvider, api_key: e.target.value })}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    placeholder="sk-..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Default Model</label>
                  <input
                    type="text"
                    value={newProvider.default_model}
                    onChange={e => setNewProvider({ ...newProvider, default_model: e.target.value })}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    placeholder="deepseek-chat"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full bg-primary-600 text-white py-2 px-4 rounded-md hover:bg-primary-700 transition-colors"
                >
                  Add Provider
                </button>
              </form>
            </div>
          )}

          {providers.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-4">No providers configured</p>
              <button
                onClick={() => setShowCreate(true)}
                className="text-primary-600 hover:text-primary-700"
              >
                Add your first provider
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {providers.map(provider => (
                <div key={provider.id} className="bg-white rounded-lg shadow p-6">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{provider.name}</h3>
                      <span className="inline-block mt-1 px-2 py-1 text-xs font-medium bg-gray-100 rounded">
                        {provider.provider_type}
                      </span>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded ${provider.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                      {provider.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="mt-4 text-sm text-gray-600">
                    <p className="truncate">API Base: {provider.api_base}</p>
                    <p>Model: {provider.default_model || 'Not set'}</p>
                  </div>
                  <div className="mt-4 flex gap-2">
                    <button
                      onClick={() => handleDelete(provider.id)}
                      className="text-red-600 hover:text-red-700 px-3 py-1 text-sm"
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

import Link from 'next/link'
