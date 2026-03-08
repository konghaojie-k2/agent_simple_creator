'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { experimentsApi, agentsApi, experiencesApi } from '@/lib/api'
import { Experiment, Agent, ExperimentExperience } from '@/types'

const statusColors = {
  pending: 'bg-gray-100 text-gray-800',
  running: 'bg-blue-100 text-blue-800',
  success: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
}

const typeLabels = {
  skill_creation: 'Skill Creation',
  document: 'Document',
  problem_solving: 'Problem Solving',
  data_analysis: 'Data Analysis',
  custom: 'Custom',
}

export default function ExperimentDetailPage() {
  const params = useParams()
  const router = useRouter()
  const experimentId = params.id as string

  const [experiment, setExperiment] = useState<Experiment | null>(null)
  const [agent, setAgent] = useState<Agent | null>(null)
  const [experiences, setExperiences] = useState<ExperimentExperience[]>([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [showExperienceForm, setShowExperienceForm] = useState(false)
  const [experienceForm, setExperienceForm] = useState({
    summary: '',
    lessons_learned: '',
    improvements: '',
  })

  useEffect(() => {
    loadData()
  }, [experimentId])

  const loadData = async () => {
    try {
      const [expData, expList] = await Promise.all([
        experimentsApi.get(experimentId),
        experiencesApi.list({ experiment_id: experimentId }),
      ])
      setExperiment(expData)
      setExperiences(expList)

      if (expData?.agent_id) {
        const agentData = await agentsApi.get(expData.agent_id)
        setAgent(agentData)
      }
    } catch (error) {
      console.error('Failed to load experiment:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRun = async () => {
    setRunning(true)
    try {
      await experimentsApi.run(experimentId)
      await loadData()
    } catch (error) {
      console.error('Failed to run experiment:', error)
    } finally {
      setRunning(false)
    }
  }

  const handleCreateExperience = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await experiencesApi.create({
        experiment_id: experimentId,
        summary: experienceForm.summary,
        lessons_learned: experienceForm.lessons_learned || undefined,
        improvements: experienceForm.improvements || undefined,
      })
      setShowExperienceForm(false)
      setExperienceForm({ summary: '', lessons_learned: '', improvements: '' })
      loadData()
    } catch (error) {
      console.error('Failed to create experience:', error)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this experiment?')) return
    try {
      await experimentsApi.delete(experimentId)
      router.push('/experiments')
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

  if (!experiment) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Experiment not found</h2>
          <Link href="/experiments" className="text-purple-600 hover:text-purple-700">
            Back to experiments
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-purple-50">
      <header className="bg-white/80 backdrop-blur-sm shadow-sm border-b border-purple-100">
        <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
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
                <h1 className="text-2xl font-bold text-gray-900">{experiment.name}</h1>
                <p className="text-sm text-gray-500">
                  {typeLabels[experiment.experiment_type as keyof typeof typeLabels] || experiment.experiment_type}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[experiment.status as keyof typeof statusColors]}`}>
                {experiment.status}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 sm:px-0 space-y-6">
          {/* Actions */}
          <div className="flex justify-between items-center">
            <div className="flex gap-2">
              {experiment.status === 'pending' && (
                <button
                  onClick={handleRun}
                  disabled={running}
                  className="px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 transition-colors disabled:opacity-50 flex items-center gap-2 cursor-pointer"
                >
                  {running ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Running...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      </svg>
                      Run Experiment
                    </>
                  )}
                </button>
              )}
            </div>
            <button
              onClick={handleDelete}
              className="px-3 py-2 text-red-500 hover:text-red-700 transition-colors cursor-pointer"
            >
              Delete
            </button>
          </div>

          {/* Details */}
          <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Details</h2>
            <dl className="grid grid-cols-1 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Description</dt>
                <dd className="text-gray-900 mt-1">{experiment.description || 'No description'}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Agent</dt>
                <dd className="text-gray-900 mt-1">
                  {agent ? (
                    <Link href={`/agents/${agent.id}`} className="text-purple-600 hover:text-purple-700">
                      {agent.name}
                    </Link>
                  ) : (
                    'Unknown'
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Created</dt>
                <dd className="text-gray-900 mt-1">{new Date(experiment.created_at).toLocaleString()}</dd>
              </div>
            </dl>
          </div>

          {/* Background Information */}
          {(experiment.requirements || experiment.background || (experiment.doc_ids && experiment.doc_ids.length > 0)) && (
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Background Information</h2>
              <dl className="space-y-4">
                {experiment.requirements && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Requirements</dt>
                    <dd className="text-gray-900 mt-1 whitespace-pre-wrap">{experiment.requirements}</dd>
                  </div>
                )}
                {experiment.background && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Background</dt>
                    <dd className="text-gray-900 mt-1 whitespace-pre-wrap">{experiment.background}</dd>
                  </div>
                )}
                {experiment.doc_ids && experiment.doc_ids.length > 0 && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Referenced Documents</dt>
                    <dd className="text-gray-900 mt-1">
                      <div className="flex flex-wrap gap-2">
                        {experiment.doc_ids.map(docId => (
                          <span key={docId} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                            {docId}
                          </span>
                        ))}
                      </div>
                    </dd>
                  </div>
                )}
                {experiment.data_ids && experiment.data_ids.length > 0 && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Referenced Datasets</dt>
                    <dd className="text-gray-900 mt-1">
                      <div className="flex flex-wrap gap-2">
                        {experiment.data_ids.map(dataId => (
                          <span key={dataId} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {dataId}
                          </span>
                        ))}
                      </div>
                    </dd>
                  </div>
                )}
                {experiment.skill_ids && experiment.skill_ids.length > 0 && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Required Skills</dt>
                    <dd className="text-gray-900 mt-1">
                      <div className="flex flex-wrap gap-2">
                        {experiment.skill_ids.map(skillId => (
                          <span key={skillId} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            {skillId}
                          </span>
                        ))}
                      </div>
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* Input Data */}
          {experiment.input_data && Object.keys(experiment.input_data).length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Input Data</h2>
              <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm font-mono">
                {JSON.stringify(experiment.input_data, null, 2)}
              </pre>
            </div>
          )}

          {/* Output Data */}
          {experiment.output_data && Object.keys(experiment.output_data).length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Output</h2>
              <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm font-mono">
                {JSON.stringify(experiment.output_data, null, 2)}
              </pre>
            </div>
          )}

          {/* Error Message */}
          {experiment.error_message && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6">
              <h2 className="text-lg font-semibold text-red-900 mb-2">Error</h2>
              <p className="text-red-700">{experiment.error_message}</p>
            </div>
          )}

          {/* Metrics */}
          {experiment.metrics && Object.keys(experiment.metrics).length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Metrics</h2>
              <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm font-mono">
                {JSON.stringify(experiment.metrics, null, 2)}
              </pre>
            </div>
          )}

          {/* Experiences */}
          <div className="bg-white rounded-xl shadow-sm border border-purple-100 p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Experiences</h2>
              <button
                onClick={() => setShowExperienceForm(!showExperienceForm)}
                className="px-3 py-1.5 bg-purple-100 text-purple-600 rounded-lg hover:bg-purple-200 transition-colors text-sm cursor-pointer"
              >
                {showExperienceForm ? 'Cancel' : 'Add Experience'}
              </button>
            </div>

            {showExperienceForm && (
              <form onSubmit={handleCreateExperience} className="mb-6 p-4 bg-purple-50 rounded-lg space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Summary</label>
                  <input
                    type="text"
                    required
                    value={experienceForm.summary}
                    onChange={e => setExperienceForm({ ...experienceForm, summary: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500"
                    placeholder="What did you learn?"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Lessons Learned</label>
                  <textarea
                    value={experienceForm.lessons_learned}
                    onChange={e => setExperienceForm({ ...experienceForm, lessons_learned: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500"
                    rows={3}
                    placeholder="What worked well? What didn't?"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Improvements</label>
                  <textarea
                    value={experienceForm.improvements}
                    onChange={e => setExperienceForm({ ...experienceForm, improvements: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500"
                    rows={2}
                    placeholder="How can this be improved?"
                  />
                </div>
                <button
                  type="submit"
                  className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-colors cursor-pointer"
                >
                  Save Experience
                </button>
              </form>
            )}

            {experiences.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No experiences recorded yet</p>
            ) : (
              <div className="space-y-4">
                {experiences.map(exp => (
                  <div key={exp.id} className="border-l-4 border-purple-300 pl-4 py-2">
                    <p className="font-medium text-gray-900">{exp.summary}</p>
                    {exp.lessons_learned && (
                      <p className="text-sm text-gray-600 mt-1">📚 {exp.lessons_learned}</p>
                    )}
                    {exp.improvements && (
                      <p className="text-sm text-gray-600 mt-1">💡 {exp.improvements}</p>
                    )}
                    <p className="text-xs text-gray-400 mt-2">
                      {new Date(exp.created_at).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
