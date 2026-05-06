import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'

const CATEGORY_CONFIG = {
  accommodation_inr:   { label: 'Accommodation', icon: '🏨', color: '#0ea5e9' },
  food_inr:            { label: 'Food',           icon: '🍽️', color: '#10b981' },
  transport_inr:       { label: 'Transport',      icon: '🚗', color: '#f59e0b' },
  activities_inr:      { label: 'Activities',     icon: '🎯', color: '#8b5cf6' },
  shopping_buffer_inr: { label: 'Shopping',       icon: '🛍️', color: '#ec4899' },
  contingency_inr:     { label: 'Contingency',    icon: '🛡️', color: '#64748b' },
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const { name, value } = payload[0]
  const pct = payload[0].payload.pct
  return (
    <div className="bg-surface-800 border border-surface-600 rounded-xl px-4 py-3 shadow-xl text-sm">
      <div className="text-white font-semibold">{name}</div>
      <div className="text-primary-400 font-bold">₹{value.toLocaleString('en-IN')}</div>
      <div className="text-slate-400">{pct}% of total</div>
    </div>
  )
}

const CustomLegend = ({ payload }) => (
  <div className="grid grid-cols-2 gap-2 mt-4">
    {payload.map((entry, i) => (
      <div key={i} className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: entry.color }} />
        <span className="text-slate-400 text-xs">{entry.value}</span>
      </div>
    ))}
  </div>
)

export default function BudgetBreakdown({ budget }) {
  if (!budget) return null

  const total = budget.total_inr

  const chartData = Object.entries(CATEGORY_CONFIG).map(([key, config]) => ({
    name:  config.label,
    value: budget[key] || 0,
    pct:   total ? Math.round(((budget[key] || 0) / total) * 100) : 0,
    color: config.color,
    icon:  config.icon,
  })).filter(d => d.value > 0)

  return (
    <div className="bg-surface-800 rounded-2xl border border-surface-600 p-6 space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-white font-bold text-lg">💰 Budget Breakdown</h3>
        <div className="text-right">
          <div className="text-slate-400 text-xs">Total Budget</div>
          <div className="text-primary-400 font-bold text-xl">
            ₹{total.toLocaleString('en-IN')}
          </div>
        </div>
      </div>

      {/* Donut chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={70}
              outerRadius={100}
              paddingAngle={3}
              dataKey="value"
            >
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.color} stroke="transparent" />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend content={<CustomLegend />} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Category rows */}
      <div className="space-y-3">
        {Object.entries(CATEGORY_CONFIG).map(([key, config]) => {
          const value = budget[key] || 0
          const pct   = total ? Math.round((value / total) * 100) : 0
          return (
            <div key={key}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="text-base">{config.icon}</span>
                  <span className="text-slate-300 text-sm">{config.label}</span>
                </div>
                <div className="text-right">
                  <span className="text-white text-sm font-semibold">
                    ₹{value.toLocaleString('en-IN')}
                  </span>
                  <span className="text-slate-500 text-xs ml-2">{pct}%</span>
                </div>
              </div>
              {/* Progress bar */}
              <div className="h-1.5 bg-surface-700 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{ width: `${pct}%`, background: config.color }}
                />
              </div>
            </div>
          )
        })}
      </div>

      {/* Per person per day */}
      <div className="bg-surface-700 rounded-xl p-4 flex items-center justify-between border border-surface-600">
        <div className="text-slate-400 text-sm">Per person / per day</div>
        <div className="text-primary-400 font-bold text-lg">
          ₹{Math.round(total / ((budget.group_size || 2) * (budget.duration_days || 5))).toLocaleString('en-IN')}
        </div>
      </div>

    </div>
  )
}