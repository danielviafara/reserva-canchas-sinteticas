import React, { useEffect, useState } from 'react'
import { api } from '../api'
import Icon from './Icon.jsx'

const yaPaso = (r) => new Date(`${r.fecha}T${r.hora_fin}`) < new Date()

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

  return (
    <section className="screen">
      <header className="screen-head">
        <span className="eyebrow"><Icon name="ticket" size={15} />Tu actividad</span>
        <h1>Mis reservas</h1>
        <p className="lead">Tus turnos reservados. Puedes cancelar los que aún no han pasado para liberar el cupo.</p>
      </header>
      {cargando && <div className="empty">Cargando…</div>}
      {!cargando && reservas.length === 0 &&
        <div className="empty">Todavía no tienes reservas. Reserva tu primer turno desde Disponibilidad.</div>}
      {reservas.map(r => {
        const finalizada = r.estado === 'confirmada' && yaPaso(r)
        const activa = r.estado === 'confirmada' && !finalizada
        const etiqueta = r.estado === 'cancelada' ? 'cancelada' : (finalizada ? 'finalizada' : 'confirmada')
        return (
          <div className="item" key={r.reserva_id}>
            <span className="ic">{r.hora_inicio.slice(0, 2)}</span>
            <div className="info">
              <div className="t">{r.cancha}</div>
              <div className="d">{r.fecha}, de {r.hora_inicio} a {r.hora_fin}</div>
            </div>
            <span className={'badge ' + etiqueta}><Icon name={etiqueta === 'confirmada' ? 'check' : etiqueta === 'finalizada' ? 'clock' : 'x'} size={13} />{etiqueta}</span>
            {activa && <button className="btn danger sm" onClick={() => cancelar(r.reserva_id)}><Icon name="x" size={14} />Cancelar</button>}
          </div>
        )
      })}
    </section>
  )
}
