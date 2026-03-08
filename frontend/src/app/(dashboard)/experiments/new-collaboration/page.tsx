"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/contexts/AuthContext"
import { ExperimentType, CollaborationType, type ExperimentParticipantCreate, type ParticipantRole } from "@/types"

// API client
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface Agent {
  id: string
  name: string
  description?: string
  model: string
}

export default function NewCollaborationExperimentPage() {
  const router = useRouter()
  const { user, isLoading: authLoading } = useAuth()

  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  const [experimentName, setExperimentName] = useState("")
  const [experimentDesc, setExperimentDesc] = useState("")
  const [experimentType, setExperimentType] = useState< ExperimentType>("collaboration")
  const [collaborationType, setCollaborationType] = useState< CollaborationType>("sequential")
  const [participants, setParticipants] = useState<ExperimentParticipantCreate[]>([
    { agent_id: "", role: "leader", join_order: 0 }
  ])
  const [maxRounds, setMaxRounds] = useState(3)
  const [inputData, setInputData] = useState("{}")

  useEffect(() => {
    if (user) {
      fetchAgents()
    }
  }, [user])

  const fetchAgents = async () => {
    try {
      const token = localStorage.getItem("token")
      const response = await fetch(`${API_URL}/api/agents`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setAgents(data)
      }
    } catch (error) {
      console.error("Failed to fetch agents:", error)
    } finally {
      setLoading(false)
    }
  }

  const addParticipant = () => {
    setParticipants([
      ...participants,
      { agent_id: "", role: "worker", join_order: participants.length }
    ])
  }

  const removeParticipant = (index: number) => {
    if (participants.length > 1) {
      const newParticipants = participants.filter((_, i) => i !== index)
      // Reorder join_order
      newParticipants.forEach((p, i) => p.join_order = i)
      setParticipants(newParticipants)
    }
  }

  const updateParticipant = (index: number, field: keyof ExperimentParticipantCreate, value: string | number) => {
    const newParticipants = [...participants]
    ;(newParticipants[index] as any)[field] = value
    setParticipants(newParticipants)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)

    try {
      const token = localStorage.getItem("token")

      // Validate participants
      const validParticipants = participants.filter(p => p.agent_id)
      if (validParticipants.length === 0) {
        alert("请至少选择一个 Agent")
        setSubmitting(false)
        return
      }

      const experimentData = {
        name: experimentName,
        description: experimentDesc,
        experiment_type: experimentType,
        collaboration_type: collaborationType,
        participants: validParticipants,
        workflow_config: collaborationType === "debate" ? { max_rounds: maxRounds } : {},
        input_data: inputData ? JSON.parse(inputData) : {}
      }

      const response = await fetch(`${API_URL}/api/collaboration/experiments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(experimentData)
      })

      if (response.ok) {
        const experiment = await response.json()
        router.push(`/experiments/${experiment.id}`)
      } else {
        const error = await response.json()
        alert(`创建失败: ${error.detail || "未知错误"}`)
      }
    } catch (error) {
      console.error("Failed to create experiment:", error)
      alert("创建失败，请检查网络连接")
    } finally {
      setSubmitting(false)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">加载中...</div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">创建多Agent协作实验</h1>
        <p className="text-gray-600 mt-1">配置多个Agent协作完成复杂任务</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 基本信息 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">基本信息</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                实验名称 *
              </label>
              <input
                type="text"
                required
                value={experimentName}
                onChange={(e) => setExperimentName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="例如：多Agent文档协作生成"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                实验描述
              </label>
              <textarea
                value={experimentDesc}
                onChange={(e) => setExperimentDesc(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="描述实验的目标和预期结果..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                协作模式 *
              </label>
              <select
                value={collaborationType}
                onChange={(e) => setCollaborationType(e.target.value as CollaborationType)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="sequential">顺序执行 (Sequential)</option>
                <option value="parallel">并行执行 (Parallel)</option>
                <option value="debate">辩论模式 (Debate)</option>
              </select>
              <p className="text-sm text-gray-500 mt-1">
                {collaborationType === "sequential" && "Agent 按顺序依次执行，每个Agent的输出传递给下一个"}
                {collaborationType === "parallel" && "所有Agent同时执行，最后汇总结果"}
                {collaborationType === "debate" && "Agent轮流发表观点，进行多轮讨论后达成共识"}
              </p>
            </div>
          </div>
        </div>

        {/* 参与者配置 */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">参与者配置</h2>
            <button
              type="button"
              onClick={addParticipant}
              className="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 text-sm"
            >
              + 添加参与者
            </button>
          </div>

          <div className="space-y-4">
            {participants.map((participant, index) => (
              <div key={index} className="border border-gray-200 rounded-md p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium">参与者 #{index + 1}</span>
                  {participants.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeParticipant(index)}
                      className="text-red-500 hover:text-red-600 text-sm"
                    >
                      移除
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Agent *
                    </label>
                    <select
                      required
                      value={participant.agent_id}
                      onChange={(e) => updateParticipant(index, "agent_id", e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">选择 Agent</option>
                      {agents.map((agent) => (
                        <option key={agent.id} value={agent.id}>
                          {agent.name} ({agent.model})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      角色
                    </label>
                    <select
                      value={participant.role}
                      onChange={(e) => updateParticipant(index, "role", e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="leader">领导者 (Leader)</option>
                      <option value="worker">工作者 (Worker)</option>
                      <option value="reviewer">审核者 (Reviewer)</option>
                      <option value="observer">观察者 (Observer)</option>
                    </select>
                  </div>

                  {collaborationType === "sequential" && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        执行顺序
                      </label>
                      <input
                        type="number"
                        min="0"
                        value={participant.join_order}
                        onChange={(e) => updateParticipant(index, "join_order", parseInt(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 工作流配置 */}
        {collaborationType === "debate" && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">辩论配置</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                最大讨论轮数
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={maxRounds}
                onChange={(e) => setMaxRounds(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-sm text-gray-500 mt-1">
                Agent 将进行多轮讨论，然后由领导者总结
              </p>
            </div>
          </div>
        )}

        {/* 输入数据 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">输入数据 (JSON)</h2>

          <textarea
            value={inputData}
            onChange={(e) => setInputData(e.target.value)}
            rows={6}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
            placeholder='{"task": "分析以下数据并生成报告", "data": "..."}'
          />
          <p className="text-sm text-gray-500 mt-1">
            提供给实验的输入数据，将作为每个Agent的上下文
          </p>
        </div>

        {/* 提交按钮 */}
        <div className="flex items-center justify-end space-x-4">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            取消
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
          >
            {submitting ? "创建中..." : "创建协作实验"}
          </button>
        </div>
      </form>
    </div>
  )
}
