const CONDITION_ICONS = {
  'hot':      '🌡️',
  'sunny':    '☀️',
  'pleasant': '🌤️',
  'humid':    '💧',
  'rainy':    '🌧️',
  'cold':     '❄️',
  'windy':    '💨',
  'breezy':   '🌬️',
  'warm':     '🌞',
  'dry':      '🏜️',
}

const RAIN_RISK_CONFIG = {
  Low:    { color: 'text-green-400',  bg: 'bg-green-900/30',  border: 'border-green-800',  bar: 'bg-green-500',  width: 'w-1/4' },
  Medium: { color: 'text-yellow-400', bg: 'bg-yellow-900/30', border: 'border-yellow-800', bar: 'bg-yellow-500', width: 'w-1/2' },
  High:   { color: 'text-red-400',    bg: 'bg-red-900/30',    border: 'border-red-800',    bar: 'bg-red-500',    width: 'w-3/4' },
}

function getConditionIcon(condition) {
  if (!condition) return '🌤️'
  const lower = condition.toLowerCase()
  for (const [key, icon] of Object.entries(CONDITION_ICONS)) {
    if (lower.includes(key)) return icon
  }
  return '🌤️'
}

function WeatherCard({ city, data }) {
  const rain   = RAIN_RISK_CONFIG[data.rain_risk] || RAIN_RISK_CONFIG.Low
  const icon   = getConditionIcon(data.condition)

  return (
    <div className="bg-surface-800 rounded-2xl border border-surface-600 p-5 hover:border-surface-500 transition">

      {/* City header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-white font-bold text-base">{city}</h3>
          <p className="text-slate-400 text-xs mt-0.5">{data.condition}</p>
        </div>
        <div className="text-4xl">{icon}</div>
      </div>

      {/* Temperature */}
      <div className="bg-surface-700 rounded-xl px-4 py-3 mb-4 flex items-center justify-between">
        <span className="text-slate-400 text-sm">Temperature</span>
        <span className="text-white font-bold text-lg">{data.temp}</span>
      </div>

      {/* Rain risk */}
      <div className={`rounded-xl px-4 py-3 mb-4 border ${rain.bg} ${rain.border}`}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-slate-400 text-sm">Rain Risk</span>
          <span className={`text-sm font-bold ${rain.color}`}>{data.rain_risk}</span>
        </div>
        <div className="h-1.5 bg-surface-600 rounded-full overflow-hidden">
          <div className={`h-full rounded-full ${rain.bar} ${rain.width} transition-all duration-700`} />
        </div>
      </div>

      {/* Tip */}
      {data.tip && (
        <div className="flex gap-2 items-start bg-surface-700 rounded-xl px-4 py-3">
          <span className="text-yellow-400 text-sm flex-shrink-0">💡</span>
          <p className="text-slate-300 text-xs leading-relaxed">{data.tip}</p>
        </div>
      )}
    </div>
  )
}

export default function WeatherWidget({ weatherInfo }) {
  if (!weatherInfo || Object.keys(weatherInfo).length === 0) return null

  const cities = Object.keys(weatherInfo)

  return (
    <div className="space-y-4">

      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-white font-bold text-lg">🌦️ Weather Guide</h3>
        <span className="text-slate-500 text-xs">At time of travel</span>
      </div>

      {/* Cards grid */}
      <div className={`grid gap-4 ${
        cities.length === 1 ? 'grid-cols-1' :
        cities.length === 2 ? 'grid-cols-1 sm:grid-cols-2' :
        'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
      }`}>
        {cities.map(city => (
          <WeatherCard
            key={city}
            city={city}
            data={weatherInfo[city]}
          />
        ))}
      </div>

      {/* Packing reminder */}
      <div className="bg-primary-900/20 border border-primary-800 rounded-xl px-5 py-4">
        <div className="flex gap-3 items-start">
          <span className="text-2xl flex-shrink-0">🎒</span>
          <div>
            <div className="text-primary-400 font-semibold text-sm mb-1">
              Packing Reminder
            </div>
            <p className="text-slate-400 text-xs leading-relaxed">
              Check the local tips tab for a full packing list tailored to your destinations and travel style.
            </p>
          </div>
        </div>
      </div>

    </div>
  )
}