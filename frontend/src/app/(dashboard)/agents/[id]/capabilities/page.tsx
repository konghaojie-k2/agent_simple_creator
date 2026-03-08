'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { Agent, AgentCapabilities } from '@/types'

export default function AgentCapabilitiesPage() {
  const router = useRouter()
  const params = useParams()
  const agentId = params.id as string

  const [agent, setAgent] = useState<Agent | null>(null)
  const [capabilities, setCapabilities] = useState<AgentCapabilities | null>(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)

  // 提示词预览
  const [taskDescription, setTaskDescription] = useState('')
  const [previewing, setPreviewing] = useState(false)
  const [promptPreview, setPromptPreview] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [agentId])

  const loadData = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')

      // 并行获取 Agent 信息和能力
      const [agentRes, capRes] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/agents/${agentId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/agents/${agentId}/capabilities`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ])

      if (agentRes.ok) {
        const agentData = await agentRes.json()
        setAgent(agentData)
      }

      if (capRes.ok) {
        const capData = await capRes.json()
        setCapabilities(capData)
      }
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateCapabilities = async () => {
    setUpdating(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/agents/${agentId}/capabilities/update`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        const data = await response.json()
        setCapabilities(data)
        // 刷新 Agent 信息
        const agentRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/agents/${agentId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (agentRes.ok) {
          setAgent(await agentRes.json())
        }
      }
    } catch (error) {
      console.error('Failed to update capabilities:', error)
    } finally {
      setUpdating(false)
    }
  }

  const handlePreviewPrompt = async () => {
    if (!taskDescription.trim()) {
      alert('请输入任务描述')
      return
    }

    setPreviewing(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/agents/${agentId}/prompt/preview`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ task_description: taskDescription })
      })

      if (response.ok) {
        const data = await response.json()
        setPromptPreview(data.dynamic_prompt)
      }
    } catch (error) {
      console.error('Failed to preview prompt:', error)
    } finally {
      setPreviewing(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">加载中...</div>
      </div>
    )
  }

  if (!agent) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">Agent 不存在</div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => router.back()}
          className="text-blue-500 hover:text-blue-600 mb-2"
        >
          ← 返回
        </button>
        <h1 className="text-2xl font-bold text-gray-900">{agent.name} - 能力分析</h1>
        <p className="text-gray-600 mt-1">{agent.description || '暂无描述'}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左侧：能力概览 */}
        <div className="space-y-6">
          {/* 统计卡片 */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">能力统计</h2>
              <button
                onClick={handleUpdateCapabilities}
                disabled={updating}
                className="bg-blue-500 text-white px-3 py-1 rounded-md hover:bg-blue-600 disabled:opacity-50 text-sm"
              >
                {updating ? '更新中...' : '从经验重新聚合'}
              </button>
            </div>

            {capabilities?.statistics ? (
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {capabilities.statistics.total_experiences}
                  </div>
                  <div className="text-sm text-gray-500">经验总数</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-600">
                    {capabilities.statistics.success_count}
                  </div>
                  <div className="text-sm text-gray-500">成功</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-red-600">
                    {capabilities.statistics.failure_count}
                  </div>
                  <div className="text-sm text-gray-500">失败</div>
                </div>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">暂无统计数据</p>
            )}
          </div>

          {/* 核心能力 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">核心能力</h2>
            {capabilities?.core_capabilities && capabilities.core_capabilities.length > 0 ? (
              <ul className="space-y-2">
                {capabilities.core_capabilities.map((cap, idx) => (
                  <li key={idx} className="flex items-center">
                    <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                    {cap}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">暂无核心能力记录</p>
            )}
          </div>

          {/* 已掌握技能 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">已掌握技能 ({capabilities?.learned_skills?.length || 0})</h2>
            {capabilities?.learned_skills && capabilities.learned_skills.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {capabilities.learned_skills.map((skill, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">暂无技能记录</p>
            )}
          </div>

          {/* 成功模式 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">成功经验模式</h2>
            {capabilities?.successful_patterns && capabilities.successful_patterns.length > 0 ? (
              <ul className="space-y-3">
                {capabilities.successful_patterns.map((pattern, idx) => (
                  <li key={idx} className="text-sm text-gray-700 bg-green-50 p-3 rounded-md">
                    ✓ {pattern}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">暂无成功模式记录</p>
            )}
          </div>
        </div>

        {/* 右侧：提示词预览 */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">动态提示词预览</h2>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                任务描述（用于检索相关经验）
              </label>
              <textarea
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
                rows={3}
                placeholder="例如：生成一份关于 AI Agent 的技术报告..."
              />
            </div>

            <button
              onClick={handlePreviewPrompt}
              disabled={previewing}
              className="w-full bg-green-500 text-white py-2 px-4 rounded-md hover:bg-green-600 disabled:opacity-50"
            >
              {previewing ? '生成中...' : '生成动态提示词'}
            </button>

            {promptPreview && (
              <div className="mt-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">生成的提示词：</h3>
                <div className="bg-gray-50 rounded-md p-4 max-h-96 overflow-y-auto">
                  <pre className="text-sm text-gray-800 whitespace-pre-wrap font-sans">
                    {promptPreview}
                  </pre>
                </div>
              </div>
            )}
          </div>

          {/* 配置信息 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">提示词配置</h2>
            {agent.prompt_config ? (
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">注入经验：</span>
                  <span className={agent.prompt_config.inject_experiences ? 'text-green-600' : 'text-gray-400'}>
                    {agent.prompt_config.inject_experiences ? '启用' : '禁用'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">最大经验数：</span>
                  <span className="text-gray-900">{agent.prompt_config.max_experiences}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">注入模式：</span>
                  <span className="text-gray-900">{agent.prompt_config.injection_mode}</span>
                </div>
              </div>
            ) : (
              <p className="text-gray-500">使用默认配置</p>
            )}
          </div>

          {/* 基础提示词 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">基础系统提示词</h2>
            <div className="bg-gray-50 rounded-md p-4 max-h-48 overflow-y-auto">
              <pre className="text-sm text-gray-800 whitespace-pre-wrap font-sans">
                {agent.system_prompt || '（未设置基础提示词）'}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
