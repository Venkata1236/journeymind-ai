import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import PlannerPage from './pages/PlannerPage.jsx'
import ItineraryPage from './pages/ItineraryPage.jsx'
import HistoryPage from './pages/HistoryPage.jsx'

function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-surface-900 border-b border-surface-600">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-label="JourneyMind AI">
            <circle cx="16" cy="16" r="15" stroke="#0ea5e9" strokeWidth="2" />
            <path
              d="M8 20 Q12 8 16 14 Q20 20 24 10"
              stroke="#0ea5e9"
              strokeWidth="2"
              strokeLinecap="round"
              fill="none"
            />
            <circle cx="24" cy="10" r="2.5" fill="#38bdf8" />
          </svg>

          <span className="text-white font-bold text-lg tracking-tight">
            Journey<span className="text-primary-400">Mind</span>
            <span className="text-primary-500 text-sm font-normal ml-1">AI</span>
          </span>
        </div>

        <div className="flex items-center gap-1">
          {[
            { to: '/', label: 'Plan Trip' },
            { to: '/itinerary', label: 'Itinerary' },
            { to: '/history', label: 'History' },
          ].map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-primary-600 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-surface-700'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-surface-900">
        <Navbar />
        <main className="pt-16">
          <Routes>
            <Route path="/" element={<PlannerPage />} />
            <Route path="/itinerary" element={<ItineraryPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}