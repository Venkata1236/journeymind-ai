import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getHistory, deleteTrip } from '../services/api.js'

function TripCard({ trip, onView, onDelete }) {
  const [deleting, setDeleting] = useState(false)

  const handleDelete = async (e) => {
    e.stopPropagation()
    if (!confirm('Delete this trip plan?')) return
    setDeleting(true)
    try { await onDelete(trip.trip_id) }
    finally { setDeleting(false) }
  }

  const feasColor = {
    FEASIBLE:    'text-green-400 bg-green-900/30 border-green-800',
    TIGHT:       'text-yellow-400 bg-yellow-900/30 border-yellow-800',
    OVER_BUDGET: 'text-red-400 bg-red-900/30 border-red-800',
  }[trip.budget_feasibility] || 'text-slate-400 bg-surface-700 border-surface-600'

  return (
    <div
      onClick={() => onView(trip)}
      className="bg-surface-800 border border-surface-600 rounded-2xl p-5
                 hover:border-primary-500 cursor-pointer transition-all group"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-white font-bold text-base truncate group-hover:text-primary-400 transition">
            {trip.destinations?.join(' → ') || 'Unknown Route'}
          </h3>
          <p className="text-slate-500 text-xs mt-1">
            from {trip.origin} · {trip.duration_days} days
          </p>
          <div className="flex items-center gap-3 mt-3 flex-wrap">
            <span className="text-primary-400 text-sm font-semibold">
              ₹{trip.total_budget_inr?.toLocaleString('en-IN')}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${feasColor}`}>
              {trip.budget_feasibility}
            </span>
            <span className="text-slate-600 text-xs">
              {trip.best_season}
            </span>
          </div>
        </div>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="text-slate-600 hover:text-red-400 transition text-lg flex-shrink-0 p-1
                     opacity-0 group-hover:opacity-100"
          title="Delete"
        >
          {deleting ? '...' : '🗑'}
        </button>
      </div>
    </div>
  )
}

export default function HistoryPage() {
  const navigate = useNavigate()
  const [trips, setTrips]     = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  const load = async () => {
    setLoading(true); setError(null)
    try {
      const data = await getHistory(20, 0)
      setTrips(data.trips || data || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleView = (trip) => {
    sessionStorage.setItem('tripPlan', JSON.stringify(trip))
    navigate('/itinerary')
  }

  const handleDelete = async (tripId) => {
    await deleteTrip(tripId)
    setTrips(t => t.filter(x => x.trip_id !== tripId))
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-10 space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Trip History</h1>
          <p className="text-slate-400 text-sm mt-1">
            {trips.length} saved plan{trips.length !== 1 ? 's' : ''}
          </p>
        </div>
        <button
          onClick={() => navigate('/')}
          className="px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white
                     rounded-xl text-sm font-medium transition"
        >
          + New Trip
        </button>
      </div>

      {/* States */}
      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-28 bg-surface-800 rounded-2xl border border-surface-600 animate-pulse" />
          ))}
        </div>
      )}

      {error && (
        <div className="bg-red-900/30 border border-red-800 rounded-xl p-4 text-red-300 text-sm">
          ⚠️ {error}
          <button onClick={load} className="ml-3 underline hover:no-underline">Retry</button>
        </div>
      )}

      {!loading && !error && trips.length === 0 && (
        <div className="text-center py-20 bg-surface-800 rounded-2xl border border-surface-600">
          <div className="text-5xl mb-4">🗺️</div>
          <h3 className="text-white font-semibold mb-2">No trips planned yet</h3>
          <p className="text-slate-400 text-sm mb-6">
            Generate your first AI-powered trip plan
          </p>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-2.5 bg-primary-600 hover:bg-primary-500 text-white
                       rounded-xl text-sm font-medium transition"
          >
            Plan Your First Trip
          </button>
        </div>
      )}

      {!loading && trips.length > 0 && (
        <div className="space-y-3">
          {trips.map(trip => (
            <TripCard
              key={trip.trip_id}
              trip={trip}
              onView={handleView}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

    </div>
  )
}