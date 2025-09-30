import { useEffect, useMemo, useState } from 'react'
import './App.css'
import Overview from './pages/Overview'
import Suggestions from './pages/Suggestions'
import History from './pages/History'
import Settings from './pages/Settings'
import { ToastProvider } from './components/Toast'

type Route = 'overview' | 'suggestions' | 'history' | 'settings'

function getRouteFromHash(): Route {
  const h = window.location.hash.replace('#/', '')
  if (h === 'suggestions' || h === 'history' || h === 'settings') return h
  return 'overview'
}

export default function App() {
  const [route, setRoute] = useState<Route>(getRouteFromHash())
  useEffect(() => {
    const onHash = () => setRoute(getRouteFromHash())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])
  const links = useMemo(() => ([
    { href: '#/overview', key: 'overview', label: 'Overview' },
    { href: '#/suggestions', key: 'suggestions', label: 'Suggestions' },
    { href: '#/history', key: 'history', label: 'History' },
    { href: '#/settings', key: 'settings', label: 'Settings' },
  ] as const), [])

  return (
    <ToastProvider>
      <div style={{ padding: 24, fontFamily: 'Inter, system-ui, Arial, sans-serif' }}>
        <header style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 16, justifyContent: 'space-between' }}>
          <h2 style={{ margin: 0 }}>AI Crypto Wallet</h2>
          <nav style={{ display: 'flex', gap: 4, background: '#f3f4f6', padding: 4, borderRadius: 999 }}>
            {links.map(l => (
              <a
                key={l.key}
                href={l.href}
                style={{
                  padding: '6px 10px',
                  borderRadius: 999,
                  color: (route === l.key ? '#111827' : '#374151'),
                  background: (route === l.key ? '#ffffff' : 'transparent'),
                  textDecoration: 'none',
                  border: (route === l.key ? '1px solid #e5e7eb' : '1px solid transparent')
                }}
              >{l.label}</a>
            ))}
          </nav>
        </header>
        {route === 'overview' && <Overview />}
        {route === 'suggestions' && <Suggestions />}
        {route === 'history' && <History />}
        {route === 'settings' && <Settings />}
      </div>
    </ToastProvider>
  )
}
