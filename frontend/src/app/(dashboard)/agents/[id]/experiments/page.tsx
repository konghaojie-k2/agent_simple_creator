"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { useAuth } from "@/contexts/AuthContext"
import { type Agent, type Experiment, type ExperimentParticipant } from "@/types"

// API client
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function AgentExperimentsPage() {
  const router = useRouter()
  const params = useParams()
  const agentId = params.id as string
  const { user, isLoading: authLoading } = useAuth()

  const [agent, setAgent] = useState<Agent | null>(null)
  const [experiments, setExperiments] = useState<Experiment[]>([])
  const [participations, setParticipations] = useState<ExperimentParticipant[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<"all" | "participated">("participated")

  useEffect(() => {
    if (user && agentId) {
      fetchAgent()
      fetchExperiments()
      fetchParticipations()
    }
  }, [user, agentId])

  const fetchAgent = async () => {
    try {
      const token = localStorage.getItem("token")
      const response = await fetch(`${API_URL}/api/agents/${agentId}`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setAgent(data)
      }
    } catch (error) {
      console.error("Failed to fetch agent:", error)
    }
  }

  const fetchExperiments = async () => {
    try {
      const token = localStorage.getItem("token")
      const response = await fetch(`${API_URL}/api/experiments?agent_id=${agentId}`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setExperiments(data)
      }
    } catch (error) {
      console.error("Failed to fetch experiments:", error)
    } finally {
      setLoading(false)
    }
  }

  const fetchParticipations = async () => {
    try {
      const token = localStorage.getItem("token")
      // Fetch all collaboration experiments and filter for this agent
      const response = await fetch(`${API_URL}/api/experiments`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      })

      if (response.ok) {
        const allExperiments: Experiment[] = await response.json()
        const collaborationExperiments = allExperiments.filter(
          exp => exp.collaboration_type && exp.status !== "pending"
        )

        // Fetch participants for each collaboration experiment
        const allExperimentParticipants: ExperimentParticipant[] = []
        for (const exp of collaborationExperiments) {
          try {
            const partResponse = await fetch(
              `${API_URL}/api/collaboration/experiments/${exp.id}/participants`,
              {
                headers: {
                  "Authorization": `Bearer ${token}`
                }
              }
            )
            if (partResponse.ok) {
              const parts: ExperimentParticipant[] = await partResponse.json()
              allExperimentParticipants.push(...parts.filter(p => p.agent_id === agentId))
            }
          } catch (e) {
            console.error("Failed to fetch participants:", e)
          }
        }
        setParticipations(allExperimentParticipants)
      }
    } catch (error) {
      console.error("Failed to fetch participations:", error)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "success": return "bg-green-100 text-green-800"
      case "failed": return "bg-red-100 text-red-800"
      case "running": return "bg-blue-100 text-blue-800"
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

  const stats = {
    totalExperiments: experiments.length,
    participatedExperiments: participations.length,
    successRate: (() => {
      const allExperiments = [...experiments, ...participations.map(p => experiments.find(e => e.id === p.experiment_id)).filter(Boolean) as Experiment[]]
      const completed = allExperiments.filter(e => e.status === "success").length
      return allExperiments.length > 0 ? Math.round((completed / allExperiments.length) * 100) : 0
    })()
  }

  if (authLoading || loading) {
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
        <h1 className="text-2xl font-bold text-gray-900">{agent.name} - 实验历史</h1>
        <p className="text-gray-600 mt-1">{agent.description || "暂无描述"}</p>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">主导实验</div>
          <div className="text-2xl font-bold text-gray-900">{stats.totalExperiments}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">参与实验</div>
          <div className="text-2xl font-bold text-gray-900">{stats.participatedExperiments}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">成功率</div>
          <div className="text-2xl font-bold text-green-600">{stats.successRate}%</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-2 mb-4">
        <button
          onClick={() => setFilter("all")}
          className={`px-4 py-2 rounded-md ${
            filter === "all"
              ? "bg-blue-500 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          主导的实验 ({experiments.length})
        </button>
        <button
          onClick={() => setFilter("participated")}
          className={`px-4 py-2 rounded-md ${
            filter === "participated"
              ? "bg-blue-500 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          参与的协作实验 ({participations.length})
        </button>
      </div>

      {/* Experiments List */}
      <div className="bg-white rounded-lg shadow">
        {filter === "all" ? (
          experiments.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              暂无主导的实验
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {experiments.map((experiment) => (
                <div
                  key={experiment.id}
                  onClick={() => router.push(`/experiments/${experiment.id}`)}
                  className="p-4 hover:bg-gray-50 cursor-pointer"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h3 className="font-medium text-gray-900">{experiment.name}</h3>
                        <span className={`px-2 py-1 text-xs rounded ${getStatusColor(experiment.status)}`}>
                          {experiment.status}
                        </span>
                        <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                          {experiment.experiment_type}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 mt-1">{experiment.description || "暂无描述"}</p>
                    </div>
                    <div className="text-sm text-gray-500">
                      {new Date(experiment.created_at).toLocaleDateString("zh-CN")}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )
        ) : (
          participations.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              暂无参与的协作实验
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {participations.map((participation) => {
                const experiment = experiments.find(e => e.id === participation.experiment_id)
                return (
                  <div
                    key={participation.id}
                    onClick={() => router.push(`/experiments/${participation.experiment_id}`)}
                    className="p-4 hover:bg-gray-50 cursor-pointer"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h3 className="font-medium text-gray-900">
                            {experiment?.name || "未知实验"}
                          </h3>
                          <span className={`px-2 py-1 text-xs rounded ${getRoleBadge(participation.role)}`}>
                            {participation.role}
                          </span>
                          <span className={`px-2 py-1 text-xs rounded ${getStatusColor(participation.status)}`}>
                            {participation.status}
                          </span>
                        </div>
                        <p className="text-sm text-gray-500 mt-1">
                          执行顺序: #{participation.join_order}
                        </p>
                      </div>
                      <div className="text-sm text-gray-500">
                        {experiment && new Date(experiment.created_at).toLocaleDateString("zh-CN")}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )
        )}
      </div>
    </div>
  )
}
