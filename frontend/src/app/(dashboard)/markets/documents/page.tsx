'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { documentsApi } from '@/lib/api'
import { Document } from '@/types'

const docTypeLabels: Record<string, string> = {
  markdown: 'Markdown',
  text: 'Text',
  html: 'HTML',
  pdf: 'PDF',
  docx: 'Word',
}

type TabType = 'all' | 'public' | 'private'

export default function DocMarketPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [activeTab, setActiveTab] = useState<TabType>('all')

  useEffect(() => {
    loadDocuments()
  }, [activeTab])

  const loadDocuments = async () => {
    setLoading(true)
    try {
      let params: Record<string, string | boolean> = {}
      if (activeTab === 'public') {
        params.is_public = true
      } else if (activeTab === 'private') {
        params.is_public = false
      }
      const data = await documentsApi.list(params)
      setDocuments(data)
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return
    try {
      await documentsApi.delete(id)
      loadDocuments()
    } catch (error) {
      console.error('Failed to delete document:', error)
    }
  }

  const handleToggleVisibility = async (doc: Document) => {
    try {
      await documentsApi.updateVisibility(doc.id, !doc.is_public)
      loadDocuments()
    } catch (error) {
      console.error('Failed to update visibility:', error)
    }
  }

  const filteredDocs = documents.filter(d =>
    d.name.toLowerCase().includes(filter.toLowerCase()) ||
    d.description?.toLowerCase().includes(filter.toLowerCase())
  )

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
                Document Market
              </h1>
              <p className="text-sm text-gray-500">Manage your reference documents</p>
            </div>
            <Link
              href="/markets/documents/new"
              className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-colors cursor-pointer"
            >
              Create Document
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
              placeholder="Search documents..."
              value={filter}
              onChange={e => setFilter(e.target.value)}
              className="w-full max-w-md px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
            />
          </div>

          {/* Document Grid */}
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
            </div>
          ) : filteredDocs.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-12 text-center">
              <div className="text-6xl mb-4">📄</div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">No Documents Found</h2>
              <p className="text-gray-500 mb-6">
                {activeTab === 'all'
                  ? 'Create your first document to get started'
                  : activeTab === 'public'
                  ? 'No public documents available'
                  : 'You have no private documents yet'}
              </p>
              <Link
                href="/markets/documents/new"
                className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-colors cursor-pointer"
              >
                Create Document
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredDocs.map(doc => (
                <div
                  key={doc.id}
                  className="bg-white rounded-xl shadow-sm border border-purple-100 p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900">{doc.name}</h3>
                      <div className="flex gap-2 mt-1">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                          {docTypeLabels[doc.doc_type] || doc.doc_type}
                        </span>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          doc.is_public
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {doc.is_public ? 'Public' : 'Private'}
                        </span>
                        {doc.source === 'filesystem' && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                            System
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  {doc.description && (
                    <p className="text-sm text-gray-500 mb-3 line-clamp-2">{doc.description}</p>
                  )}
                  {doc.tags && doc.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {doc.tags.slice(0, 3).map(tag => (
                        <span key={tag} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="flex items-center justify-between text-xs text-gray-400 mb-4">
                    <span>{doc.category || 'Uncategorized'}</span>
                    <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex gap-2">
                    {doc.source === 'database' && (
                      <>
                        <button
                          onClick={() => handleToggleVisibility(doc)}
                          className="flex-1 px-3 py-1.5 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                          {doc.is_public ? 'Make Private' : 'Make Public'}
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id)}
                          className="px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          Delete
                        </button>
                      </>
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
