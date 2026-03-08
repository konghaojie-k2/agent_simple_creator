'use client'

import { useEffect, useState } from 'react'
import { UserSoul, SoulUpdateRequest } from '@/types'
import { soulApi } from '@/lib/api'

export default function SoulSettingsPage() {
  const [soul, setSoul] = useState<UserSoul | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editMode, setEditMode] = useState(false)

  // 编辑状态
  const [editedSoul, setEditedSoul] = useState<SoulUpdateRequest>({})
  const [newTruth, setNewTruth] = useState('')
  const [newBoundary, setNewBoundary] = useState('')

  useEffect(() => {
    loadSoul()
  }, [])

  const loadSoul = async () => {
    setLoading(true)
    try {
      const data = await soulApi.get()
      setSoul(data)
      setEditedSoul({
        core_truths: data.core_truths || [],
        boundaries: data.boundaries || [],
        vibe: data.vibe || '',
        soul_content: data.soul_content || '',
      })
    } catch (error) {
      console.error('Failed to load soul:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const updated = await soulApi.update(editedSoul)
      setSoul(updated)
      setEditMode(false)
    } catch (error) {
      console.error('Failed to save soul:', error)
      alert('保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleReset = async () => {
    if (!confirm('确定要重置为默认 SOUL 吗？')) return

    setSaving(true)
    try {
      const template = await soulApi.getTemplate()
      setEditedSoul({
        core_truths: template.core_truths,
        boundaries: template.boundaries,
        vibe: template.vibe,
        soul_content: template.soul_content,
      })
    } catch (error) {
      console.error('Failed to reset soul:', error)
    } finally {
      setSaving(false)
    }
  }

  const addTruth = () => {
    if (!newTruth.trim()) return
    setEditedSoul({
      ...editedSoul,
      core_truths: [...(editedSoul.core_truths || []), newTruth],
    })
    setNewTruth('')
  }

  const removeTruth = (index: number) => {
    setEditedSoul({
      ...editedSoul,
      core_truths: editedSoul.core_truths?.filter((_, i) => i !== index),
    })
  }

  const addBoundary = () => {
    if (!newBoundary.trim()) return
    setEditedSoul({
      ...editedSoul,
      boundaries: [...(editedSoul.boundaries || []), newBoundary],
    })
    setNewBoundary('')
  }

  const removeBoundary = (index: number) => {
    setEditedSoul({
      ...editedSoul,
      boundaries: editedSoul.boundaries?.filter((_, i) => i !== index),
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">加载中...</div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">SOUL 设置</h1>
        <p className="text-gray-600 mt-2">
          你的 SOUL 是所有 Agent 共享的核心价值观和行为准则。
          <br />
          这里的设置会影响你创建的所有 Agent。
        </p>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center mb-6">
        <div className="text-sm text-gray-500">
          {editMode ? '编辑模式' : '查看模式'}
        </div>
        <div className="space-x-2">
          {editMode ? (
            <>
              <button
                onClick={() => setEditMode(false)}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
              >
                {saving ? '保存中...' : '保存'}
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleReset}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                重置为默认
              </button>
              <button
                onClick={() => setEditMode(true)}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
              >
                编辑
              </button>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Core Truths */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">核心价值观 (Core Truths)</h2>

          {editMode ? (
            <div className="space-y-3">
              <ul className="space-y-2">
                {editedSoul.core_truths?.map((truth, index) => (
                  <li key={index} className="flex items-center justify-between bg-blue-50 px-3 py-2 rounded">
                    <span className="text-sm">{truth}</span>
                    <button
                      onClick={() => removeTruth(index)}
                      className="text-red-500 hover:text-red-700"
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newTruth}
                  onChange={(e) => setNewTruth(e.target.value)}
                  className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm"
                  placeholder="添加新的价值观..."
                  onKeyPress={(e) => e.key === 'Enter' && addTruth()}
                />
                <button
                  onClick={addTruth}
                  className="px-3 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
                >
                  添加
                </button>
              </div>
            </div>
          ) : (
            <ul className="space-y-2">
              {soul?.core_truths?.map((truth, index) => (
                <li key={index} className="text-sm text-gray-700 bg-blue-50 px-3 py-2 rounded">
                  {truth}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Boundaries */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">行为边界 (Boundaries)</h2>

          {editMode ? (
            <div className="space-y-3">
              <ul className="space-y-2">
                {editedSoul.boundaries?.map((boundary, index) => (
                  <li key={index} className="flex items-center justify-between bg-red-50 px-3 py-2 rounded">
                    <span className="text-sm">{boundary}</span>
                    <button
                      onClick={() => removeBoundary(index)}
                      className="text-red-500 hover:text-red-700"
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newBoundary}
                  onChange={(e) => setNewBoundary(e.target.value)}
                  className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm"
                  placeholder="添加新的边界..."
                  onKeyPress={(e) => e.key === 'Enter' && addBoundary()}
                />
                <button
                  onClick={addBoundary}
                  className="px-3 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
                >
                  添加
                </button>
              </div>
            </div>
          ) : (
            <ul className="space-y-2">
              {soul?.boundaries?.map((boundary, index) => (
                <li key={index} className="text-sm text-gray-700 bg-red-50 px-3 py-2 rounded">
                  {boundary}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Vibe */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">风格/氛围 (Vibe)</h2>

          {editMode ? (
            <textarea
              value={editedSoul.vibe || ''}
              onChange={(e) => setEditedSoul({ ...editedSoul, vibe: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              rows={3}
              placeholder="描述你想要的 Agent 风格..."
            />
          ) : (
            <p className="text-sm text-gray-700 bg-purple-50 px-3 py-2 rounded">
              {soul?.vibe || '未设置'}
            </p>
          )}
        </div>

        {/* Full SOUL Content (Markdown) */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">完整 SOUL 内容 (Markdown)</h2>

          {editMode ? (
            <textarea
              value={editedSoul.soul_content || ''}
              onChange={(e) => setEditedSoul({ ...editedSoul, soul_content: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono"
              rows={10}
              placeholder="完整的 SOUL.md 内容..."
            />
          ) : (
            <div className="bg-gray-50 rounded-md p-4 max-h-64 overflow-y-auto">
              <pre className="text-sm text-gray-800 whitespace-pre-wrap font-sans">
                {soul?.soul_content || '未设置'}
              </pre>
            </div>
          )}
        </div>
      </div>

      {/* Info */}
      <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h3 className="font-semibold text-yellow-800 mb-2">关于 SOUL</h3>
        <p className="text-sm text-yellow-700">
          SOUL 是你所有 Agent 共享的核心价值观。它定义了 Agent 的基本行为准则和风格。
          参考了 clawdbot 的 SOUL.md 设计理念。
        </p>
      </div>
    </div>
  )
}
