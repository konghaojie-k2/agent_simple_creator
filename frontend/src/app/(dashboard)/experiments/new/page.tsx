'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { experimentsApi, agentsApi, templatesApi, documentsApi, datasetsApi, skillsApi } from '@/lib/api'
import { Agent, ExperimentTemplate, ExperimentType, Document, Dataset, Skill } from '@/types'

const experimentTypes = [
  { value: 'document', label: 'Document Generation', icon: '📄', description: 'Generate README, API docs, technical docs' },
  { value: 'skill_creation', label: 'Skill Creation', icon: '🛠️', description: 'Create CLI tools, API wrappers' },
  { value: 'problem_solving', label: 'Problem Solving', icon: '🧩', description: 'Solve complex problems with AI' },
  { value: 'data_analysis', label: 'Data Analysis', icon: '📊', description: 'Clean, visualize, analyze data' },
  { value: 'custom', label: 'Custom', icon: '⚡', description: 'Custom experiment type' },
]

export default function NewExperimentPage() {
  const router = useRouter()
  // const searchParams = useSearchParams() // TODO: re-enable for template functionality
  const [agents, setAgents] = useState<Agent[]>([])
  const [templates, setTemplates] = useState<ExperimentTemplate[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [skills, setSkills] = useState<Skill[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [formData, setFormData] = useState<{
    name: string;
    description: string;
    agent_id: string;
    experiment_type: string;
    template_id: string;
    // Background Info
    requirements: string;
    background: string;
    doc_ids: string[];
    data_ids: string[];
    skill_ids: string[];
    input_data: string;
  }>({
    name: '',
    description: '',
    agent_id: '',
    experiment_type: 'document',
    template_id: '',
    requirements: '',
    background: '',
    doc_ids: [],
    data_ids: [],
    skill_ids: [],
    input_data: '',
  })

  // 从 URL 读取 template 参数并应用模板配置
  /*
  useEffect(() => {
    const templateId = searchParams.get('template')
    if (templateId && templates.length > 0) {
      const template = templates.find(t => t.id === templateId)
      if (template && template.template_config) {
        const config = template.template_config as Record<string, any>
        setFormData(prev => ({
          ...prev,
          template_id: templateId,
          experiment_type: config.experiment_type || prev.experiment_type,
          requirements: config.requirements || prev.requirements,
          background: config.background || prev.background,
          input_data: config.input_data ? JSON.stringify(config.input_data, null, 2) : prev.input_data,
        }))
      } else {
        setFormData(prev => ({ ...prev, template_id: templateId }))
      }
    }
  }, [searchParams, templates])
  */

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [agentsData, templatesData, documentsData, datasetsData, skillsData] = await Promise.all([
        agentsApi.list(),
        templatesApi.list(),
        documentsApi.list(),
        datasetsApi.list(),
        skillsApi.list(),
      ])
      console.log('Loaded agents:', agentsData)
      setAgents(agentsData || [])
      setTemplates(templatesData || [])
      setDocuments(documentsData || [])
      setDatasets(datasetsData || [])
      setSkills(skillsData || [])
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const inputData = formData.input_data ? JSON.parse(formData.input_data) : {}
      await experimentsApi.create({
        name: formData.name,
        description: formData.description,
        agent_id: formData.agent_id,
        experiment_type: formData.experiment_type as ExperimentType,
        template_id: formData.template_id || undefined,
        requirements: formData.requirements || undefined,
        background: formData.background || undefined,
        doc_ids: formData.doc_ids.length > 0 ? formData.doc_ids : undefined,
        data_ids: formData.data_ids.length > 0 ? formData.data_ids : undefined,
        skill_ids: formData.skill_ids.length > 0 ? formData.skill_ids : undefined,
        input_data: inputData,
      })
      router.push('/experiments')
    } catch (error) {
      console.error('Failed to create experiment:', error)
      alert('Failed to create experiment. Please check your input.')
    } finally {
      setSubmitting(false)
    }
  }

  const filteredTemplates = templates.filter(t => t.experiment_type === formData.experiment_type)

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  if (agents.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-purple-50 flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-8 text-center max-w-md">
          <div className="text-6xl mb-4">🤖</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Agents Available</h2>
          <p className="text-gray-500 mb-6">You need to create an agent before running experiments</p>
          <Link
            href="/agents"
            className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-colors cursor-pointer"
          >
            Create Agent
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-purple-50">
      <header className="bg-white/80 backdrop-blur-sm shadow-sm border-b border-purple-100">
        <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
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
                Create New Experiment
              </h1>
              <p className="text-sm text-gray-500">Configure your experiment parameters</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 sm:px-0">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Info */}
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Experiment Name</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    placeholder="My Experiment"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={e => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    rows={2}
                    placeholder="What is this experiment about?"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Agent</label>
                  <select
                    required
                    value={formData.agent_id}
                    onChange={e => setFormData({ ...formData, agent_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 cursor-pointer"
                  >
                    <option value="">Select an agent</option>
                    {agents.map(agent => (
                      <option key={agent.id} value={agent.id}>
                        {agent.name} ({agent.model})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Experiment Type */}
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Experiment Type</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {experimentTypes.map(type => (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => setFormData({ ...formData, experiment_type: type.value as ExperimentType, template_id: '' })}
                    className={`p-4 rounded-lg border-2 text-left transition-all ${
                      formData.experiment_type === type.value
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-gray-200 hover:border-purple-200'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{type.icon}</span>
                      <div>
                        <div className="font-medium text-gray-900">{type.label}</div>
                        <div className="text-xs text-gray-500">{type.description}</div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Template Selection */}
            {filteredTemplates.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Template (Optional)</h2>
                <div className="space-y-2">
                  <label className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 cursor-pointer hover:bg-purple-50">
                    <input
                      type="radio"
                      name="template"
                      value=""
                      checked={!formData.template_id}
                      onChange={() => setFormData({ ...formData, template_id: '' })}
                      className="text-purple-600 focus:ring-purple-500"
                    />
                    <span className="text-gray-700">No template (custom input)</span>
                  </label>
                  {filteredTemplates.map(template => (
                    <label
                      key={template.id}
                      className={`flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-all ${
                        formData.template_id === template.id
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-purple-200'
                      }`}
                    >
                      <input
                        type="radio"
                        name="template"
                        value={template.id}
                        checked={formData.template_id === template.id}
                        onChange={() => setFormData({ ...formData, template_id: template.id })}
                        className="text-purple-600 focus:ring-purple-500"
                      />
                      <div>
                        <div className="font-medium text-gray-900">{template.name}</div>
                        <div className="text-xs text-gray-500">{template.description}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Background Info */}
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Background Information</h2>
              <p className="text-sm text-gray-500 mb-4">Provide context for your experiment (choose lightweight or reference mode)</p>

              {/* Mode 1: Lightweight - direct input */}
              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Requirements</label>
                  <textarea
                    value={formData.requirements}
                    onChange={e => setFormData({ ...formData, requirements: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    rows={3}
                    placeholder="What specific requirements should the experiment meet?"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Background</label>
                  <textarea
                    value={formData.background}
                    onChange={e => setFormData({ ...formData, background: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    rows={3}
                    placeholder="Additional background information..."
                  />
                </div>
              </div>

              {/* Mode 2: Reference documents */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Reference Documents</label>
                <p className="text-xs text-gray-500 mb-2">Select documents to reference in this experiment</p>
                {documents.length === 0 ? (
                  <p className="text-sm text-gray-400 py-2">No documents available. Create one in Doc Market first.</p>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {documents.map(doc => (
                      <label
                        key={doc.id}
                        className={`flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-all ${
                          formData.doc_ids.includes(doc.id)
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-200 hover:border-purple-200'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={formData.doc_ids.includes(doc.id)}
                          onChange={e => {
                            if (e.target.checked) {
                              setFormData({ ...formData, doc_ids: [...formData.doc_ids, doc.id] })
                            } else {
                              setFormData({ ...formData, doc_ids: formData.doc_ids.filter(id => id !== doc.id) })
                            }
                          }}
                          className="text-purple-600 focus:ring-purple-500"
                        />
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{doc.name}</div>
                          {doc.description && (
                            <div className="text-xs text-gray-500">{doc.description}</div>
                          )}
                        </div>
                        <span className="text-xs text-gray-400">{doc.doc_type}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Reference Datasets */}
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Reference Datasets</label>
              <p className="text-xs text-gray-500 mb-2">Select datasets to use in this experiment</p>
              {datasets.length === 0 ? (
                <p className="text-sm text-gray-400 py-2">No datasets available. Create one in Data Market first.</p>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {datasets.map(dataset => (
                    <label
                      key={dataset.id}
                      className={`flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-all ${
                        formData.data_ids.includes(dataset.id)
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-blue-200'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={formData.data_ids.includes(dataset.id)}
                        onChange={e => {
                          if (e.target.checked) {
                            setFormData({ ...formData, data_ids: [...formData.data_ids, dataset.id] })
                          } else {
                            setFormData({ ...formData, data_ids: formData.data_ids.filter(id => id !== dataset.id) })
                          }
                        }}
                        className="text-blue-600 focus:ring-blue-500"
                      />
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">{dataset.name}</div>
                        {dataset.description && (
                          <div className="text-xs text-gray-500">{dataset.description}</div>
                        )}
                      </div>
                      <span className="text-xs text-gray-400">{dataset.dataset_type}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Required Skills */}
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Required Skills</label>
              <p className="text-xs text-gray-500 mb-2">Select skills needed for this experiment</p>
              {skills.length === 0 ? (
                <p className="text-sm text-gray-400 py-2">No skills available. Create one in Skill Market first.</p>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {skills.map(skill => (
                    <label
                      key={skill.id}
                      className={`flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-all ${
                        formData.skill_ids.includes(skill.id)
                          ? 'border-green-500 bg-green-50'
                          : 'border-gray-200 hover:border-green-200'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={formData.skill_ids.includes(skill.id)}
                        onChange={e => {
                          if (e.target.checked) {
                            setFormData({ ...formData, skill_ids: [...formData.skill_ids, skill.id] })
                          } else {
                            setFormData({ ...formData, skill_ids: formData.skill_ids.filter(id => id !== skill.id) })
                          }
                        }}
                        className="text-green-600 focus:ring-green-500"
                      />
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">{skill.name}</div>
                        {skill.description && (
                          <div className="text-xs text-gray-500">{skill.description}</div>
                        )}
                      </div>
                      <span className="text-xs text-gray-400">{skill.category}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Input Data */}
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Input Data (Optional)</h2>
              <p className="text-sm text-gray-500 mb-3">Enter JSON data that will be passed to the experiment</p>
              <textarea
                value={formData.input_data}
                onChange={e => setFormData({ ...formData, input_data: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 font-mono text-sm"
                rows={6}
                placeholder='{"description": "My awesome project"}'
              />
              {formData.input_data && (
                <div className="mt-2">
                  {(() => {
                    try {
                      JSON.parse(formData.input_data)
                      return <span className="text-sm text-green-600">✓ Valid JSON</span>
                    } catch {
                      return <span className="text-sm text-red-600">✗ Invalid JSON</span>
                    }
                  })()}
                </div>
              )}
            </div>

            {/* Submit */}
            <div className="flex justify-end gap-3">
              <Link
                href="/experiments"
                className="px-4 py-2 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
              >
                Cancel
              </Link>
              <button
                type="submit"
                disabled={submitting}
                className="px-6 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-colors disabled:opacity-50 cursor-pointer"
              >
                {submitting ? 'Creating...' : 'Create Experiment'}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  )
}
