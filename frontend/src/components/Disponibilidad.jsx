import React, { useEffect, useState } from 'react'
import { api } from '../api'

const hoy = () => new Date().toISOString().slice(0, 10)

function usuarioGuardado() {
  try { return JSON.parse(localStorage.getItem('goltime_user')) || {} } catch { return {} }
}

export default function Disponibilidad() {
  const [canchas, setCanchas] = useState([])
  const [canchaId, setCanchaId] = useState('')
  const [fecha, setFecha] = useState(hoy())
  const [franjas, setFranjas] = useState([])
  const [msg, setMsg] = useState(null)
  const [cargando, setCargando] = useState(false)
  const [seleccion, setSeleccion] = useState(null)   // franja elegida para reservar
  const [datos, setDatos] = useState({ nombre_contacto: '', celular: '', correo_contacto: '' })
  const [enviando, setEnviando] = useState(false)

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

  function abrirFormulario(f) {
    const u = usuarioGuardado()
    setDatos({ nombre_contacto: u.nombre || '', celular: '', correo_contacto: u.email || '' })
    setSeleccion(f); setMsg(null)
  }

  async function confirmarReserva(e) {
    e.preventDefault()
    setEnviando(true)
    let resultado
    try {
      await api.reservar(Number(canchaId), seleccion.franja_id, fecha, datos)
      resultado = { t: 'ok', m: 'Reserva confirmada. La puedes ver en "Mis reservas".' }
    } catch (ex) {
      resultado = { t: 'err', m: ex.status === 409 ? 'Esa franja acaba de ser tomada por otra persona.' : 'No se pudo reservar. Revisa los datos.' }
    }
    setSeleccion(null)
    setEnviando(false)
    await cargar()        // refresca la grilla (cargar() limpia el mensaje)
    setMsg(resultado)     // mostramos el resultado DESPUES de refrescar, para que no se borre
  }

  const nombreCancha = canchas.find(c => String(c.cancha_id) === String(canchaId))?.nombre

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
                 onClick={() => f.estado === 'libre' && abrirFormulario(f)}>
              <div className="h">{f.hora_inicio} – {f.hora_fin}</div>
              <div className="s">{f.estado === 'libre' ? 'Libre · reservar' : 'Ocupada'}</div>
            </div>
          ))}
        </div>
      )}

      {seleccion && (
        <div className="modal-fondo" onClick={() => !enviando && setSeleccion(null)}>
          <form className="modal panel" onClick={e => e.stopPropagation()} onSubmit={confirmarReserva}>
            <h2>Datos de la reserva</h2>
            <p className="sub">{nombreCancha} · {fecha} · {seleccion.hora_inicio} a {seleccion.hora_fin}</p>
            <div className="reco">
              <div className="reco-t">Antes de reservar, ten en cuenta:</div>
              <ul>
                <li>Llega al menos 15 minutos antes de tu franja.</li>
                <li>La franja dura una hora; respeta el horario para no afectar la siguiente reserva.</li>
                <li>Si no vas a asistir, cancela a tiempo para liberar el cupo.</li>
                <li>Lleva calzado adecuado para césped sintético.</li>
              </ul>
            </div>
            <div className="field">
              <label>Nombre completo</label>
              <input value={datos.nombre_contacto} required minLength={3}
                     onChange={e => setDatos({ ...datos, nombre_contacto: e.target.value })} />
            </div>
            <div className="field">
              <label>Número de celular</label>
              <input value={datos.celular} required minLength={7} inputMode="tel" placeholder="3001234567"
                     onChange={e => setDatos({ ...datos, celular: e.target.value })} />
            </div>
            <div className="field">
              <label>Correo electrónico</label>
              <input type="email" value={datos.correo_contacto} required
                     onChange={e => setDatos({ ...datos, correo_contacto: e.target.value })} />
            </div>
            <div className="row" style={{ marginTop: 10 }}>
              <button className="btn" type="submit" disabled={enviando}>
                {enviando ? 'Reservando...' : 'Confirmar reserva'}
              </button>
              <button className="btn ghost" type="button" onClick={() => setSeleccion(null)} disabled={enviando}>Cancelar</button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
