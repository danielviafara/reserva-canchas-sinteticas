import React, { useEffect, useState } from 'react'
import { api } from '../api'
import Icon from './Icon.jsx'

export default function Admin() {
  const [seccion, setSeccion] = useState('reservas')
  return (
    <section className="screen">
      <header className="screen-head">
        <span className="eyebrow"><Icon name="shield" size={15} />Panel de administración</span>
        <h1>Reservas y gestión</h1>
        <p className="lead">Consulta todas las reservas y administra las canchas y franjas del sistema.</p>
      </header>
      <div className="subtabs">
        <button className={'tab' + (seccion === 'reservas' ? ' active' : '')} onClick={() => setSeccion('reservas')}><Icon name="ticket" size={15} />Reservas</button>
        <button className={'tab' + (seccion === 'canchas' ? ' active' : '')} onClick={() => setSeccion('canchas')}><Icon name="pitch" size={15} />Canchas</button>
        <button className={'tab' + (seccion === 'franjas' ? ' active' : '')} onClick={() => setSeccion('franjas')}><Icon name="clock" size={15} />Franjas</button>
      </div>
      {seccion === 'reservas' && <AdminReservas />}
      {seccion === 'canchas' && <AdminCanchas />}
      {seccion === 'franjas' && <AdminFranjas />}
    </section>
  )
}

function AdminReservas() {
  const [rs, setRs] = useState([])
  const [cargando, setCargando] = useState(true)
  async function cargar() { try { setRs(await api.adminReservas()) } catch {} finally { setCargando(false) } }
  useEffect(() => { cargar() }, [])
  async function cancelar(id) {
    if (!window.confirm('¿Cancelar esta reserva? El cupo quedará libre.')) return
    try { await api.adminCancelar(id) } catch {}
    cargar()
  }
  return (
    <div className="panel">
      <h2 className="sec">Todas las reservas</h2>
      <p className="sub">El contacto de cada persona que reservó. Puedes cancelar cualquier reserva confirmada.</p>
      {cargando ? <div className="empty">Cargando…</div> :
        !rs.length ? <div className="empty">Aún no hay reservas.</div> : (
          <div className="tabla-wrap"><table className="tabla">
            <thead><tr><th>Cancha</th><th>Fecha</th><th>Hora</th><th>Estado</th><th>Nombre</th><th>Celular</th><th>Correo</th><th></th></tr></thead>
            <tbody>{rs.map(r => (
              <tr key={r.reserva_id}>
                <td>{r.cancha}</td><td>{r.fecha}</td><td>{r.hora_inicio}–{r.hora_fin}</td>
                <td><span className={'badge ' + r.estado}><Icon name={r.estado === 'confirmada' ? 'check' : 'x'} size={13} />{r.estado}</span></td>
                <td>{r.nombre_contacto || '—'}</td>
                <td><span className="cell-ico"><Icon name="phone" size={14} />{r.celular || '—'}</span></td>
                <td><span className="cell-ico"><Icon name="mail" size={14} />{r.correo_contacto || '—'}</span></td>
                <td>{r.estado === 'confirmada' &&
                  <button className="btn danger sm" onClick={() => cancelar(r.reserva_id)}><Icon name="x" size={14} />Cancelar</button>}</td>
              </tr>))}</tbody>
          </table></div>
        )}
    </div>
  )
}

function AdminCanchas() {
  const [cs, setCs] = useState([])
  const [nombre, setNombre] = useState('')
  const [sup, setSup] = useState('Césped sintético')
  const [msg, setMsg] = useState(null)
  async function cargar() { try { setCs(await api.adminCanchas()) } catch {} }
  useEffect(() => { cargar() }, [])
  async function agregar(e) {
    e.preventDefault()
    try { await api.crearCancha(nombre, sup); setNombre(''); setMsg({ t: 'ok', m: 'Cancha agregada.' }); cargar() }
    catch (ex) { setMsg({ t: 'err', m: ex.detail || 'No se pudo agregar.' }) }
  }
  async function toggle(id) { try { await api.toggleCancha(id); cargar() } catch {} }
  return (
    <div className="panel">
      <h2 className="sec">Canchas</h2>
      <p className="sub">Agrega canchas, o actívalas y desactívalas.</p>
      <form className="row" onSubmit={agregar}>
        <div><label>Nombre</label><input value={nombre} onChange={e => setNombre(e.target.value)} required minLength={2} placeholder="Cancha 4" /></div>
        <div><label>Superficie</label><input value={sup} onChange={e => setSup(e.target.value)} /></div>
        <button className="btn"><Icon name="plus" size={16} />Agregar cancha</button>
      </form>
      {msg && <div className={'msg ' + msg.t}>{msg.m}</div>}
      <div style={{ marginTop: 16 }}>
        {cs.map(c => (
          <div className="item" key={c.cancha_id}>
            <span className="ic"><Icon name="pitch" size={20} /></span>
            <div className="info"><div className="t">{c.nombre}</div><div className="d">{c.superficie || 'Sin especificar'}</div></div>
            <span className={'badge ' + (c.activa ? 'confirmada' : 'cancelada')}><Icon name={c.activa ? 'check' : 'x'} size={13} />{c.activa ? 'activa' : 'inactiva'}</span>
            <button className="btn ghost sm" onClick={() => toggle(c.cancha_id)}>{c.activa ? 'Desactivar' : 'Activar'}</button>
          </div>
        ))}
      </div>
    </div>
  )
}

function AdminFranjas() {
  const [fs, setFs] = useState([])
  const [ini, setIni] = useState('')
  const [fin, setFin] = useState('')
  const [msg, setMsg] = useState(null)
  async function cargar() { try { setFs(await api.adminFranjas()) } catch {} }
  useEffect(() => { cargar() }, [])
  async function agregar(e) {
    e.preventDefault()
    try { await api.crearFranja(ini, fin); setIni(''); setFin(''); setMsg({ t: 'ok', m: 'Franja agregada.' }); cargar() }
    catch (ex) { setMsg({ t: 'err', m: ex.detail || 'No se pudo agregar.' }) }
  }
  async function toggle(id) { try { await api.toggleFranja(id); cargar() } catch {} }
  return (
    <div className="panel">
      <h2 className="sec">Franjas horarias</h2>
      <p className="sub">Define los turnos disponibles para reservar.</p>
      <form className="row" onSubmit={agregar}>
        <div><label>Hora inicio</label><input type="time" value={ini} onChange={e => setIni(e.target.value)} required /></div>
        <div><label>Hora fin</label><input type="time" value={fin} onChange={e => setFin(e.target.value)} required /></div>
        <button className="btn"><Icon name="plus" size={16} />Agregar franja</button>
      </form>
      {msg && <div className={'msg ' + msg.t}>{msg.m}</div>}
      <div style={{ marginTop: 16 }}>
        {fs.map(f => (
          <div className="item" key={f.franja_id}>
            <span className="ic"><Icon name="clock" size={20} /></span>
            <div className="info"><div className="t">{f.hora_inicio} – {f.hora_fin}</div></div>
            <span className={'badge ' + (f.activa ? 'confirmada' : 'cancelada')}><Icon name={f.activa ? 'check' : 'x'} size={13} />{f.activa ? 'activa' : 'inactiva'}</span>
            <button className="btn ghost sm" onClick={() => toggle(f.franja_id)}>{f.activa ? 'Desactivar' : 'Activar'}</button>
          </div>
        ))}
      </div>
    </div>
  )
}
