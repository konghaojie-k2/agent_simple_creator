'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import { Agent, AgentIdentity } from '@/types'
import { agentsApi } from '@/lib/api'

// 可选的生物类型
const CREATURE_OPTIONS = [
  'AI助手', '猫', '狗', '狐狸', '龙', '巫师', '工程师',
  '老师', '医生', '作家', '艺术家', '科学家', '商人', '其他'
]

// 可选的风格
const VIBE_OPTIONS = [
  'friendly', 'professional', 'playful', 'serious', 'casual',
  'enthusiastic', 'calm', 'helpful', 'creative', 'analytical'
]

// 可选的emoji
const EMOJI_OPTIONS = [
  '🤖', '🐱', '🐶', '🦊', '🐉', '🧙', '👨‍💻',
  '👩‍🏫', '👨‍⚕️', '✍️', '🎨', '🔬', '💼', '🌟', '💡'
]

export default function AgentIdentityPage() {
  const router = useRouter()
  const params = useParams()
  const agentId = params.id as string

  const [agent, setAgent] = useState<Agent | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // 表单状态
  const [identityName, setIdentityName] = useState('')
  const [creature, setCreature] = useState('')
  const [vibe, setVibe] = useState('')
  const [emoji, setEmoji] = useState('')
  const [avatar, setAvatar] = useState('')

  useEffect(() => {
    loadAgent()
  }, [agentId])

  const loadAgent = async () => {
    setLoading(true)
    try {
      const data = await agentsApi.getDetail(agentId)
      setAgent(data)

      // 初始化表单
      if (data.identity) {
        setIdentityName(data.identity.name || '')
        setCreature(data.identity.creature || '')
        setVibe(data.identity.vibe || '')
        setEmoji(data.identity.emoji || '')
        setAvatar(data.identity.avatar || '')
      }
    } catch (error) {
      console.error('Failed to load agent:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const identity: AgentIdentity = {
        name: identityName || undefined,
        creature: creature || undefined,
        vibe: vibe || undefined,
        emoji: emoji || undefined,
        avatar: avatar || undefined
      }

      await agentsApi.update(agentId, {
        identity
      })

      alert('Identity 更新成功！')
      router.push(`/agents/${agentId}`)
    } catch (error) {
      console.error('Failed to save identity:', error)
      alert('更新失败，请重试')
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => {
    if (agent?.identity) {
      setIdentityName(agent.identity.name || '')
      setCreature(agent.identity.creature || '')
      setVibe(agent.identity.vibe || '')
      setEmoji(agent.identity.emoji || '')
      setAvatar(agent.identity.avatar || '')
    } else {
      setIdentityName('')
      setCreature('')
      setVibe('')
      setEmoji('')
      setAvatar('')
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
    <div className="max-w-3xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <Link
            href={`/agents/${agentId}`}
            className="text-blue-500 hover:text-blue-600"
          >
            ← 返回 Agent 详情
          </Link>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          {agent.name} - Identity 设置
        </h1>
        <p className="text-gray-600 mt-1">定义 Agent 的身份特征和个性风格</p>
      </div>

      {/* 预览 */}
      <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg p-6 mb-6 text-white">
        <div className="flex items-center gap-4">
          <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center text-4xl">
            {emoji || '🤖'}
          </div>
          <div>
            <div className="text-2xl font-bold">
              {identityName || agent.name}
              {vibe && <span className="text-white/80 text-lg ml-2">({vibe})</span>}
            </div>
            {creature && <div className="text-white/80">{creature}</div>}
            {avatar && <div className="text-white/60 text-sm mt-1">Avatar: {avatar}</div>}
          </div>
        </div>
      </div>

      {/* 表单 */}
      <div className="bg-white rounded-lg shadow p-6 space-y-6">
        {/* Identity Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Identity 名称
          </label>
          <input
            type="text"
            value={identityName}
            onChange={(e) => setIdentityName(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-purple-500 focus:border-purple-500"
            placeholder="例如：智能助手小A"
          />
          <p className="text-sm text-gray-500 mt-1">Agent 的自定义名称（可选）</p>
        </div>

        {/* Creature */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            生物类型
          </label>
          <select
            value={creature}
            onChange={(e) => setCreature(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-purple-500 focus:border-purple-500"
          >
            <option value="">选择生物类型...</option>
            {CREATURE_OPTIONS.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <p className="text-sm text-gray-500 mt-1">Agent 是什么样的角色/实体</p>
        </div>

        {/* Vibe */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            风格/氛围
          </label>
          <select
            value={vibe}
            onChange={(e) => setVibe(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-purple-500 focus:border-purple-500"
          >
            <option value="">选择风格...</option>
            {VIBE_OPTIONS.map((v) => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>
          <p className="text-sm text-gray-500 mt-1">Agent 对话的风格特点</p>
        </div>

        {/* Emoji */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Emoji 头像
          </label>
          <div className="flex flex-wrap gap-2">
            {EMOJI_OPTIONS.map((e) => (
              <button
                key={e}
                type="button"
                onClick={() => setEmoji(e)}
                className={`w-12 h-12 rounded-lg flex items-center justify-center text-2xl transition-all ${
                  emoji === e
                    ? 'bg-purple-100 ring-2 ring-purple-500 scale-110'
                    : 'bg-gray-50 hover:bg-gray-100'
                }`}
              >
                {e}
              </button>
            ))}
          </div>
          <p className="text-sm text-gray-500 mt-1">选择 Agent 的 emoji 代表</p>
        </div>

        {/* Avatar URL */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Avatar 图片链接（可选）
          </label>
          <input
            type="text"
            value={avatar}
            onChange={(e) => setAvatar(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-purple-500 focus:border-purple-500"
            placeholder="https://example.com/avatar.png"
          />
          <p className="text-sm text-gray-500 mt-1">如果设置，将优先使用图片 Avatar</p>
        </div>

        {/* Actions */}
        <div className="flex gap-4 pt-4 border-t">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex-1 bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 disabled:opacity-50 transition-colors"
          >
            {saving ? '保存中...' : '保存 Identity'}
          </button>
          <button
            onClick={handleReset}
            className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            重置
          </button>
        </div>
      </div>

      {/* 提示 */}
      <div className="mt-6 bg-blue-50 rounded-lg p-4 text-sm text-blue-800">
        <h3 className="font-medium mb-2">💡 Identity 的作用</h3>
        <ul className="list-disc list-inside space-y-1">
          <li>Identity 定义了 Agent 的身份特征和个性风格</li>
          <li>这些信息会注入到动态提示词中，影响 Agent 的对话方式</li>
          <li>在实验执行时，Agent 会根据 Identity 调整自己的行为</li>
        </ul>
      </div>
    </div>
  )
}
