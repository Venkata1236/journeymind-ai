import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { planTrip } from '../services/api'

const TRAVEL_STYLES = [
  { value: 'budget',   label: '🎒 Budget',   desc: 'Hostels, local dhabas' },
  { value: 'comfort',  label: '🏨 Comfort',  desc: 'Mid-range hotels' },
  { value: 'heritage', label: '🏰 Heritage', desc: 'Havelis, palace stays' },
  { value: 'luxury',   label: '💎 Luxury',   desc: 'Five-star resorts' },
]

const ACCOMMODATION_OPTIONS = [
  { value: 'budget_hostel', label: 'Budget Hostel' },
  { value: 'guesthouse',    label: 'Guesthouse' },
  { value: 'hotel',         label: 'Hotel' },
  { value: 'heritage',      label: 'Heritage / Haveli' },
  { value: 'resort',        label: 'Resort' },
]

const INTEREST_OPTIONS = [
  'forts', 'temples', 'street food', 'photography',
  'shopping', 'adventure', 'wildlife', 'beaches',
  'art & culture', 'nightlife', 'trekking', 'history',
]

const DEFAULT_FORM = {
  origin: '',
  destinations: '',
  duration_days: 5,
  budget_inr: 35000,
  group_size: 2,
  travel_style: 'heritage',
  accommodation_preference: 'hotel',
  trip_start_date: '',
  interests: [],
}

