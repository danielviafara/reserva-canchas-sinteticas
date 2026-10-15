import React, { useEffect, useState } from 'react'
import { api } from '../api'

export default function MisReservas() {
  const [reservas, setReservas] = useState([])
  const [cargando, setCargando] = useState(true)

  async function cargar() {
    setCargando(true)
    try { setReservas(await api.misReservas()) } finally { setCargando(false) }
  }
  useEffect(() => { cargar() }, [])

  async function cancelar(id) {
    if (!window.confirm('¿Cancelar esta reserva? El cupo quedará libre.')) return
    try { await api.cancelar(id) } catch {}
    cargar()
  }

  if (cargando) return <div className="panel"><div className="empty">Cargando...</div></div>

  return (
    <div className="panel">
      <h2>Mis reservas</h2>
      <p className="sub">Aquí ves tus reservas y puedes cancelarlas para liberar el cupo.</p>
      {reservas.length === 0 && <div className="empty">Todavía no tienes reservas.</div>}
      {reservas.map(r => (
        <div className="item" key={r.reserva_id}>
          <div className="info">
            <div className="t">{r.cancha} · {r.hora_inicio} – {r.hora_fin}</div>
            <div className="d">{r.fecha}</div>
          </div>
          <span className={'badge ' + r.estado}>{r.estado}</span>
          {r.estado === 'confirmada' &&
            <button className="btn danger sm" onClick={() => cancelar(r.reserva_id)}>Cancelar</button>}
        </div>
      ))}
    </div>
  )
}
