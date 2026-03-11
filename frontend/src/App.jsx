import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend,
} from 'recharts'
import './App.css'

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

/* ───── helpers ───── */
const formColor = (f) => f >= 7 ? '#00ff87' : f >= 5 ? '#3b82f6' : f >= 3 ? '#f59e0b' : '#ef4444'
const fmtRank = (r) => !r ? '—' : r >= 1e6 ? `${(r/1e6).toFixed(1)}M` : r >= 1e3 ? `${(r/1e3).toFixed(0)}K` : r.toLocaleString()
const fallbackImg = (name) => `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=1a1f2e&color=94a3b8&size=88`

const CHIP_ICONS = { wildcard: '🃏', bboost: '📈', '3xc': '👑', freehit: '⚡' }

/* ───── PitchView ───── */
function PitchView({ players, onSelect }) {
  const starters = players.filter(p => p.multiplier > 0)
  const gk  = starters.filter(p => p.position === 'GKP')
  const def = starters.filter(p => p.position === 'DEF')
  const mid = starters.filter(p => p.position === 'MID')
  const fwd = starters.filter(p => p.position === 'FWD')

  const renderRow = (arr, cls) => (
    <div className={`pitch-row ${cls}`}>
      {arr.map(p => (
        <div className="pitch-player" key={p.id} onClick={() => onSelect(p)}>
          <div style={{ position: 'relative' }}>
            <img className={`pitch-player-img ${p.is_captain ? 'captain-ring' : ''}`}
              src={p.photo_url} alt={p.name}
              onError={e => { e.target.src = fallbackImg(p.name) }} />
            {p.is_captain && <span className="pitch-captain-icon c">C</span>}
            {p.is_vice_captain && <span className="pitch-captain-icon v">V</span>}
          </div>
          <span className="pitch-player-name">{p.name}</span>
          <span className="pitch-player-pts">{p.total_points} pts</span>
        </div>
      ))}
    </div>
  )

  return (
    <div className="pitch-container">
      <div className="pitch-lines">
        <div className="pitch-halfway" />
        <div className="pitch-center-circle" />
        <div className="pitch-box-top" />
        <div className="pitch-box-bottom" />
      </div>
      {renderRow(fwd, 'fwd')}
      {renderRow(mid, 'mid')}
      {renderRow(def, 'def')}
      {renderRow(gk,  'gk')}
    </div>
  )
}

/* ───── PlayerCard ───── */
function PlayerCard({ player, isBench, selected, onClick }) {
  const formPct = Math.min((player.form / 10) * 100, 100)
  const fc = formColor(player.form)
  const hasInjury = player.status === 'i' || player.status === 'u' || player.status === 's'
  const isDoubtful = player.status === 'd'
  const hasPriceUp = player.cost_change_event > 0
  const hasPriceDown = player.cost_change_event < 0
  const isPenTaker = player.penalties_order === 1
  const isCornerTaker = player.corners_order === 1
  const isFKTaker = player.freekicks_order === 1

  return (
    <div className={`player-card ${isBench ? 'bench-card' : ''} ${selected ? 'selected' : ''}`} onClick={onClick}>
      <div className="card-accent" style={{ background: player.team_color || '#333' }} />
      {player.is_captain && <div className="captain-badge captain">C</div>}
      {player.is_vice_captain && <div className="captain-badge vice">V</div>}

      <div className="player-card-top">
        <img className="player-photo" src={player.photo_url} alt={player.name}
          onError={e => { e.target.src = fallbackImg(player.name) }} />
        <div className="player-name-block">
          <div className="player-name">{player.name}</div>
          <div className="player-meta">
            <span className={`position-badge ${player.position}`}>{player.position}</span>
            <span>{player.team_short}</span>
            <span>£{(player.now_cost || player.cost || 0).toFixed(1)}m</span>
            {hasPriceUp && <span className="price-arrow up">▲</span>}
            {hasPriceDown && <span className="price-arrow down">▼</span>}
            {hasInjury && <span className="injury-badge injured">INJURED</span>}
            {isDoubtful && <span className="injury-badge doubtful">DOUBT</span>}
            {isPenTaker && <span className="setpiece-badge">PEN</span>}
            {isCornerTaker && <span className="setpiece-badge">COR</span>}
            {isFKTaker && <span className="setpiece-badge">FK</span>}
          </div>
        </div>
      </div>

      <div className="card-stats">
        <div className="card-stat"><div className="card-stat-value">{player.total_points}</div><div className="card-stat-label">Pts</div></div>
        <div className="card-stat"><div className="card-stat-value">{player.goals_scored}</div><div className="card-stat-label">Goals</div></div>
        <div className="card-stat"><div className="card-stat-value">{player.assists}</div><div className="card-stat-label">Assists</div></div>
      </div>

      <div className="form-bar-container">
        <div className="form-bar-label"><span>Form</span><strong style={{ color: fc }}>{player.form}</strong></div>
        <div className="form-bar-track"><div className="form-bar-fill" style={{ width: `${formPct}%`, background: fc }} /></div>
      </div>
    </div>
  )
}

