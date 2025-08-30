import React, { useEffect, useState } from 'react'
import './App.css'
import Overview from './pages/Overview'
import Suggestions from './pages/Suggestions'
import History from './pages/History'
import Settings from './pages/Settings'

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

  return (
    <div style={{ padding: 24, fontFamily: 'Inter, system-ui, Arial, sans-serif' }}>
      <header style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>AI Crypto Wallet</h2>
        <nav style={{ display: 'flex', gap: 8 }}>
          <a href="#/overview">Overview</a>
          <a href="#/suggestions">Suggestions</a>
          <a href="#/history">History</a>
          <a href="#/settings">Settings</a>
        </nav>
      </header>
      {route === 'overview' && <Overview />}
      {route === 'suggestions' && <Suggestions />}
      {route === 'history' && <History />}
      {route === 'settings' && <Settings />}
    </div>
  )
}
