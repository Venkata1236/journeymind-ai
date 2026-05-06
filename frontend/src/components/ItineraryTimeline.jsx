import { useState } from 'react'

const TIME_ICONS = {
  morning:   '🌅',
  afternoon: '☀️',
  evening:   '🌆',
}

const FEASIBILITY_CONFIG = {
  FEASIBLE:    { label: 'Budget Feasible',   color: 'text-green-400',  bg: 'bg-green-900/30',  border: 'border-green-700' },
  TIGHT:       { label: 'Budget Tight',      color: 'text-yellow-400', bg: 'bg-yellow-900/30', border: 'border-yellow-700' },
  OVER_BUDGET: { label: 'Over Budget',       color: 'text-red-400',    bg: 'bg-red-900/30',    border: 'border-red-700' },
}

function cleanText(text) {
  return text?.replace(/\*\*(.*?)\*\*/g, '$1').trim() || ''
}

function SlotCard({ slot, period }) {
  if (!slot) return null
  return (
    <div className="flex gap-4 group">
      {/* Time indicator */}
      <div className="flex flex-col items-center flex-shrink-0">
        <div className="w-9 h-9 rounded-full bg-surface-700 border border-surface-600 flex items-center justify-center text-base group-hover:border-primary-500 transition">
          {TIME_ICONS[period]}
        </div>
        <div className="w-px flex-1 bg-surface-600 mt-1" />
      </div>

      {/* Content */}
      <div className="pb-5 flex-1">
        <div className="text-xs text-primary-400 font-medium mb-1">{slot.time}</div>
        <div className="bg-surface-800 rounded-xl p-4 border border-surface-600 hover:border-surface-500 transition">
          <div className="flex items-start justify-between gap-3 mb-2">
            <p className="text-white text-sm font-medium leading-snug">
              {cleanText(slot.activity)}
            </p>
            {slot.cost_inr > 0 && (
              <span className="text-primary-400 text-xs font-bold flex-shrink-0 bg-primary-900/30 px-2 py-1 rounded-lg">
                ₹{slot.cost_inr.toLocaleString('en-IN')}
              </span>
            )}
          </div>
          {slot.tip && (
            <div className="flex gap-2 items-start mt-2">
              <span className="text-yellow-400 text-xs flex-shrink-0 mt-0.5">💡</span>
              <p className="text-slate-400 text-xs leading-relaxed">{slot.tip}</p>
            </div>
          )}
          <div className="text-slate-600 text-xs mt-2">
            ⏱ {slot.duration_minutes} mins
          </div>
        </div>
      </div>
    </div>
  )
}

function DayCard({ day, isActive, onClick }) {
  return (
    <div
      onClick={onClick}
      className={`rounded-2xl border cursor-pointer transition-all duration-200 overflow-hidden ${
        isActive
          ? 'border-primary-500 bg-primary-900/20'
          : 'border-surface-600 bg-surface-800 hover:border-surface-500'
      }`}
    >
      {/* Day header */}
      <div className={`px-5 py-4 flex items-center justify-between ${
        isActive ? 'bg-primary-900/30' : ''
      }`}>
        <div>
          <div className="flex items-center gap-3">
            <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
              isActive ? 'bg-primary-500 text-white' : 'bg-surface-700 text-slate-400'
            }`}>
              Day {day.day}
            </span>
            <span className="text-white font-semibold text-sm">{day.city}</span>
          </div>
          <div className="text-slate-500 text-xs mt-1">{day.date} · {day.theme}</div>
        </div>
        <div className="text-slate-500 text-lg">
          {isActive ? '▲' : '▼'}
        </div>
      </div>

      {/* Expanded content */}
      {isActive && (
        <div className="px-5 pb-5 pt-2 space-y-0 animate-fade-in">
          <SlotCard slot={day.morning}   period="morning"   />
          <SlotCard slot={day.afternoon} period="afternoon" />
          <SlotCard slot={day.evening}   period="evening"   />

          {/* Footer */}
          <div className="flex items-center justify-between pt-3 border-t border-surface-600 mt-3">
            <div className="text-xs text-slate-500">
              🏨 {cleanText(day.accommodation)}
            </div>
            <div className="text-xs text-primary-400 font-medium">
              🍽 Food budget: ₹{day.daily_food_budget_inr?.toLocaleString('en-IN')}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function ItineraryTimeline({ itinerary, tripSummary }) {
  const [activeDay, setActiveDay] = useState(1)

  const feasibility = FEASIBILITY_CONFIG[tripSummary?.budget_feasibility] || FEASIBILITY_CONFIG.TIGHT

  return (
    <div className="space-y-4">

      {/* Trip Summary bar */}
      <div className="bg-surface-800 rounded-2xl p-5 border border-surface-600">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <div className="text-slate-400 text-xs mb-1">Route</div>
            <div className="text-white font-semibold text-sm">
              {tripSummary?.origin} → {tripSummary?.destinations?.join(' → ')}
            </div>
          </div>
          <div className="h-8 w-px bg-surface-600 hidden sm:block" />
          <div>
            <div className="text-slate-400 text-xs mb-1">Duration</div>
            <div className="text-white font-semibold text-sm">{tripSummary?.duration_days} days</div>
          </div>
          <div className="h-8 w-px bg-surface-600 hidden sm:block" />
          <div>
            <div className="text-slate-400 text-xs mb-1">Total Budget</div>
            <div className="text-white font-semibold text-sm">
              ₹{tripSummary?.total_budget_inr?.toLocaleString('en-IN')}
            </div>
          </div>
          <div className="h-8 w-px bg-surface-600 hidden sm:block" />
          <div>
            <div className="text-slate-400 text-xs mb-1">Best Season</div>
            <div className="text-white font-semibold text-sm">{tripSummary?.best_season}</div>
          </div>
          <div className={`ml-auto px-3 py-1.5 rounded-full text-xs font-bold border ${feasibility.color} ${feasibility.bg} ${feasibility.border}`}>
            {feasibility.label}
          </div>
        </div>
      </div>

      {/* Day selector pills */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {itinerary.map(day => (
          <button
            key={day.day}
            onClick={() => setActiveDay(day.day)}
            className={`flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-all border ${
              activeDay === day.day
                ? 'bg-primary-600 border-primary-500 text-white'
                : 'bg-surface-800 border-surface-600 text-slate-400 hover:border-slate-500'
            }`}
          >
            Day {day.day} · {day.city}
          </button>
        ))}
      </div>

      {/* Day cards */}
      <div className="space-y-3">
        {itinerary.map(day => (
          <DayCard
            key={day.day}
            day={day}
            isActive={activeDay === day.day}
            onClick={() => setActiveDay(activeDay === day.day ? null : day.day)}
          />
        ))}
      </div>

    </div>
  )
}