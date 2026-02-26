'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { agentsApi } from '@/lib/api'
import { AgentDetail as AgentDetailType, ToolInfo, SkillInfo } from '@/types'

export default function AgentDetailPage() {
  const params = useParams()
  const agentId = params.id as string
  const [agent, setAgent] = useState<AgentDetailType | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAgentDetail()
  }, [agentId])

  const loadAgentDetail = async () => {
    try {
      const detail = await agentsApi.getDetail(agentId)
      setAgent(detail)
    } catch (error) {
      console.error('Failed to load agent detail:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  if (!agent) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Agent not found</p>
      </div>
    )
  }

  const sourceColors = {
    shared: 'bg-blue-100 text-blue-800',
    agent: 'bg-green-100 text-green-800',
    experience: 'bg-purple-100 text-purple-800',
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4">
            <Link
              href="/agents"
              className="text-gray-600 hover:text-gray-900"
            >
              ← Back
            </Link>
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900">{agent.name}</h1>
              <p className="text-gray-500 mt-1">{agent.description || 'No description'}</p>
            </div>
            <Link
              href={`/chat/${agent.id}`}
              className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors"
            >
              Chat with Agent
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Agent Info */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Agent Information</h2>
            <dl className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Model</dt>
                <dd className="mt-1 text-sm text-gray-900">{agent.model}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Max Steps</dt>
                <dd className="mt-1 text-sm text-gray-900">{agent.max_steps}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Created</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {new Date(agent.created_at).toLocaleDateString()}
                </dd>
              </div>
            </dl>
            {agent.system_prompt && (
              <div className="mt-4">
                <dt className="text-sm font-medium text-gray-500">System Prompt</dt>
                <dd className="mt-1 text-sm text-gray-900 bg-gray-50 p-3 rounded font-mono text-xs">
                  {agent.system_prompt}
                </dd>
              </div>
            )}
          </div>

          {/* Tools */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">
              Available Tools ({agent.tools.length})
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {agent.tools.map((tool: ToolInfo) => (
                <div
                  key={tool.name}
                  className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50"
                >
                  <div className="font-medium text-sm text-gray-900 font-mono">
                    {tool.name}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">{tool.description}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Skills */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">
              Skills ({agent.skills.length})
            </h2>
            {agent.skills.length === 0 ? (
              <p className="text-gray-500">No skills loaded</p>
            ) : (
              <div className="space-y-3">
                {agent.skills.map((skill: SkillInfo) => (
                  <div
                    key={skill.name}
                    className="border border-gray-200 rounded-lg p-4 flex items-start justify-between"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-gray-900">{skill.name}</h3>
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            sourceColors[skill.source]
                          }`}
                        >
                          {skill.source}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 mt-1">{skill.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Directories */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Agent Storage</h2>
            <div className="mb-4 p-3 bg-blue-50 rounded-md text-sm text-blue-800">
              <p className="font-medium">无独立工作空间</p>
              <p className="mt-1">Agent通过实验执行任务，工作空间位于实验目录中。</p>
            </div>
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Skills Directory</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono text-xs bg-gray-50 p-2 rounded">
                  {agent.directories.skills_dir}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Experiences Directory</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono text-xs bg-gray-50 p-2 rounded">
                  {agent.directories.experiences_dir}
                </dd>
              </div>
            </dl>
          </div>

          {/* Agent Note */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">About Agent Architecture</h2>
            <div className="text-sm text-gray-600 space-y-2">
              <p>Agent是<span className="font-medium text-gray-900">无状态工作者</span>，只存储：</p>
              <ul className="list-disc list-inside ml-4 space-y-1">
                <li><span className="font-medium">能力</span> - 技能集合（Skills）</li>
                <li><span className="font-medium">经验</span> - 沉淀的知识（Experiences）</li>
                <li><span className="font-medium">配置</span> - Agent参数（Profile）</li>
              </ul>
              <p className="mt-2">所有任务执行都在<span className="font-medium text-primary-600">实验工作空间</span>中完成。</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
