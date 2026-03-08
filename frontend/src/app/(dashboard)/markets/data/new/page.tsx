'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { datasetsApi } from '@/lib/api'

const datasetTypes = [
  { value: 'json', label: 'JSON', description: 'JSON array of objects' },
  { value: 'csv', label: 'CSV', description: 'Comma-separated values' },
  { value: 'text', label: 'Text', description: 'Plain text data' },
  { value: 'parquet', label: 'Parquet', description: 'Apache Parquet format' },
]

export default function NewDatasetPage() {
  const router = useRouter()
  const [submitting, setSubmitting] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    dataset_type: 'json',
    schema: '',
    row_count: 0,
    category: '',
    tags: '',
    is_public: false,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      let schema = {}
      if (formData.schema) {
        try {
          schema = JSON.parse(formData.schema)
        } catch {
          alert('Invalid JSON schema')
          setSubmitting(false)
          return
        }
      }

      await datasetsApi.create({
        name: formData.name,
        description: formData.description || undefined,
        dataset_type: formData.dataset_type,
        schema: Object.keys(schema).length > 0 ? schema : undefined,
        row_count: formData.row_count,
        category: formData.category || undefined,
        tags: formData.tags ? formData.tags.split(',').map(t => t.trim()) : undefined,
        is_public: formData.is_public,
      })
      router.push('/markets/data')
    } catch (error) {
      console.error('Failed to create dataset:', error)
      alert('Failed to create dataset')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-purple-50">
      <header className="bg-white/80 backdrop-blur-sm shadow-sm border-b border-purple-100">
        <div className="max-w-2xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4">
            <Link
              href="/markets/data"
              className="p-2 hover:bg-purple-50 rounded-lg transition-colors cursor-pointer"
            >
              <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Link>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
                Create Dataset
              </h1>
              <p className="text-sm text-gray-500">Add a new dataset to your library</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-2xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 sm:px-0">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Info */}
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    placeholder="My Dataset"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={e => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    rows={3}
                    placeholder="What is this dataset about?"
                  />
                </div>
              </div>
            </div>

            {/* Dataset Type */}
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Dataset Type</h2>
              <div className="grid grid-cols-2 gap-3">
                {datasetTypes.map(type => (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => setFormData({ ...formData, dataset_type: type.value })}
                    className={`p-4 rounded-lg border-2 text-left transition-all ${
                      formData.dataset_type === type.value
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-gray-200 hover:border-purple-200'
                    }`}
                  >
                    <div className="font-medium text-gray-900">{type.label}</div>
                    <div className="text-xs text-gray-500">{type.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Schema */}
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Schema (Optional)</h2>
              <p className="text-sm text-gray-500 mb-3">Define the data schema in JSON Schema format</p>
              <textarea
                value={formData.schema}
                onChange={e => setFormData({ ...formData, schema: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 font-mono text-sm"
                rows={6}
                placeholder='{"type": "object", "properties": {"name": {"type": "string"}}}'
              />
              {formData.schema && (
                <div className="mt-2">
                  {(() => {
                    try {
                      JSON.parse(formData.schema)
                      return <span className="text-sm text-green-600">✓ Valid JSON</span>
                    } catch {
                      return <span className="text-sm text-red-600">✗ Invalid JSON</span>
                    }
                  })()}
                </div>
              )}
            </div>

            {/* Additional Info */}
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Additional Info</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Row Count</label>
                  <input
                    type="number"
                    min="0"
                    value={formData.row_count}
                    onChange={e => setFormData({ ...formData, row_count: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <input
                    type="text"
                    value={formData.category}
                    onChange={e => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    placeholder="e.g., ml, analytics, reference"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tags (comma-separated)</label>
                  <input
                    type="text"
                    value={formData.tags}
                    onChange={e => setFormData({ ...formData, tags: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    placeholder="tag1, tag2, tag3"
                  />
                </div>
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={formData.is_public}
                    onChange={e => setFormData({ ...formData, is_public: e.target.checked })}
                    className="text-purple-600 focus:ring-purple-500 rounded"
                  />
                  <span className="text-sm text-gray-700">Make this dataset public</span>
                </label>
              </div>
            </div>

            {/* Submit */}
            <div className="flex justify-end gap-3">
              <Link
                href="/markets/data"
                className="px-4 py-2 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
              >
                Cancel
              </Link>
              <button
                type="submit"
                disabled={submitting}
                className="px-6 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-colors disabled:opacity-50 cursor-pointer"
              >
                {submitting ? 'Creating...' : 'Create Dataset'}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  )
}
