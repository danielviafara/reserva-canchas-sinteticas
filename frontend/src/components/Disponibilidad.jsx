import React, { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api'
import Icon from './Icon.jsx'
import Silueta from './Silueta.jsx'
import { DIAS, MESES, NIVEL, hoy, iso, parse, pct, proximosDias, yaPaso, fechaLarga } from '../utils'

const REGLAS = [
  ['stopwatch', 'Llega 15 minutos antes de tu franja para calentar y no perder minutos.'],
  ['clock', 'Cada franja dura una hora: respeta el horario de la siguiente reserva.'],
  ['x', 'Si no vas a asistir, cancela a tiempo para liberar el cupo.'],
  ['boot', 'Usa guayos de césped sintético (multitaco o turf). Nada de tacos de aluminio.'],
]

export default function Disponibilidad({ usuario, irAMis, sugerencia, limpiarSugerencia }) {
  const [canchas, setCanchas] = useState([])
  const [canchaId, setCanchaId] = useState('')
  const [fecha, setFecha] = useState(hoy())
  const [franjas, setFranjas] = useState([])
  const [demanda, setDemanda] = useState({})
  const [sugerencias, setSugerencias] = useState(null)
  const [msg, setMsg] = useState(null)
  const [cargando, setCargando] = useState(false)
  const [seleccion, setSeleccion] = useState(null)
  const [datos, setDatos] = useState({ nombre_contacto: '', celular: '', correo_contacto: '' })
  const [enviando, setEnviando] = useState(false)
  const horarioRef = useRef(null)
  const dias = useMemo(() => proximosDias(14), [])

  useEffect(() => {
    api.canchas().then(cs => { setCanchas(cs); if (cs[0]) setCanchaId(String(cs[0].cancha_id)) })
      .catch(() => setMsg({ t: 'err', m: 'No hay conexión con el servidor.' }))
    cargarSugerencias()
  }, [])

  // Si se llego desde "Mi juego" con una sugerencia, abrir directamente esa franja.
  useEffect(() => {
    if (sugerencia && canchas.length) { usarSugerencia(sugerencia); limpiarSugerencia?.() }
  }, [sugerencia, canchas])

  function cargarSugerencias() { api.recomendaciones().then(setSugerencias).catch(() => setSugerencias({ items: [] })) }

  async function cargar() {
    if (!canchaId) return
    setCargando(true)
    try {
      const [fs, dem] = await Promise.all([
        api.disponibilidad(canchaId, fecha),
        api.demanda(canchaId, fecha).catch(() => []),
      ])
      setFranjas(fs)
      setDemanda(Object.fromEntries(dem.map(d => [d.franja_id, d])))
    } catch { setMsg({ t: 'err', m: 'No se pudo cargar la disponibilidad.' }) }
    finally { setCargando(false) }
  }
  useEffect(() => { cargar() }, [canchaId, fecha])

  function abrir(f, cancha = canchaId, dia = fecha) {
    const u = usuario || {}
    setDatos(d => ({ nombre_contacto: d.nombre_contacto || u.nombre || '', celular: d.celular, correo_contacto: d.correo_contacto || u.email || '' }))
    setSeleccion({ ...f, cancha_id: Number(cancha), fecha: dia }); setMsg(null)
  }

  function usarSugerencia(s) {
    setCanchaId(String(s.cancha_id)); setFecha(s.fecha)
    abrir({ franja_id: s.franja_id, hora_inicio: s.hora_inicio, hora_fin: s.hora_fin }, s.cancha_id, s.fecha)
  }

  async function confirmar(e) {
    e.preventDefault()
    setEnviando(true)
    let r
    try {
      await api.reservar(seleccion.cancha_id, seleccion.franja_id, seleccion.fecha, datos)
      r = { t: 'ok', m: `¡Listo! ${nombreDe(seleccion.cancha_id)}, ${fechaLarga(seleccion.fecha)} a las ${seleccion.hora_inicio}. Nos vemos en la cancha.` }
    } catch (ex) {
      r = { t: 'err', m: ex.status === 409 ? 'Alguien se te adelantó: esa franja acaba de ser tomada. Elige otra.' : (ex.status === 401 ? 'Tu sesión expiró. Vuelve a iniciar sesión.' : 'No se pudo reservar. Revisa los datos.') }
    }
    setSeleccion(null); setEnviando(false)
    await cargar(); cargarSugerencias()
    setMsg(r)
  }

  const nombreDe = (id) => canchas.find(c => String(c.cancha_id) === String(id))?.nombre || ''
  const libres = franjas.filter(f => f.estado === 'libre' && !yaPaso(fecha, f.hora_inicio)).length
  const fechaSel = parse(fecha)

  return (
    <section>
      {/* ---------------------------------------------------------- portada */}
      <div className="hero">
        <span className="hero-tag"><span className="live" />Disponibilidad en vivo</span>
        <Silueta name="celebracion" className="hero-sil" />
        <div className="hero-in">
          <span className="kicker">Hola, {(usuario?.nombre || '').split(' ')[0] || 'crack'}</span>
          <h1 className="display h-xl" style={{ marginTop: 14 }}>Bajo las luces,<br /><span className="volt">cada minuto cuenta.</span></h1>
          <p className="lead">Elige cancha, día y hora. Te mostramos qué tan rápido se llena cada franja para que no te quedes sin jugar.</p>
          <div className="hero-meta">
            <div className="stat"><div className="v">{canchas.length || '—'}</div><div className="k">Canchas activas</div></div>
            <div className="stat"><div className="v">{franjas.length ? `${franjas[0].hora_inicio.slice(0, 2)}–${franjas[franjas.length - 1].hora_fin.slice(0, 2)}` : '—'}<small>h</small></div><div className="k">Horario nocturno</div></div>
            <div className="stat"><div className="v">{libres}</div><div className="k">Libres este día</div></div>
            <div className="grow" />
            <button className="btn glow" onClick={() => horarioRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })}>
              Reservar ahora<Icon name="arrow" size={18} className="go" />
            </button>
          </div>
        </div>
      </div>

      {msg && <div className={'toast ' + msg.t}><Icon name={msg.t === 'ok' ? 'check' : 'info'} size={18} /><span className="grow">{msg.m}</span>
        {msg.t === 'ok' && <button className="btn line sm" onClick={irAMis}>Ver mis reservas</button>}</div>}

      {/* ---------------------------------------------------------- IA: sugeridas */}
      <Sugerencias data={sugerencias} onUsar={usarSugerencia} nombreDe={nombreDe} />

      {/* ---------------------------------------------------------- 01 cancha */}
      <div className={'block' + (canchaId ? ' done' : '')}>
        <div className="block-head">
          <span className="idx">01</span>
          <div className="ttl"><h3 className="h-sm">Elige tu cancha</h3><p>Todas en césped sintético con iluminación LED.</p></div>
          <span className="val">{nombreDe(canchaId)}</span>
        </div>
        <div className="block-body">
          <div className="courts">
            {canchas.map(c => (
              <button key={c.cancha_id} className={'court' + (String(c.cancha_id) === canchaId ? ' on' : '')} onClick={() => setCanchaId(String(c.cancha_id))}>
                <span className="chk"><Icon name="check" size={15} /></span>
                <div className="mini" />
                <div className="nm">{c.nombre}</div>
                <div className="sf">{c.superficie || 'Césped sintético'} · Fútbol 5</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ---------------------------------------------------------- 02 fecha */}
      <div className="block done">
        <div className="block-head">
          <span className="idx">02</span>
          <div className="ttl"><h3 className="h-sm">¿Qué día juegas?</h3><p>Puedes reservar hasta con dos semanas de anticipación.</p></div>
          <span className="val">{DIAS[fechaSel.getDay()]} {fechaSel.getDate()} {MESES[fechaSel.getMonth()]}</span>
        </div>
        <div className="block-body">
          <div className="dates">
            {dias.map((d, i) => {
              const k = iso(d)
              return (
                <button key={k} className={'date' + (k === fecha ? ' on' : '') + (d.getDay() === 5 || d.getDay() === 6 ? ' wk' : '')} onClick={() => setFecha(k)}>
                  <div className="dw">{i === 0 ? 'Hoy' : DIAS[d.getDay()]}</div>
                  <div className="dn">{d.getDate()}</div>
                  <div className="dm">{MESES[d.getMonth()]}</div>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* ---------------------------------------------------------- 03 horario */}
      <div className="block" ref={horarioRef} style={{ scrollMarginTop: 90 }}>
        <div className="block-head">
          <span className="idx">03</span>
          <div className="ttl"><h3 className="h-sm">Escoge la hora</h3><p>La barra indica la demanda que predice la IA para esta franja.</p></div>
          <span className="val">{libres} libre{libres === 1 ? '' : 's'}</span>
        </div>
        <div className="block-body">
          {cargando && !franjas.length ? (
            <div className="slots">{[0, 1, 2, 3].map(i => <div key={i} className="skeleton" />)}</div>
          ) : !franjas.length ? (
            <div className="empty"><Silueta name="duelo" style={{ width: 200 }} />No hay franjas configuradas.</div>
          ) : (
            <div className="slots" style={{ opacity: cargando ? .6 : 1, transition: 'opacity .2s' }}>
              {franjas.map(f => {
                const pasada = yaPaso(fecha, f.hora_inicio)
                const libre = f.estado === 'libre' && !pasada
                const dem = demanda[f.franja_id]
                return (
                  <button key={f.franja_id} className={'slot ' + (pasada ? 'past' : libre ? 'free' : 'taken')}
                    onClick={() => libre && abrir(f)} disabled={!libre} aria-label={`${f.hora_inicio} ${libre ? 'disponible' : 'no disponible'}`}>
                    <div className="top">
                      <span className="state"><Icon name={libre ? 'check' : pasada ? 'clock' : 'x'} size={14} />{pasada ? 'Ya pasó' : libre ? 'Disponible' : 'Reservada'}</span>
                      {libre && dem && <span className={'pill ' + dem.nivel}>{dem.nivel === 'alta' && <Icon name="flame" size={12} />}{NIVEL[dem.nivel]}</span>}
                    </div>
                    <div className="time">{f.hora_inicio}<small>– {f.hora_fin}</small></div>
                    {libre && dem && (
                      <div className="demand">
                        <div className="lbl"><span>Demanda estimada</span><b>{pct(dem.probabilidad)} %</b></div>
                        <div className={'meter ' + dem.nivel}><i style={{ width: pct(dem.probabilidad) + '%' }} /></div>
                      </div>
                    )}
                    {libre && <div className="cta">Reservar esta franja<Icon name="arrow" size={15} /></div>}
                  </button>
                )
              })}
            </div>
          )}
        </div>
        <details className="fold">
          <summary><Icon name="whistle" size={17} />Reglamento de la cancha<Icon name="chevron" size={17} className="chev" /></summary>
          <div className="fold-body"><ul className="rules">{REGLAS.map(([ic, t]) => <li key={t}><Icon name={ic} size={18} />{t}</li>)}</ul></div>
        </details>
      </div>

      {/* ---------------------------------------------------------- hoja de reserva */}
      {seleccion && (
        <>
          <div className="sheet-bg" onClick={() => !enviando && setSeleccion(null)} />
          <form className="sheet" onSubmit={confirmar} role="dialog" aria-label="Confirmar reserva">
            <div className="sheet-head">
              <span className="kicker">Confirmar reserva</span>
              <button type="button" className="icon-btn" onClick={() => setSeleccion(null)} disabled={enviando} aria-label="Cerrar"><Icon name="x" size={16} /></button>
            </div>
            <div className="sheet-body">
              <div className="ticket">
                <div className="tk-row">
                  <div><div className="tk-l">Cancha</div><div className="tk-v">{nombreDe(seleccion.cancha_id)}</div></div>
                  <Icon name="pitch" size={34} />
                </div>
                <div className="tk-cut" />
                <div className="tk-row">
                  <div><div className="tk-l">Fecha</div><div className="tk-v" style={{ fontSize: 22 }}>{fechaLarga(seleccion.fecha)}</div></div>
                  <div style={{ textAlign: 'right' }}><div className="tk-l">Hora</div><div className="tk-v">{seleccion.hora_inicio}</div></div>
                </div>
              </div>

              <h4 className="h-sm" style={{ margin: '28px 0 16px', fontSize: 18 }}>Datos de contacto</h4>
              <div className="field"><label>Nombre completo</label>
                <div className="input"><Icon name="user" size={17} /><input value={datos.nombre_contacto} required minLength={3} onChange={e => setDatos({ ...datos, nombre_contacto: e.target.value })} /></div></div>
              <div className="field"><label>Celular</label>
                <div className="input"><Icon name="phone" size={17} /><input value={datos.celular} required minLength={7} inputMode="tel" placeholder="300 123 4567" onChange={e => setDatos({ ...datos, celular: e.target.value })} /></div></div>
              <div className="field"><label>Correo electrónico</label>
                <div className="input"><Icon name="mail" size={17} /><input type="email" value={datos.correo_contacto} required onChange={e => setDatos({ ...datos, correo_contacto: e.target.value })} /></div></div>

              <details className="fold boxed" style={{ marginTop: 8 }}>
                <summary><Icon name="whistle" size={16} />Antes de reservar<Icon name="chevron" size={16} className="chev" /></summary>
                <div className="fold-body"><ul className="rules">{REGLAS.map(([ic, t]) => <li key={t}><Icon name={ic} size={17} />{t}</li>)}</ul></div>
              </details>
            </div>
            <div className="sheet-foot">
              <button className="btn wide glow" type="submit" disabled={enviando}>
                {enviando ? 'Reservando…' : 'Confirmar reserva'}<Icon name="arrow" size={18} className="go" />
              </button>
            </div>
          </form>
        </>
      )}
    </section>
  )
}

function Sugerencias({ data, onUsar, nombreDe }) {
  if (!data) return <div className="ai-block"><div className="ai-in"><div className="picks">{[0, 1, 2].map(i => <div key={i} className="skeleton" style={{ minHeight: 150 }} />)}</div></div></div>
  if (!data.items?.length) return null
  return (
    <div className="ai-block">
      <div className="ai-in">
        <div className="ai-head">
          <div className="grow">
            <span className="pill ai"><Icon name="spark" size={13} />Inteligencia GolTime</span>
            <h2 className="display h-md" style={{ marginTop: 12 }}>{data.personalizado ? 'Hecho a tu medida' : 'Los horarios del momento'}</h2>
            <p className="muted" style={{ margin: '6px 0 0', fontSize: 14 }}>
              {data.personalizado ? 'Franjas libres que encajan con el día y la hora en que sueles jugar.' : 'Aún no conocemos tus hábitos: te mostramos lo que más reserva la comunidad.'}
            </p>
          </div>
        </div>
        <div className="picks">
          {data.items.map(s => (
            <div className="pick" key={`${s.fecha}-${s.franja_id}`}>
              <div className="when">
                <span className="num">{s.hora_inicio}</span>
                <span className="d">{s.dia} {parse(s.fecha).getDate()}</span>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                <span className="tiny"><Icon name="pitch" size={13} /> {s.cancha || nombreDe(s.cancha_id)}</span>
                <span className={'pill ' + s.nivel}>{NIVEL[s.nivel]}</span>
              </div>
              <div className="why">{s.motivo}</div>
              <div className="match"><span>Afinidad</span><div className="meter"><i style={{ width: pct(s.afinidad) + '%' }} /></div><b>{pct(s.afinidad)} %</b></div>
              <button className="btn sm" onClick={() => onUsar(s)}>Reservar<Icon name="arrow" size={15} className="go" /></button>
            </div>
          ))}
        </div>
      </div>
      <details className="fold" style={{ background: 'var(--carbon)', borderRadius: '0 0 var(--r-lg) var(--r-lg)' }}>
        <summary><Icon name="brain" size={17} />¿Cómo elegimos estas franjas?<Icon name="chevron" size={17} className="chev" /></summary>
        <div className="fold-body">
          Analizamos el historial de reservas: qué días y a qué hora juegas más (tu <b>afinidad</b>) y qué tan probable es
          que cada franja se ocupe (la <b>demanda</b>, aprendida de los últimos meses con más peso para las semanas recientes).
          El puntaje combina ambas: <code>afinidad × √(1 − demanda)</code>. Así priorizamos horarios que te gustan y que todavía puedes conseguir.
        </div>
      </details>
    </div>
  )
}
