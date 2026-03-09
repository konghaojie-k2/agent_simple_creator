"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter, useParams } from "next/navigation"
import { useAuth } from "@/contexts/AuthContext"
import { type Experiment, type ExperimentParticipant, type AgentMessage, type CollaborationType } from "@/types"

// API client
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function CollaborationExperimentDetailsPage() {
  const router = useRouter()
  const params = useParams()
  const experimentId = params.id as string
  const { user, isLoading: authLoading } = useAuth()

  const [experiment, setExperiment] = useState<Experiment | null>(null)
  const [participants, setParticipants] = useState<ExperimentParticipant[]>([])
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)

  const pollingRef = useRef<NodeJS.Timeout | null>(null)

  // 轮询获取实验状态
  const startPolling = () => {
    if (pollingRef.current) return

    pollingRef.current = setInterval(async () => {
      try {
        await fetchExperiment()
        await fetchMessages()

        // 如果实验完成，停止轮询
        if (experiment?.status === 'success' || experiment?.status === 'failed') {
          stopPolling()
          setRunning(false)
        }
      } catch (error) {
        console.error('Polling error:', error)
      }
    }, 2000)
  }

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }

  // 组件卸载时停止轮询
  useEffect(() => {
    return () => {
      stopPolling()
    }
  }, [])

  // 监听实验状态，自动开始/停止轮询
  useEffect(() => {
    if (experiment?.status === 'running') {
      startPolling()
    } else {
      stopPolling()
    }
  }, [experiment?.status])

  useEffect(() => {
    if (user && experimentId) {
      fetchExperiment()
      fetchParticipants()
      fetchMessages()
    }
  }, [user, experimentId])

  const fetchExperiment = async () => {
    try {
      const token = localStorage.getItem("token")
      const response = await fetch(`${API_URL}/api/experiments/${experimentId}`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setExperiment(data)
      }
    } catch (error) {
      console.error("Failed to fetch experiment:", error)
    } finally {
      setLoading(false)
    }
  }

  const fetchParticipants = async () => {
    try {
      const token = localStorage.getItem("token")
      const response = await fetch(`${API_URL}/api/collaboration/experiments/${experimentId}/participants`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setParticipants(data)
      }
    } catch (error) {
      console.error("Failed to fetch participants:", error)
    }
  }

  const fetchMessages = async () => {
    try {
      const token = localStorage.getItem("token")
      const response = await fetch(`${API_URL}/api/collaboration/experiments/${experimentId}/messages`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setMessages(data)
      }
    } catch (error) {
      console.error("Failed to fetch messages:", error)
    }
  }

  const handleRun = async () => {
    setRunning(true)
    try {
      const token = localStorage.getItem("token")
      const response = await fetch(`${API_URL}/api/collaboration/experiments/${experimentId}/run`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      })

      if (response.ok) {
        // 立即开始轮询
        startPolling()
        // 立即刷新一次数据
        await fetchExperiment()
        await fetchParticipants()
        await fetchMessages()
      } else {
        const error = await response.json()
        alert(`运行失败: ${error.detail || "未知错误"}`)
        setRunning(false)
        stopPolling()
      }
    } catch (error) {
      console.error("Failed to run experiment:", error)
      alert("运行失败，请检查网络连接")
      setRunning(false)
      stopPolling()
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "success": return "bg-green-100 text-green-800"
      case "failed": return "bg-red-100 text-red-800"
      case "running": return "bg-blue-100 text-blue-800"
      case "active": return "bg-blue-100 text-blue-800"
      case "completed": return "bg-green-100 text-green-800"
      default: return "bg-gray-100 text-gray-800"
    }
  }

  const getRoleBadge = (role: string) => {
    switch (role) {
      case "leader": return "bg-purple-100 text-purple-800"
      case "worker": return "bg-blue-100 text-blue-800"
      case "reviewer": return "bg-yellow-100 text-yellow-800"
      case "observer": return "bg-gray-100 text-gray-800"
      default: return "bg-gray-100 text-gray-800"
    }
  }

  const getCollaborationTypeLabel = (type?: string) => {
    switch (type) {
      case "sequential": return "顺序执行"
      case "parallel": return "并行执行"
      case "debate": return "辩论模式"
      default: return "未知"
    }
  }

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">加载中...</div>
      </div>
    )
  }

  if (!experiment) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">实验不存在</div>
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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{experiment.name}</h1>
            <p className="text-gray-600 mt-1">{experiment.description || "暂无描述"}</p>
          </div>
          <div className="flex items-center space-x-2">
            {experiment.status === "pending" || experiment.status === "failed" ? (
              <button
                onClick={handleRun}
                disabled={running}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
              >
                {running ? "运行中..." : "运行实验"}
              </button>
            ) : null}
            <span className={`px-3 py-1 text-sm rounded ${getStatusColor(experiment.status)}`}>
              {experiment.status}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Experiment Info */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">实验信息</h2>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">协作模式</span>
                <span className="font-medium">{getCollaborationTypeLabel(experiment.collaboration_type)}</span>
              </div>

              {experiment.collaboration_type === "debate" && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">最大讨论轮数</span>
                  <span className="font-medium">
                    {(experiment.workflow_config.max_rounds as number) || 3}
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between">
                <span className="text-gray-600">参与者数量</span>
                <span className="font-medium">{participants.length}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-gray-600">创建时间</span>
                <span className="font-medium">
                  {new Date(experiment.created_at).toLocaleString("zh-CN")}
                </span>
              </div>
            </div>
          </div>

          {/* Participants */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">参与者</h2>

            <div className="space-y-3">
              {participants.map((participant) => (
                <div
                  key={participant.id}
                  className="flex items-center justify-between p-3 border border-gray-200 rounded-md"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-blue-600 font-medium">
                        {participant.role === "leader" ? "L" :
                         participant.role === "worker" ? "W" :
                         participant.role === "reviewer" ? "R" : "O"}
                      </span>
                    </div>
                    <div>
                      <div className="font-medium">Agent #{participant.agent_id.slice(0, 8)}</div>
                      <div className="text-sm text-gray-500">执行顺序: #{participant.join_order}</div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs rounded ${getRoleBadge(participant.role)}`}>
                      {participant.role}
                    </span>
                    <span className={`px-2 py-1 text-xs rounded ${getStatusColor(participant.status)}`}>
                      {participant.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Agent Messages */}
          {messages.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Agent 通信记录</h2>

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className="p-3 border border-gray-200 rounded-md bg-gray-50"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-sm">
                          Agent #{message.from.slice(0, 8)}
                        </span>
                        <span className="text-gray-400">→</span>
                        <span className="font-medium text-sm">
                          {message.to === "*" ? "所有人" : `Agent #${message.to.slice(0, 8)}`}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {new Date(message.timestamp).toLocaleTimeString("zh-CN")}
                      </span>
                    </div>

                    <div className="text-sm text-gray-700">
                      {message.message.round && (
                        <span className="inline-block px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs mr-2">
                          第 {message.message.round} 轮
                        </span>
                      )}
                      {message.message.action && (
                        <span className="inline-block px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                          {message.message.action}
                        </span>
                      )}
                    </div>

                    {message.message.output && (
                      <div className="mt-2 p-2 bg-white rounded border border-gray-200">
                        <pre className="text-xs overflow-x-auto">
                          {JSON.stringify(message.message.output, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Input Data */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">输入数据</h2>

            <div className="bg-gray-50 p-3 rounded-md">
              <pre className="text-xs overflow-x-auto">
                {JSON.stringify(experiment.input_data, null, 2)}
              </pre>
            </div>
          </div>

          {/* Output Data */}
          {experiment.status === "success" && Object.keys(experiment.output_data).length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">输出结果</h2>

              <div className="bg-gray-50 p-3 rounded-md">
                <pre className="text-xs overflow-x-auto">
                  {JSON.stringify(experiment.output_data, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Workflow Status */}
          {experiment.collaboration_type === "debate" && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">讨论进度</h2>

              <div className="space-y-2">
                {Array.from({ length: (experiment.workflow_config.max_rounds as number) || 3 }).map((_, i) => {
                  const roundMessages = messages.filter(m => m.message.round === i + 1)
                  const completed = roundMessages.length > 0

                  return (
                    <div
                      key={i}
                      className={`flex items-center space-x-2 p-2 rounded ${
                        completed ? "bg-green-50" : "bg-gray-50"
                      }`}
                    >
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                        completed ? "bg-green-500 text-white" : "bg-gray-300"
                      }`}>
                        {completed ? "✓" : i + 1}
                      </div>
                      <span className="text-sm">第 {i + 1} 轮讨论</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
