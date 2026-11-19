import React, { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import Icon from './Icon.jsx'
import AdminIA from './AdminIA.jsx'
import { AdminClientes, AdminDataset } from './AdminDatos.jsx'

const SECCIONES = [
  ['ia', 'spark', 'Inteligencia'],
  ['clientes', 'users', 'Clientes'],
  ['dataset', 'layers', 'Dataset'],
  ['reservas', 'ticket', 'Reservas'],
  ['canchas', 'pitch', 'Canchas'],
  ['franjas', 'clock', 'Franjas'],
]

export default function Admin() {
  const [seccion, setSeccion] = useState('ia')
  return (
    <section>
      <div className="page-head">
        <div>
          <span className="kicker">Centro de control</span>
          <h1 className="display h-lg" style={{ marginTop: 12 }}>Administración</h1>
          <p className="lead">Mira cómo se mueve el negocio, anticipa la demanda y gestiona canchas, franjas y reservas.</p>
        </div>
        <div className="seg">
          {SECCIONES.map(([id, ic, t]) => (
            <button key={id} className={seccion === id ? 'on' : ''} onClick={() => setSeccion(id)}><Icon name={ic} size={15} />{t}</button>
          ))}
        </div>
      </div>
      <div style={{ marginTop: 26 }}>
        {seccion === 'ia' && <AdminIA />}
        {seccion === 'clientes' && <AdminClientes />}
        {seccion === 'dataset' && <AdminDataset />}
        {seccion === 'reservas' && <AdminReservas />}
        {seccion === 'canchas' && <AdminCanchas />}
        {seccion === 'franjas' && <AdminFranjas />}
      </div>
    </section>
  )
}

function AdminReservas() {
  const [rs, setRs] = useState([])
  const [cargando, setCargando] = useState(true)
  const [q, setQ] = useState('')
  const [estado, setEstado] = useState('todas')
  const [limite, setLimite] = useState(50)

  async function cargar() { try { setRs(await api.adminReservas()) } catch {} finally { setCargando(false) } }
  useEffect(() => { cargar() }, [])
  async function cancelar(id) {
    if (!window.confirm('¿Cancelar esta reserva? El cupo quedará libre.')) return
    try { await api.adminCancelar(id) } catch {}
    cargar()
  }

  const filtradas = useMemo(() => {
    const t = q.trim().toLowerCase()
    return rs.filter(r => (estado === 'todas' || r.estado === estado) &&
      (!t || [r.cancha, r.nombre_contacto, r.correo_contacto, r.celular, r.fecha].some(v => String(v || '').toLowerCase().includes(t))))
  }, [rs, q, estado])

  return (
    <div className="card">
      <div className="card-h"><div><h3 className="h-sm">Todas las reservas</h3><p>{rs.length} registros · busca por nombre, correo, celular, cancha o fecha.</p></div></div>
      <div className="toolbar">
        <div className="input"><Icon name="search" size={17} /><input value={q} onChange={e => { setQ(e.target.value); setLimite(50) }} placeholder="Buscar…" /></div>
        <div className="seg">
          {['todas', 'confirmada', 'cancelada'].map(e => <button key={e} className={estado === e ? 'on' : ''} onClick={() => setEstado(e)}>{e === 'todas' ? 'Todas' : e + 's'}</button>)}
        </div>
      </div>
      {cargando ? <div className="skeleton" /> : !filtradas.length ? <div className="empty"><Icon name="search" size={30} />Sin resultados.</div> : (
        <>
          <div className="table-wrap"><table>
            <thead><tr><th>Cancha</th><th>Fecha</th><th>Hora</th><th>Estado</th><th>Contacto</th><th>Celular</th><th>Correo</th><th></th></tr></thead>
            <tbody>{filtradas.slice(0, limite).map(r => (
              <tr key={r.reserva_id}>
                <td><b>{r.cancha}</b></td><td>{r.fecha}</td><td>{r.hora_inicio}–{r.hora_fin}</td>
                <td><span className={'pill ' + (r.estado === 'confirmada' ? 'ok' : 'off')}>{r.estado}</span></td>
                <td>{r.nombre_contacto || '—'}</td>
                <td className="muted">{r.celular || '—'}</td>
                <td className="muted">{r.correo_contacto || '—'}</td>
                <td>{r.estado === 'confirmada' && <button className="btn danger" onClick={() => cancelar(r.reserva_id)}>Cancelar</button>}</td>
              </tr>))}</tbody>
          </table></div>
          {filtradas.length > limite && <div style={{ textAlign: 'center', marginTop: 16 }}><button className="btn line sm" onClick={() => setLimite(l => l + 100)}>Ver más ({filtradas.length - limite} restantes)</button></div>}
        </>
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
    <div className="card">
      <div className="card-h"><div><h3 className="h-sm">Canchas</h3><p>Agrega canchas o actívalas y desactívalas.</p></div></div>
      <details className="fold boxed">
        <summary><Icon name="plus" size={16} />Agregar cancha<Icon name="chevron" size={16} className="chev" /></summary>
        <div className="fold-body">
          <form className="row" onSubmit={agregar}>
            <div><label className="lbl-up">Nombre</label><input value={nombre} onChange={e => setNombre(e.target.value)} required minLength={2} placeholder="Cancha 4" /></div>
            <div><label className="lbl-up">Superficie</label><input value={sup} onChange={e => setSup(e.target.value)} /></div>
            <button className="btn"><Icon name="plus" size={16} />Agregar</button>
          </form>
          {msg && <div className={'toast ' + msg.t}>{msg.m}</div>}
        </div>
      </details>
      <div className="list">
        {cs.map(c => (
          <div className="li" key={c.cancha_id}>
            <span className="ic"><Icon name="pitch" size={20} /></span>
            <div className="grow"><b>{c.nombre}</b><span>{c.superficie || 'Sin especificar'}</span></div>
            <span className={'pill ' + (c.activa ? 'ok' : 'off')}>{c.activa ? 'activa' : 'inactiva'}</span>
            <button className="btn line sm" onClick={() => toggle(c.cancha_id)}>{c.activa ? 'Desactivar' : 'Activar'}</button>
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
    <div className="card">
      <div className="card-h"><div><h3 className="h-sm">Franjas horarias</h3><p>Define los turnos disponibles para reservar.</p></div></div>
      <details className="fold boxed">
        <summary><Icon name="plus" size={16} />Agregar franja<Icon name="chevron" size={16} className="chev" /></summary>
        <div className="fold-body">
          <form className="row" onSubmit={agregar}>
            <div><label className="lbl-up">Hora inicio</label><input type="time" value={ini} onChange={e => setIni(e.target.value)} required /></div>
            <div><label className="lbl-up">Hora fin</label><input type="time" value={fin} onChange={e => setFin(e.target.value)} required /></div>
            <button className="btn"><Icon name="plus" size={16} />Agregar</button>
          </form>
          {msg && <div className={'toast ' + msg.t}>{msg.m}</div>}
        </div>
      </details>
      <div className="list">
        {fs.map(f => (
          <div className="li" key={f.franja_id}>
            <span className="ic"><Icon name="clock" size={20} /></span>
            <div className="grow"><b>{f.hora_inicio} – {f.hora_fin}</b><span>Franja horaria</span></div>
            <span className={'pill ' + (f.activa ? 'ok' : 'off')}>{f.activa ? 'activa' : 'inactiva'}</span>
            <button className="btn line sm" onClick={() => toggle(f.franja_id)}>{f.activa ? 'Desactivar' : 'Activar'}</button>
          </div>
        ))}
      </div>
    </div>
  )
}
