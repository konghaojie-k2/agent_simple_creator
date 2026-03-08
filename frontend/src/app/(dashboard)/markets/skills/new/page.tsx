'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { skillsApi } from '@/lib/api'

const categories = [
  { value: 'tool', label: 'Tool', description: 'Reusable tool with parameters' },
  { value: 'prompt', label: 'Prompt', description: 'Prompt template' },
  { value: 'template', label: 'Template', description: 'Code or text template' },
  { value: 'custom', label: 'Custom', description: 'Custom skill type' },
]

const contentTypes = [
  { value: 'text', label: 'Text' },
  { value: 'json', label: 'JSON' },
  { value: 'yaml', label: 'YAML' },
]

export default function NewSkillPage() {
  const router = useRouter()
  const [submitting, setSubmitting] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'custom',
    content: '',
    content_type: 'text',
    parameters_schema: '',
    tags: '',
    is_public: false,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      let parameters_schema = {}
      if (formData.parameters_schema) {
        try {
          parameters_schema = JSON.parse(formData.parameters_schema)
        } catch {
          alert('Invalid JSON schema')
          setSubmitting(false)
          return
        }
      }

      await skillsApi.create({
        name: formData.name,
        description: formData.description || undefined,
        category: formData.category,
        content: formData.content || undefined,
        content_type: formData.content_type,
        parameters_schema: Object.keys(parameters_schema).length > 0 ? parameters_schema : undefined,
        tags: formData.tags ? formData.tags.split(',').map(t => t.trim()) : undefined,
        is_public: formData.is_public,
      })
      router.push('/markets/skills')
    } catch (error) {
      console.error('Failed to create skill:', error)
      alert('Failed to create skill')
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
              href="/markets/skills"
              className="p-2 hover:bg-purple-50 rounded-lg transition-colors cursor-pointer"
            >
              <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Link>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
                Create Skill
              </h1>
              <p className="text-sm text-gray-500">Add a new reusable skill</p>
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
                    placeholder="My Skill"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={e => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    rows={3}
                    placeholder="What does this skill do?"
                  />
                </div>
              </div>
            </div>

            {/* Category */}
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Category</h2>
              <div className="grid grid-cols-2 gap-3">
                {categories.map(cat => (
                  <button
                    key={cat.value}
                    type="button"
                    onClick={() => setFormData({ ...formData, category: cat.value })}
                    className={`p-4 rounded-lg border-2 text-left transition-all ${
                      formData.category === cat.value
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-gray-200 hover:border-purple-200'
                    }`}
                  >
                    <div className="font-medium text-gray-900">{cat.label}</div>
                    <div className="text-xs text-gray-500">{cat.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Content */}
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Skill Content</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Content Type</label>
                  <select
                    value={formData.content_type}
                    onChange={e => setFormData({ ...formData, content_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 cursor-pointer"
                  >
                    {contentTypes.map(ct => (
                      <option key={ct.value} value={ct.value}>{ct.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Content</label>
                  <textarea
                    value={formData.content}
                    onChange={e => setFormData({ ...formData, content: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 font-mono text-sm"
                    rows={10}
                    placeholder={formData.content_type === 'json' ? '{"key": "value"}' : 'Your skill content here...'}
                  />
                </div>
              </div>
            </div>

            {/* Parameters Schema */}
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Parameters Schema (Optional)</h2>
              <p className="text-sm text-gray-500 mb-3">Define parameters in JSON Schema format</p>
              <textarea
                value={formData.parameters_schema}
                onChange={e => setFormData({ ...formData, parameters_schema: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 font-mono text-sm"
                rows={6}
                placeholder='{"type": "object", "properties": {"name": {"type": "string"}}}'
              />
              {formData.parameters_schema && (
                <div className="mt-2">
                  {(() => {
                    try {
                      JSON.parse(formData.parameters_schema)
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
                  <span className="text-sm text-gray-700">Make this skill public</span>
                </label>
              </div>
            </div>

            {/* Submit */}
            <div className="flex justify-end gap-3">
              <Link
                href="/markets/skills"
                className="px-4 py-2 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
              >
                Cancel
              </Link>
              <button
                type="submit"
                disabled={submitting}
                className="px-6 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-colors disabled:opacity-50 cursor-pointer"
              >
                {submitting ? 'Creating...' : 'Create Skill'}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  )
}
