import React, { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import Icon from './Icon.jsx'
import { DIAS, MESES, parse, yaPaso } from '../utils'

function faltan(r) {
  const ms = new Date(`${r.fecha}T${r.hora_inicio}`) - new Date()
  const h = Math.floor(ms / 36e5)
  if (h < 1) return 'En menos de una hora'
  if (h < 24) return `En ${h} h`
  const d = Math.round(h / 24)
  return `En ${d} día${d === 1 ? '' : 's'}`
}

export default function MisReservas({ irAReservar }) {
  const [reservas, setReservas] = useState([])
  const [cargando, setCargando] = useState(true)
  const [tab, setTab] = useState('proximas')
  const [err, setErr] = useState('')

  async function cargar() {
    setCargando(true)
    try { setReservas(await api.misReservas()) } catch { setErr('No se pudieron cargar tus reservas.') } finally { setCargando(false) }
  }
  useEffect(() => { cargar() }, [])

  async function cancelar(id) {
    if (!window.confirm('¿Cancelar esta reserva? El cupo quedará libre para otro jugador.')) return
    try { await api.cancelar(id) } catch {}
    cargar()
  }

  const { proximas, historial, stats } = useMemo(() => {
    const prox = reservas.filter(r => r.estado === 'confirmada' && !yaPaso(r.fecha, r.hora_fin))
      .sort((a, b) => (a.fecha + a.hora_inicio).localeCompare(b.fecha + b.hora_inicio))
    const hist = reservas.filter(r => !prox.includes(r))
      .sort((a, b) => (b.fecha + b.hora_inicio).localeCompare(a.fecha + a.hora_inicio))
    const jugados = hist.filter(r => r.estado === 'confirmada')
    const cuenta = {}
    jugados.forEach(r => { cuenta[r.cancha] = (cuenta[r.cancha] || 0) + 1 })
    const fav = Object.entries(cuenta).sort((a, b) => b[1] - a[1])[0]
    return { proximas: prox, historial: hist, stats: { jugados: jugados.length, canceladas: hist.length - jugados.length, fav: fav?.[0] } }
  }, [reservas])

  const lista = tab === 'proximas' ? proximas : historial

  return (
    <section>
      <div className="page-head">
        <div>
          <span className="kicker">Tu temporada</span>
          <h1 className="display h-lg" style={{ marginTop: 12 }}>Mis reservas</h1>
          <p className="lead">Tus próximos partidos y tu historial. Cancela con tiempo si no vas a llegar.</p>
        </div>
        <button className="btn glow" onClick={irAReservar}><Icon name="plus" size={17} />Nueva reserva</button>
      </div>

      <div className="kpis">
        <div className="kpi"><div className="k"><Icon name="calendar" size={15} />Próximos</div><div className="v">{proximas.length}</div><div className="s">{proximas[0] ? faltan(proximas[0]) : 'Sin partidos agendados'}</div></div>
        <div className="kpi"><div className="k"><Icon name="trophy" size={15} />Jugados</div><div className="v">{stats.jugados}</div><div className="s">{stats.jugados} hora{stats.jugados === 1 ? '' : 's'} en la cancha</div></div>
        <div className="kpi"><div className="k"><Icon name="pitch" size={15} />Cancha favorita</div><div className="v" style={{ fontSize: 32, marginTop: 16 }}>{stats.fav || '—'}</div><div className="s">Según tus partidos jugados</div></div>
      </div>

      <div style={{ marginTop: 34, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <div className="seg">
          <button className={tab === 'proximas' ? 'on' : ''} onClick={() => setTab('proximas')}>Próximas <span className="ct">{proximas.length}</span></button>
          <button className={tab === 'historial' ? 'on' : ''} onClick={() => setTab('historial')}>Historial <span className="ct">{historial.length}</span></button>
        </div>
      </div>

      {err && <div className="toast err"><Icon name="info" size={18} />{err}</div>}
      {cargando ? (
        <div className="bookings">{[0, 1].map(i => <div key={i} className="skeleton" style={{ minHeight: 90 }} />)}</div>
      ) : !lista.length ? (
        <div className="block"><div className="empty">
          <Icon name={tab === 'proximas' ? 'ball' : 'clock'} size={38} />
          {tab === 'proximas' ? 'No tienes partidos agendados. ¿Armamos uno?' : 'Aún no tienes historial.'}
          {tab === 'proximas' && <button className="btn sm" onClick={irAReservar}>Reservar cancha<Icon name="arrow" size={15} className="go" /></button>}
        </div></div>
      ) : (
        <div className="bookings">
          {lista.map((r, i) => {
            const d = parse(r.fecha)
            const etiqueta = r.estado === 'cancelada' ? 'cancelada' : yaPaso(r.fecha, r.hora_fin) ? 'jugada' : 'confirmada'
            return (
              <div key={r.reserva_id} className={'bk' + (tab === 'proximas' && i === 0 ? ' next' : '') + (etiqueta === 'cancelada' ? ' dim' : '')}>
                <div className="dt">
                  <div className="m">{MESES[d.getMonth()]}</div>
                  <div className="d">{d.getDate()}</div>
                  <div className="w">{DIAS[d.getDay()]}</div>
                </div>
                <div className="inf">
                  <div className="t">{r.cancha}</div>
                  <div className="s">
                    <span><Icon name="clock" size={14} />{r.hora_inicio} – {r.hora_fin}</span>
                    {etiqueta === 'confirmada' && <span><Icon name="stopwatch" size={14} />{faltan(r)}</span>}
                  </div>
                </div>
                <div className="act">
                  <span className={'pill ' + (etiqueta === 'confirmada' ? 'ok' : etiqueta === 'cancelada' ? 'off' : 'end')}>
                    <Icon name={etiqueta === 'confirmada' ? 'check' : etiqueta === 'cancelada' ? 'x' : 'trophy'} size={12} />{etiqueta}
                  </span>
                  {etiqueta === 'confirmada' && <button className="btn danger" onClick={() => cancelar(r.reserva_id)}>Cancelar</button>}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}