export default function TripPlannerForm() {
  const navigate = useNavigate()
  const [form, setForm] = useState(DEFAULT_FORM)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [agentStep, setAgentStep] = useState(0)

  const AGENT_STEPS = [
    'Researching destinations...',
    'Building your itinerary...',
    'Analysing budget...',
    'Gathering local tips...',
    'Finalising your plan...',
  ]

  const toggleInterest = (interest) => {
    setForm(f => ({
      ...f,
      interests: f.interests.includes(interest)
        ? f.interests.filter(i => i !== interest)
        : [...f.interests, interest],
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    setAgentStep(0)

    // Animate agent steps every 12s
    const interval = setInterval(() => {
      setAgentStep(s => Math.min(s + 1, AGENT_STEPS.length - 1))
    }, 12000)

    try {
      const payload = {
        ...form,
        duration_days: Number(form.duration_days),
        budget_inr: Number(form.budget_inr),
        group_size: Number(form.group_size),
        destinations: form.destinations
          .split(',')
          .map(d => d.trim())
          .filter(Boolean),
        interests: form.interests.length ? form.interests : ['sightseeing'],
      }

      const result = await planTrip(payload)
      sessionStorage.setItem('tripPlan', JSON.stringify(result))
      navigate('/itinerary')
    } catch (err) {
      setError(err.message)
    } finally {
      clearInterval(interval)
      setLoading(false)
      setAgentStep(0)
    }
  }

  // ── Loading overlay ──────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-900">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="relative w-24 h-24 mx-auto mb-8">
            <div className="absolute inset-0 rounded-full border-4 border-primary-800 animate-pulse" />
            <div className="absolute inset-2 rounded-full border-4 border-t-primary-400 border-r-primary-400 border-b-transparent border-l-transparent animate-spin" />
            <div className="absolute inset-0 flex items-center justify-center">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                <circle cx="16" cy="16" r="15" stroke="#0ea5e9" strokeWidth="2"/>
                <path d="M8 20 Q12 8 16 14 Q20 20 24 10" stroke="#0ea5e9" strokeWidth="2" strokeLinecap="round" fill="none"/>
                <circle cx="24" cy="10" r="2.5" fill="#38bdf8"/>
              </svg>
            </div>
          </div>

          <h2 className="text-2xl font-bold text-white mb-2">Planning Your Trip</h2>
          <p className="text-primary-400 font-medium mb-6 animate-pulse">
            {AGENT_STEPS[agentStep]}
          </p>

          <div className="space-y-3">
            {['🔍 Destination Research', '🗓️ Itinerary Planning', '💰 Budget Analysis', '🍜 Local Expert'].map((step, i) => (
              <div key={i} className="flex items-center gap-3 bg-surface-800 rounded-lg px-4 py-3">
                <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                  i < agentStep ? 'bg-green-400' :
                  i === agentStep ? 'bg-primary-400 animate-pulse' :
                  'bg-surface-600'
                }`} />
                <span className={`text-sm ${
                  i < agentStep ? 'text-green-400' :
                  i === agentStep ? 'text-white' :
                  'text-slate-500'
                }`}>{step}</span>
                {i < agentStep && <span className="ml-auto text-green-400 text-xs">Done</span>}
                {i === agentStep && <span className="ml-auto text-primary-400 text-xs animate-pulse">Running...</span>}
              </div>
            ))}
          </div>

          <p className="text-slate-500 text-sm mt-6">
            AI agents are working in sequence — this takes ~60 seconds
          </p>
        </div>
      </div>
    )
  }

  // ── Form ─────────────────────────────────────────────────────────
  return (
    <div className="max-w-3xl mx-auto px-4 py-12">

      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold text-white mb-3">
          Plan Your <span className="text-primary-400">Dream Trip</span>
        </h1>
        <p className="text-slate-400 text-lg">
          4 AI agents will research, plan, budget, and personalise your journey
        </p>
      </div>

      {error && (
        <div className="mb-6 bg-red-900/40 border border-red-700 rounded-xl p-4 text-red-300 text-sm">
          ⚠️ {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">

        {/* Origin + Destinations */}
        <div className="bg-surface-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-white font-semibold text-lg">🗺️ Where</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-slate-400 text-sm mb-1 block">Flying from</label>
              <input
                type="text"
                required
                placeholder="e.g. Hyderabad"
                value={form.origin}
                onChange={e => setForm(f => ({ ...f, origin: e.target.value }))}
                className="w-full bg-surface-700 border border-surface-600 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-primary-500 transition"
              />
            </div>
            <div>
              <label className="text-slate-400 text-sm mb-1 block">Destinations (comma separated)</label>
              <input
                type="text"
                required
                placeholder="e.g. Jaipur, Jodhpur"
                value={form.destinations}
                onChange={e => setForm(f => ({ ...f, destinations: e.target.value }))}
                className="w-full bg-surface-700 border border-surface-600 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-primary-500 transition"
              />
            </div>
          </div>
        </div>

        {/* Dates + Duration */}
        <div className="bg-surface-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-white font-semibold text-lg">📅 When & How Long</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="text-slate-400 text-sm mb-1 block">Start Date</label>
              <input
                type="date"
                required
                value={form.trip_start_date}
                onChange={e => setForm(f => ({ ...f, trip_start_date: e.target.value }))}
                className="w-full bg-surface-700 border border-surface-600 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-primary-500 transition"
              />
            </div>
            <div>
              <label className="text-slate-400 text-sm mb-1 block">Duration (days)</label>
              <input
                type="number"
                min={2} max={21}
                value={form.duration_days}
                onChange={e => setForm(f => ({ ...f, duration_days: e.target.value }))}
                className="w-full bg-surface-700 border border-surface-600 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-primary-500 transition"
              />
            </div>
            <div>
              <label className="text-slate-400 text-sm mb-1 block">Group Size</label>
              <input
                type="number"
                min={1} max={20}
                value={form.group_size}
                onChange={e => setForm(f => ({ ...f, group_size: e.target.value }))}
                className="w-full bg-surface-700 border border-surface-600 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-primary-500 transition"
              />
            </div>
          </div>
        </div>

        {/* Budget */}
        <div className="bg-surface-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-white font-semibold text-lg">💰 Budget</h2>
          <div>
            <div className="flex justify-between mb-2">
              <label className="text-slate-400 text-sm">Total Budget (INR)</label>
              <span className="text-primary-400 font-bold">₹{Number(form.budget_inr).toLocaleString('en-IN')}</span>
            </div>
            <input
              type="range"
              min={5000} max={500000} step={1000}
              value={form.budget_inr}
              onChange={e => setForm(f => ({ ...f, budget_inr: e.target.value }))}
              className="w-full accent-primary-500"
            />
            <div className="flex justify-between text-xs text-slate-600 mt-1">
              <span>₹5,000</span>
              <span>₹5,00,000</span>
            </div>
          </div>
        </div>

        {/* Travel Style */}
        <div className="bg-surface-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-white font-semibold text-lg">✈️ Travel Style</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {TRAVEL_STYLES.map(({ value, label, desc }) => (
              <button
                key={value}
                type="button"
                onClick={() => setForm(f => ({ ...f, travel_style: value }))}
                className={`rounded-xl p-4 text-left transition-all border ${
                  form.travel_style === value
                    ? 'bg-primary-900/50 border-primary-500 text-white'
                    : 'bg-surface-700 border-surface-600 text-slate-400 hover:border-slate-500'
                }`}
              >
                <div className="font-medium text-sm mb-1">{label}</div>
                <div className="text-xs opacity-70">{desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Accommodation */}
        <div className="bg-surface-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-white font-semibold text-lg">🏨 Accommodation</h2>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {ACCOMMODATION_OPTIONS.map(({ value, label }) => (
              <button
                key={value}
                type="button"
                onClick={() => setForm(f => ({ ...f, accommodation_preference: value }))}
                className={`rounded-xl px-3 py-3 text-sm text-center transition-all border ${
                  form.accommodation_preference === value
                    ? 'bg-primary-900/50 border-primary-500 text-white'
                    : 'bg-surface-700 border-surface-600 text-slate-400 hover:border-slate-500'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Interests */}
        <div className="bg-surface-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-white font-semibold text-lg">❤️ Interests</h2>
          <div className="flex flex-wrap gap-2">
            {INTEREST_OPTIONS.map(interest => (
              <button
                key={interest}
                type="button"
                onClick={() => toggleInterest(interest)}
                className={`px-4 py-2 rounded-full text-sm transition-all border capitalize ${
                  form.interests.includes(interest)
                    ? 'bg-primary-600 border-primary-500 text-white'
                    : 'bg-surface-700 border-surface-600 text-slate-400 hover:border-slate-500'
                }`}
              >
                {interest}
              </button>
            ))}
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          className="w-full bg-primary-600 hover:bg-primary-500 text-white font-bold py-4 rounded-2xl text-lg transition-all duration-200 shadow-lg shadow-primary-900/50"
        >
          🚀 Generate My Trip Plan
        </button>

      </form>
    </div>
  )
}