import React, { useEffect, useState } from 'react'
import { api } from '../api'

const hoy = () => new Date().toISOString().slice(0, 10)

export default function Disponibilidad() {
  const [canchas, setCanchas] = useState([])
  const [canchaId, setCanchaId] = useState('')
  const [fecha, setFecha] = useState(hoy())
  const [franjas, setFranjas] = useState([])
  const [msg, setMsg] = useState(null)
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    api.canchas().then(cs => { setCanchas(cs); if (cs[0]) setCanchaId(String(cs[0].cancha_id)) })
  }, [])

  async function cargar() {
    if (!canchaId) return
    setCargando(true); setMsg(null)
    try { setFranjas(await api.disponibilidad(canchaId, fecha)) }
    catch { setMsg({ t: 'err', m: 'No se pudo cargar la disponibilidad' }) }
    finally { setCargando(false) }
  }

  useEffect(() => { cargar() }, [canchaId, fecha])

  async function reservar(f) {
    const nombre = canchas.find(c => String(c.cancha_id) === String(canchaId))?.nombre
    if (!window.confirm(`¿Reservar ${nombre} el ${fecha} de ${f.hora_inicio} a ${f.hora_fin}?`)) return
    try {
      await api.reservar(Number(canchaId), f.franja_id, fecha)
      setMsg({ t: 'ok', m: 'Reserva confirmada. La puedes ver en "Mis reservas".' })
    } catch (ex) {
      // El servidor es la fuente de verdad: ante un 409 avisamos y re-sincronizamos.
      setMsg({ t: 'err', m: ex.status === 409 ? 'Esa franja acaba de ser tomada por otra persona.' : 'No se pudo reservar.' })
    }
    cargar()
  }

  return (
    <div className="panel">
      <h2>Consultar disponibilidad</h2>
      <p className="sub">Elige una cancha y una fecha. Las franjas en verde están libres.</p>
      <div className="row">
        <div>
          <label>Cancha</label>
          <select value={canchaId} onChange={e => setCanchaId(e.target.value)}>
            {canchas.map(c => <option key={c.cancha_id} value={c.cancha_id}>{c.nombre}</option>)}
          </select>
        </div>
        <div>
          <label>Fecha</label>
          <input type="date" value={fecha} min={hoy()} onChange={e => setFecha(e.target.value)} />
        </div>
      </div>

      {msg && <div className={'msg ' + msg.t}>{msg.m}</div>}

      {cargando ? <div className="empty">Cargando...</div> : (
        <div className="grid">
          {franjas.map(f => (
            <div key={f.franja_id}
                 className={'slot ' + f.estado}
                 onClick={() => f.estado === 'libre' && reservar(f)}>
              <div className="h">{f.hora_inicio} – {f.hora_fin}</div>
              <div className="s">{f.estado === 'libre' ? 'Libre · reservar' : 'Ocupada'}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
