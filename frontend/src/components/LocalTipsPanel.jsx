import { useState } from 'react'

const TABS = [
  { key: 'food_spots',         label: '🍜 Food Spots',   },
  { key: 'cultural_etiquette', label: '🙏 Etiquette',    },
  { key: 'common_mistakes',    label: '⚠️ Avoid These',  },
  { key: 'packing_list',       label: '🎒 Packing List', },
  { key: 'safety_tips',        label: '🛡️ Safety',       },
]

const TAB_EMPTY = {
  food_spots:         'No food spots found.',
  cultural_etiquette: 'No etiquette tips found.',
  common_mistakes:    'No common mistakes found.',
  packing_list:       'No packing list found.',
  safety_tips:        'No safety tips found.',
}

// Strip markdown bold (**text**) for clean display
function cleanText(text) {
  return text?.replace(/\*\*(.*?)\*\*/g, '$1').trim() || ''
}

function FoodSpotItem({ item }) {
  const clean = cleanText(item)
  // Pattern: "Name — City — Dish — ₹price"
  const parts = clean.split('—').map(p => p.trim())
  if (parts.length >= 3) {
    return (
      <div className="bg-surface-700 rounded-xl p-4 border border-surface-600 hover:border-surface-500 transition">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-white font-semibold text-sm">{parts[0]}</div>
            {parts[1] && <div className="text-primary-400 text-xs mt-0.5">{parts[1]}</div>}
            {parts[2] && <div className="text-slate-400 text-xs mt-1">Try: {parts[2]}</div>}
          </div>
          {parts[3] && (
            <span className="text-green-400 text-xs font-bold bg-green-900/30 px-2 py-1 rounded-lg flex-shrink-0 border border-green-800">
              {parts[3].startsWith('₹') ? parts[3] : `₹${parts[3]}`}
            </span>
          )}
        </div>
      </div>
    )
  }
  return (
    <div className="bg-surface-700 rounded-xl p-4 border border-surface-600 text-slate-300 text-sm">
      {clean}
    </div>
  )
}

function GenericItem({ item, index }) {
  return (
    <div className="flex gap-3 items-start bg-surface-700 rounded-xl p-4 border border-surface-600 hover:border-surface-500 transition">
      <span className="w-6 h-6 rounded-full bg-primary-900/50 border border-primary-800 text-primary-400 text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
        {index + 1}
      </span>
      <p className="text-slate-300 text-sm leading-relaxed">
        {cleanText(item)}
      </p>
    </div>
  )
}

function PackingItem({ item, index }) {
  const [checked, setChecked] = useState(false)
  return (
    <div
      onClick={() => setChecked(c => !c)}
      className={`flex gap-3 items-center rounded-xl p-3 border cursor-pointer transition ${
        checked
          ? 'bg-green-900/20 border-green-800 opacity-60'
          : 'bg-surface-700 border-surface-600 hover:border-surface-500'
      }`}
    >
      <div className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition ${
        checked ? 'bg-green-500 border-green-500' : 'border-surface-500'
      }`}>
        {checked && <span className="text-white text-xs">✓</span>}
      </div>
      <span className={`text-sm ${checked ? 'line-through text-slate-500' : 'text-slate-300'}`}>
        {cleanText(item)}
      </span>
    </div>
  )
}

export default function LocalTipsPanel({ localTips }) {
  const [activeTab, setActiveTab] = useState('food_spots')

  if (!localTips) return null

  const items = localTips[activeTab] || []

  return (
    <div className="space-y-4">

      {/* Header */}
      <h3 className="text-white font-bold text-lg">📍 Local Insider Tips</h3>

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-all border ${
              activeTab === tab.key
                ? 'bg-primary-600 border-primary-500 text-white'
                : 'bg-surface-800 border-surface-600 text-slate-400 hover:border-slate-500'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="space-y-3 animate-fade-in">
        {items.length === 0 ? (
          <div className="text-slate-500 text-sm text-center py-8 bg-surface-800 rounded-2xl border border-surface-600">
            {TAB_EMPTY[activeTab]}
          </div>
        ) : activeTab === 'food_spots' ? (
          items.map((item, i) => <FoodSpotItem key={i} item={item} />)
        ) : activeTab === 'packing_list' ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {items.map((item, i) => <PackingItem key={i} item={item} index={i} />)}
          </div>
        ) : (
          items.map((item, i) => <GenericItem key={i} item={item} index={i} />)
        )}
      </div>

      {/* Packing counter */}
      {activeTab === 'packing_list' && items.length > 0 && (
        <div className="text-xs text-slate-500 text-right">
          Click items to check them off
        </div>
      )}

    </div>
  )
}