/* ───── Fixture Calendar ───── */
function FixtureCalendar({ players, fixtureCalendar, currentGW }) {
  if (!fixtureCalendar || Object.keys(fixtureCalendar).length === 0) return null
  const gws = []
  for (let i = currentGW; i < currentGW + 5; i++) gws.push(i)

  const starters = players.filter(p => p.multiplier > 0)

  return (
    <div className="fixture-calendar">
      <table className="fixture-table">
        <thead>
          <tr>
            <th style={{ textAlign: 'left', minWidth: 140 }}>Player</th>
            {gws.map(gw => <th key={gw}>GW{gw}</th>)}
          </tr>
        </thead>
        <tbody>
          {starters.map(p => {
            const teamFx = fixtureCalendar[p.team_id] || []
            return (
              <tr key={p.id}>
                <td>
                  <div className="fixture-player-cell">
                    <img src={p.photo_url} alt={p.name} onError={e => { e.target.src = fallbackImg(p.name) }} />
                    <div><div className="fname">{p.name}</div><div className="fpos">{p.position}</div></div>
                  </div>
                </td>
                {gws.map(gw => {
                  const fx = teamFx.find(f => f.gw === gw)
                  if (!fx) return <td key={gw}>-</td>
                  return (
                    <td key={gw}>
                      <span className={`fdr-chip fdr-${fx.difficulty}`}>
                        {fx.opponent}{fx.is_home ? '(H)' : '(A)'}
                      </span>
                    </td>
                  )
                })}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

/* ───── Points History Chart ───── */
function PointsChart({ history }) {
  if (!history || history.length === 0) return null
  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={history}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="gw" stroke="#64748b" fontSize={11} tickFormatter={v => `GW${v}`} />
          <YAxis stroke="#64748b" fontSize={11} />
          <Tooltip
            contentStyle={{ background: '#1a1f2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
            labelFormatter={v => `Gameweek ${v}`}
          />
          <Line type="monotone" dataKey="points" stroke="#00ff87" strokeWidth={2} dot={{ r: 3 }} name="GW Points" />
          <Line type="monotone" dataKey="bench_points" stroke="#f59e0b" strokeWidth={1.5} dot={false} name="Bench Pts" strokeDasharray="4 4" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

/* ───── Comparison Modal ───── */
function ComparisonModal({ p1, p2, onClose }) {
  if (!p1 || !p2) return null

  const stats = [
    { key: 'total_points', label: 'Points' },
    { key: 'form', label: 'Form' },
    { key: 'goals_scored', label: 'Goals' },
    { key: 'assists', label: 'Assists' },
    { key: 'xG', label: 'xG' },
    { key: 'xA', label: 'xA' },
    { key: 'ict_index', label: 'ICT' },
    { key: 'minutes', label: 'Minutes' },
    { key: 'clean_sheets', label: 'CS' },
    { key: 'selected_by_percent', label: 'Own%' },
  ]

  // For radar chart
  const radarData = [
    { stat: 'Form', A: p1.form, B: p2.form, max: 10 },
    { stat: 'xG', A: p1.xG, B: p2.xG, max: Math.max(p1.xG, p2.xG, 1) },
    { stat: 'xA', A: p1.xA, B: p2.xA, max: Math.max(p1.xA, p2.xA, 1) },
    { stat: 'Threat', A: p1.threat / 10, B: p2.threat / 10, max: Math.max(p1.threat, p2.threat, 10) / 10 },
    { stat: 'Creativity', A: p1.creativity / 10, B: p2.creativity / 10, max: Math.max(p1.creativity, p2.creativity, 10) / 10 },
    { stat: 'Influence', A: p1.influence / 10, B: p2.influence / 10, max: Math.max(p1.influence, p2.influence, 10) / 10 },
  ]

  return (
    <div className="comparison-overlay" onClick={onClose}>
      <div className="comparison-modal" onClick={e => e.stopPropagation()}>
        <div className="comparison-header">
          <h3>Player Comparison</h3>
          <button className="comparison-close" onClick={onClose}>✕</button>
        </div>

        <div className="comparison-players">
          <div className="comp-player-card">
            <img src={p1.photo_url} alt={p1.name} onError={e => { e.target.src = fallbackImg(p1.name) }} />
            <div className="comp-name">{p1.name}</div>
            <div className="comp-team">{p1.team_name} · {p1.position}</div>
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 900, color: '#64748b', alignSelf: 'center' }}>VS</div>
          <div className="comp-player-card">
            <img src={p2.photo_url} alt={p2.name} onError={e => { e.target.src = fallbackImg(p2.name) }} />
            <div className="comp-name">{p2.name}</div>
            <div className="comp-team">{p2.team_name} · {p2.position}</div>
          </div>
        </div>

        {/* Radar Chart */}
        <div style={{ marginBottom: '1.5rem' }}>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(255,255,255,0.1)" />
              <PolarAngleAxis dataKey="stat" stroke="#94a3b8" fontSize={11} />
              <Radar name={p1.name} dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
              <Radar name={p2.name} dataKey="B" stroke="#bd00ff" fill="#bd00ff" fillOpacity={0.2} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Bar comparison */}
        <div className="comp-stats">
          {stats.map(({ key, label }) => {
            const v1 = Number(p1[key]) || 0
            const v2 = Number(p2[key]) || 0
            const max = Math.max(v1, v2, 1)
            return (
              <div className="comp-stat-row" key={key}>
                <span className="comp-val left" style={{ color: v1 >= v2 ? '#3b82f6' : '#64748b' }}>{key === 'selected_by_percent' ? `${v1}%` : v1}</span>
                <div className="comp-bar-container">
                  <div className="comp-bar-left">
                    <div className="comp-bar bar-1" style={{ width: `${(v1/max)*100}%` }} />
                  </div>
                  <span className="comp-stat-label">{label}</span>
                  <div className="comp-bar-right">
                    <div className="comp-bar bar-2" style={{ width: `${(v2/max)*100}%` }} />
                  </div>
                </div>
                <span className="comp-val right" style={{ color: v2 >= v1 ? '#bd00ff' : '#64748b' }}>{key === 'selected_by_percent' ? `${v2}%` : v2}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════
   MAIN APP
   ═══════════════════════════════════════════ */
function App() {
  const [teamId, setTeamId] = useState('')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [theme, setTheme] = useState('dark')
  const [selected, setSelected] = useState([])   // for comparison

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark')

  const handleSelect = (player) => {
    setSelected(prev => {
      const exists = prev.find(p => p.id === player.id)
      if (exists) return prev.filter(p => p.id !== player.id)
      if (prev.length >= 2) return [prev[1], player]
      return [...prev, player]
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!teamId) return
    setLoading(true); setError(null); setData(null); setSelected([])
    try {
      const res = await fetch(`${API}/api/analyze`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ team_id: parseInt(teamId) }),
      })
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const json = await res.json()
      if (json.error) setError(json.error); else setData(json)
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  const allPlayers = data ? [...(data.starting_xi || []), ...(data.bench || [])] : []

  return (
    <>
      {/* ── Navbar ── */}
      <nav className="navbar">
        <div className="container">
          <div className="nav-brand">
            <div className="nav-logo">⚽</div>
            <span className="nav-title">FPL AI Copilot</span>
          </div>
          <div className="nav-right">
            <div className="nav-badge">AI Agents</div>
            <button className="theme-toggle" onClick={toggleTheme} title="Toggle theme">
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      {!data && !loading && (
        <section className="hero">
          <div className="container">
            <h1><span className="text-gradient">Gameweek Intelligence</span></h1>
            <p>Enter your FPL Manager ID. Our multi-agent pipeline analyzes fixtures, form, and budget to deliver captain and transfer recommendations.</p>
            <form className="search-box" onSubmit={handleSubmit}>
              <input type="number" placeholder="Manager ID, e.g. 123456" value={teamId}
                onChange={e => setTeamId(e.target.value)} required />
              <button className="btn-primary" type="submit">Analyze</button>
            </form>
          </div>
        </section>
      )}

      {loading && (
        <div className="loading-overlay">
          <div className="spinner" />
          <p className="loading-text">Running multi-agent pipeline... analyzing fixtures, form & budgets.</p>
        </div>
      )}

      {error && !loading && (
        <div className="container"><div className="error-banner"><span>⚠️</span><p>{error}</p></div></div>
      )}

      {/* ═══ DASHBOARD ═══ */}
      {data && !loading && (
        <div className="container" style={{ paddingTop: '1.5rem' }}>

          {/* Manager Header */}
          <div className="manager-header animate-in">
            <div className="manager-info">
              <h2>{data.manager_name}</h2>
              <span className="team-name">{data.team_name}</span>
            </div>
            <div className="manager-stats">
              <div className="stat-block"><div className="stat-value">{data.gameweek}</div><div className="stat-label">Gameweek</div></div>
              <div className="stat-block"><div className="stat-value green">{data.overall_points?.toLocaleString()}</div><div className="stat-label">Total Points</div></div>
              <div className="stat-block"><div className="stat-value">{fmtRank(data.overall_rank)}</div><div className="stat-label">Rank</div></div>
              <div className="stat-block"><div className="stat-value green">£{data.bank_balance}m</div><div className="stat-label">Bank</div></div>
            </div>
          </div>

          {/* ── Pitch Formation ── */}
          <div className="section animate-in delay-1">
            <div className="section-header"><div className="section-icon green">⚡</div><h3>Formation View</h3></div>
            <PitchView players={allPlayers} onSelect={handleSelect} />
          </div>

          {/* ── Starting XI Cards ── */}
          <div className="section animate-in delay-1">
            <div className="section-header"><div className="section-icon green">👥</div><h3>Starting XI — click any 2 players to compare</h3></div>
            <div className="player-grid">
              {data.starting_xi?.map(p => (
                <PlayerCard key={p.id} player={p} selected={selected.some(s => s.id === p.id)} onClick={() => handleSelect(p)} />
              ))}
            </div>
          </div>

          {/* ── Bench ── */}
          {data.bench?.length > 0 && (
            <div className="section animate-in delay-2">
              <div className="section-header"><div className="section-icon blue">🪑</div><h3>Bench</h3></div>
              <div className="player-grid">
                {data.bench.map(p => (
                  <PlayerCard key={p.id} player={p} isBench selected={selected.some(s => s.id === p.id)} onClick={() => handleSelect(p)} />
                ))}
              </div>
            </div>
          )}

          {/* ── Fixture Difficulty Calendar ── */}
          <div className="section animate-in delay-2">
            <div className="section-header"><div className="section-icon amber">📅</div><h3>Fixture Difficulty Rating</h3></div>
            <div className="analysis-panel" style={{ padding: '0.5rem' }}>
              <FixtureCalendar players={allPlayers} fixtureCalendar={data.fixture_calendar} currentGW={data.gameweek} />
            </div>
          </div>

          {/* ── Captain Recommendation ── */}
          {data.captain_analysis && (
            <div className="section animate-in delay-3">
              <div className="section-header"><div className="section-icon green">🎯</div><h3>Captain Recommendation</h3></div>
              <div className="analysis-panel">
                <h4>AI Agent Analysis</h4>
                <div className="analysis-content"><ReactMarkdown>{data.captain_analysis}</ReactMarkdown></div>
              </div>
            </div>
          )}

          {/* ── Transfer Strategy ── */}
          {data.transfer_analysis && (
            <div className="section animate-in delay-3">
              <div className="section-header"><div className="section-icon purple">🔄</div><h3>Transfer Strategy</h3></div>
              <div className="analysis-panel">
                <h4>AI Agent Analysis</h4>
                <div className="analysis-content"><ReactMarkdown>{data.transfer_analysis}</ReactMarkdown></div>
              </div>
            </div>
          )}

          {/* ── Chips Status ── */}
          {data.chips_status && (
            <div className="section animate-in delay-3">
              <div className="section-header"><div className="section-icon cyan">🎲</div><h3>Chip Strategy</h3></div>
              <div className="chips-row">
                {data.chips_status.map(c => (
                  <div key={c.key} className={`chip-card ${c.used ? 'used' : 'available'}`}>
                    <div className="chip-icon">{CHIP_ICONS[c.key]}</div>
                    <div className="chip-label">{c.label}</div>
                    <div className={`chip-status ${c.used ? 'spent' : 'avail'}`}>{c.used ? 'Used' : 'Available'}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Top Transfer Targets ── */}
          {data.top_targets?.length > 0 && (
            <div className="section animate-in delay-4">
              <div className="section-header"><div className="section-icon blue">📊</div><h3>Top Transfer Targets</h3></div>
              <div className="analysis-panel" style={{ padding: '0.5rem' }}>
                <div style={{ overflowX: 'auto' }}>
                  <table className="targets-table">
                    <thead>
                      <tr>
                        <th>Player</th><th>Pos</th><th>Cost</th><th>Form</th><th>Pts</th><th>Goals</th><th>Assists</th><th>xG</th><th>Own%</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.top_targets.map(t => (
                        <tr key={t.id} onClick={() => handleSelect(t)} style={{ cursor: 'pointer' }}>
                          <td>
                            <div className="target-player-cell">
                              <img className="target-photo" src={t.photo_url} alt={t.name} onError={e => { e.target.src = fallbackImg(t.name) }} />
                              <div><div className="target-name">{t.name}</div><div className="target-team">{t.team_name}</div></div>
                            </div>
                          </td>
                          <td><span className={`position-badge ${t.position}`}>{t.position}</span></td>
                          <td>£{(t.now_cost || t.cost || 0).toFixed(1)}m</td>
                          <td style={{ color: formColor(t.form), fontWeight: 700 }}>{t.form}</td>
                          <td style={{ fontWeight: 600 }}>{t.total_points}</td>
                          <td>{t.goals_scored}</td>
                          <td>{t.assists}</td>
                          <td>{t.xG}</td>
                          <td>{(t.selected_by_percent || t.ownership || 0)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ── Differentials ── */}
          {data.differentials?.length > 0 && (
            <div className="section animate-in delay-4">
              <div className="section-header"><div className="section-icon purple">💎</div><h3>Hidden Gems — Low Ownership Differentials</h3></div>
              <div className="diff-grid">
                {data.differentials.map(d => (
                  <div className="diff-card" key={d.id} onClick={() => handleSelect(d)} style={{ cursor: 'pointer' }}>
                    <img className="diff-photo" src={d.photo_url} alt={d.name} onError={e => { e.target.src = fallbackImg(d.name) }} />
                    <div className="diff-info">
                      <div className="diff-name">{d.name}</div>
                      <div className="diff-meta">{d.team_short} · {d.position} · £{(d.now_cost || d.cost || 0).toFixed(1)}m</div>
                      <div className="diff-stats">
                        <span className="diff-stat form">Form {d.form}</span>
                        <span className="diff-stat own">{(d.selected_by_percent || d.ownership || 0)}% owned</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Points History ── */}
          {data.manager_history?.length > 0 && (
            <div className="section animate-in delay-5">
              <div className="section-header"><div className="section-icon green">📈</div><h3>Gameweek Points History</h3></div>
              <PointsChart history={data.manager_history} />
            </div>
          )}

          {/* New search */}
          <div style={{ textAlign: 'center', margin: '1.5rem 0' }}>
            <form className="search-box" onSubmit={handleSubmit} style={{ maxWidth: 400, margin: '0 auto' }}>
              <input type="number" placeholder="Try another Manager ID" value={teamId} onChange={e => setTeamId(e.target.value)} required />
              <button className="btn-primary" type="submit">Analyze</button>
            </form>
          </div>
        </div>
      )}

      {/* ── Comparison Modal ── */}
      {selected.length === 2 && (
        <ComparisonModal p1={selected[0]} p2={selected[1]} onClose={() => setSelected([])} />
      )}

      <footer className="footer">
        <p>FPL AI Copilot — FastAPI · LangGraph · Groq · React · Recharts</p>
      </footer>
    </>
  )
}

export default App
