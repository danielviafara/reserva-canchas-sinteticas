import React, { useEffect, useState } from 'react'
import { api } from '../api'
import Icon from './Icon.jsx'

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
  const [seleccion, setSeleccion] = useState(null)
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
    await cargar()
    setMsg(resultado)
  }

  const nombreCancha = canchas.find(c => String(c.cancha_id) === String(canchaId))?.nombre

  return (
    <section className="screen">
      <header className="screen-head">
        <span className="eyebrow"><Icon name="bolt" size={15} />Reserva tu turno</span>
        <h1>Encuentra una cancha <span className="hl">libre</span> bajo las luces</h1>
        <p className="lead">Elige una cancha y una fecha. Las franjas en verde están disponibles para reservar al instante.</p>
      </header>

      <div className="controls">
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

      {msg && <div className={'msg ' + msg.t} style={{ marginTop: 14 }}>{msg.m}</div>}

      {cargando ? <div className="empty">Cargando disponibilidad…</div> : (
        <div className="board">
          {franjas.map(f => (
            <button key={f.franja_id}
              className={'slot ' + (f.estado === 'libre' ? 'free' : 'taken')}
              onClick={() => f.estado === 'libre' && abrirFormulario(f)}>
              <span className="st"><Icon name={f.estado === 'libre' ? 'check' : 'x'} size={14} />{f.estado === 'libre' ? 'Disponible' : 'Reservada'}</span>
              <span className="time">{f.hora_inicio} <i>– {f.hora_fin}</i></span>
            </button>
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
                <Icon name="check" size={16} />{enviando ? 'Reservando…' : 'Confirmar reserva'}
              </button>
              <button className="btn ghost" type="button" onClick={() => setSeleccion(null)} disabled={enviando}>Cancelar</button>
            </div>
          </form>
        </div>
      )}
    </section>
  )
}
