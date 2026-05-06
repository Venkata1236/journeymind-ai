import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ItineraryTimeline from '../components/ItineraryTimeline.jsx'
import BudgetBreakdown   from '../components/BudgetBreakdown.jsx'
import WeatherWidget     from '../components/WeatherWidget.jsx'
import LocalTipsPanel    from '../components/LocalTipsPanel.jsx'

const TABS = [
  { key: 'itinerary', label: '🗓️ Itinerary'   },
  { key: 'budget',    label: '💰 Budget'       },
  { key: 'weather',   label: '🌦️ Weather'      },
  { key: 'tips',      label: '📍 Local Tips'   },
]

export default function ItineraryPage() {
  const navigate  = useNavigate()
  const [plan, setPlan]     = useState(null)
  const [activeTab, setTab] = useState('itinerary')

  useEffect(() => {
    const raw = sessionStorage.getItem('tripPlan')
    if (!raw) { navigate('/'); return }
    try { setPlan(JSON.parse(raw)) }
    catch { navigate('/') }
  }, [navigate])

  if (!plan) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-slate-400">Loading plan...</div>
    </div>
  )

  const { trip_summary, itinerary, budget_breakdown,
          weather_info, local_tips } = plan

  return (
    <div className="max-w-4xl mx-auto px-4 py-10 space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">
            {trip_summary.destinations.join(' & ')}
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            {trip_summary.origin} · {trip_summary.duration_days} days ·
            ₹{trip_summary.total_budget_inr?.toLocaleString('en-IN')}
          </p>
        </div>
        <button
          onClick={() => navigate('/')}
          className="px-4 py-2 bg-surface-800 border border-surface-600 text-slate-300
                     hover:border-primary-500 hover:text-white rounded-xl text-sm transition"
        >
          ← Plan New Trip
        </button>
      </div>

      {/* Tab bar */}
      <div className="flex gap-2 overflow-x-auto pb-1 border-b border-surface-600">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setTab(tab.key)}
            className={`flex-shrink-0 px-5 py-2.5 text-sm font-medium transition-all border-b-2 -mb-px ${
              activeTab === tab.key
                ? 'border-primary-500 text-primary-400'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="animate-fade-in">
        {activeTab === 'itinerary' && (
          <ItineraryTimeline
            itinerary={itinerary}
            tripSummary={trip_summary}
          />
        )}
        {activeTab === 'budget' && (
          <BudgetBreakdown budget={{
            ...budget_breakdown,
            group_size:    trip_summary.group_size    || 2,
            duration_days: trip_summary.duration_days || 5,
          }} />
        )}
        {activeTab === 'weather' && (
          <WeatherWidget weatherInfo={weather_info} />
        )}
        {activeTab === 'tips' && (
          <LocalTipsPanel localTips={local_tips} />
        )}
      </div>

    </div>
  )
}