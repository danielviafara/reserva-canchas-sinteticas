import React, { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api'
import Icon from './Icon.jsx'
import { PerfilJugador } from './MiJuego.jsx'
import { pct } from '../utils'

const SEGMENTOS = ['Todos', 'Fieles', 'Fin de semana', 'En riesgo', 'Ocasionales', 'Nuevo']

export function AdminClientes() {
  const [cs, setCs] = useState(null)
  const [q, setQ] = useState('')
  const [seg, setSeg] = useState('Todos')
  const [sel, setSel] = useState(null)
  const [perfil, setPerfil] = useState(null)
  const detalle = useRef(null)

  useEffect(() => { api.adminClientes().then(setCs).catch(() => setCs([])) }, [])

  async function ver(c) {
    setSel(c.usuario_id); setPerfil(null)
    setTimeout(() => detalle.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
    try { setPerfil(await api.adminCliente(c.usuario_id)) } catch { setPerfil({ error: true }) }
  }

  const lista = useMemo(() => {
    const t = q.trim().toLowerCase()
    return (cs || []).filter(c => (seg === 'Todos' || c.segmento === seg) &&
      (!t || c.nombre.toLowerCase().includes(t) || c.email.toLowerCase().includes(t)))
  }, [cs, q, seg])

  return (
    <div>
      <div className="card">
        <div className="card-h">
          <div><h3 className="h-sm">Clientes y sus patrones</h3><p>Toca un cliente para ver lo que la IA reconoce en su historial. Los perfiles <span className="tag-demo" style={{ marginLeft: 0 }}>demo</span> tienen patrones marcados para la presentación.</p></div>
          <Icon name="users" size={22} />
        </div>
        <div className="toolbar">
          <div className="input"><Icon name="search" size={17} /><input value={q} onChange={e => setQ(e.target.value)} placeholder="Buscar cliente…" /></div>
          <div className="seg">{SEGMENTOS.map(s => <button key={s} className={seg === s ? 'on' : ''} onClick={() => setSeg(s)}>{s}</button>)}</div>
        </div>
        {!cs ? <div className="skeleton" /> : !lista.length ? <div className="empty">Sin resultados.</div> : (
          <div className="table-wrap" style={{ maxHeight: 460, overflowY: 'auto' }}><table>
            <thead><tr><th>Cliente</th><th>Tipo (IA)</th><th>Reservas</th><th>Por mes</th><th>Cancela</th><th>Patrón</th><th>Regularidad</th></tr></thead>
            <tbody>{lista.map(c => (
              <tr key={c.usuario_id} className={'click' + (sel === c.usuario_id ? ' sel' : '')} onClick={() => ver(c)}>
                <td><b>{c.nombre}</b>{c.demo && <span className="tag-demo">demo</span>}<div className="tiny">{c.email}</div></td>
                <td><span className={'pill ' + (c.segmento === 'En riesgo' ? 'alta' : c.segmento === 'Fieles' ? 'baja' : c.segmento === 'Nuevo' ? 'end' : 'media')}>{c.segmento}</span></td>
                <td className="num">{c.reservas}</td>
                <td>{c.frecuencia_mes}</td>
                <td>{pct(c.tasa_cancelacion)} %</td>
                <td>{c.patron}</td>
                <td><div className="risk"><div className="meter"><i style={{ width: pct(c.regularidad) + '%', background: 'var(--volt)' }} /></div><b className="num">{pct(c.regularidad)}%</b></div></td>
              </tr>))}</tbody>
          </table></div>
        )}
      </div>

      <div ref={detalle} style={{ scrollMarginTop: 90 }}>
        {sel && (
          <div style={{ marginTop: 26 }}>
            {!perfil ? <div className="kpis">{[0, 1, 2, 3].map(i => <div key={i} className="skeleton" />)}</div>
              : perfil.error ? <div className="toast err">No se pudo cargar el perfil.</div> : (
                <>
                  <div style={{ display: 'flex', alignItems: 'flex-end', gap: 14, flexWrap: 'wrap', marginBottom: 16 }}>
                    <div className="grow"><span className="kicker">Perfil del cliente</span><h2 className="display h-md" style={{ marginTop: 8 }}>{perfil.nombre}</h2><div className="tiny">{perfil.email}</div></div>
                    <button className="btn line sm" onClick={() => { setSel(null); setPerfil(null) }}><Icon name="x" size={14} />Cerrar</button>
                  </div>
                  <PerfilJugador d={perfil} vista="admin" />
                </>
              )}
          </div>
        )}
      </div>
    </div>
  )
}

function Dist({ titulo, datos }) {
  const max = Math.max(1, ...datos.map(d => d.confirmadas + d.canceladas))
  return (
    <div className="card">
      <div className="card-h"><div><h3 className="h-sm" style={{ fontSize: 18 }}>{titulo}</h3></div></div>
      <div className="dist">
        {datos.map(d => (
          <div className="dist-row" key={d.clave}>
            <span className="tiny" style={{ color: 'var(--chalk)' }}>{d.clave}</span>
            <div className="bar">
              <i style={{ width: (d.confirmadas / max * 100) + '%', background: 'var(--volt)' }} />
              <i style={{ width: (d.canceladas / max * 100) + '%', background: 'var(--signal)' }} />
            </div>
            <span className="num" style={{ textAlign: 'right' }}>{d.confirmadas + d.canceladas}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function AdminDataset() {
  const [d, setD] = useState(null)
  const [err, setErr] = useState('')
  const [bajando, setBajando] = useState(false)
  useEffect(() => { api.adminDataset().then(setD).catch(() => setErr('No se pudo cargar el dataset.')) }, [])

  async function descargar() {
    setBajando(true)
    try { await api.descargarDataset() } catch { setErr('No se pudo descargar el CSV.') } finally { setBajando(false) }
  }

  if (err) return <div className="toast err"><Icon name="info" size={18} />{err}</div>
  if (!d) return <div className="kpis">{[0, 1, 2, 3].map(i => <div key={i} className="skeleton" />)}</div>
  const meses = d.por_mes.map(m => ({ ...m, clave: m.clave.slice(2).replace('-', '/') }))

  return (
    <div>
      <div className="card" style={{ display: 'flex', gap: 20, alignItems: 'center', flexWrap: 'wrap' }}>
        <div className="grow">
          <span className="kicker">Fuente de entrenamiento</span>
          <h3 className="display h-md" style={{ marginTop: 10 }}>Dataset de reservas</h3>
          <p className="muted" style={{ margin: '6px 0 0', fontSize: 14 }}>
            Todo lo que aprende la IA sale de esta tabla, leída en vivo desde PostgreSQL ({d.desde} a {d.hasta}).
          </p>
        </div>
        <button className="btn glow" onClick={descargar} disabled={bajando}><Icon name="layers" size={17} />{bajando ? 'Generando…' : 'Descargar CSV'}</button>
      </div>

      <div className="kpis">
        <div className="kpi"><div className="k"><Icon name="layers" size={15} />Filas</div><div className="v">{d.filas.toLocaleString('es-CO')}</div><div className="s">Una por reserva</div></div>
        <div className="kpi"><div className="k"><Icon name="users" size={15} />Clientes</div><div className="v">{d.clientes}</div><div className="s">Con al menos una reserva</div></div>
        <div className="kpi"><div className="k"><Icon name="check" size={15} />Confirmadas</div><div className="v">{d.confirmadas.toLocaleString('es-CO')}</div><div className="s">{pct(d.confirmadas / d.filas)} % del total</div></div>
        <div className="kpi"><div className="k"><Icon name="x" size={15} />Canceladas</div><div className="v">{d.canceladas}</div><div className="s">{pct(d.canceladas / d.filas)} % · objetivo del modelo</div></div>
      </div>

      <div className="grid-2" style={{ marginTop: 16 }}>
        <Dist titulo="Reservas por día" datos={d.por_dia} />
        <Dist titulo="Reservas por hora" datos={d.por_hora} />
        <Dist titulo="Reservas por cancha" datos={d.por_cancha} />
        <Dist titulo="Reservas por mes" datos={meses} />
      </div>
      <div className="legend"><span><i style={{ background: 'var(--volt)' }} />Confirmadas</span><span><i style={{ background: 'var(--signal)' }} />Canceladas</span></div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-h"><div><h3 className="h-sm">Muestra</h3><p>Las {d.muestra.length} reservas más recientes, con las columnas que usa el modelo.</p></div></div>
        <div className="table-wrap"><table>
          <thead><tr>{d.columnas.map(c => <th key={c.nombre}>{c.nombre}</th>)}</tr></thead>
          <tbody>{d.muestra.map(f => (
            <tr key={f.reserva_id}>{d.columnas.map(c => (
              <td key={c.nombre}>{c.nombre === 'estado' ? <span className={'pill ' + (f.estado === 'confirmada' ? 'ok' : 'off')}>{f.estado}</span> : String(f[c.nombre])}</td>
            ))}</tr>))}</tbody>
        </table></div>
      </div>

      <div className="block" style={{ marginTop: 16 }}>
        <details className="fold" style={{ borderTop: 0 }} open>
          <summary><Icon name="info" size={18} />Diccionario de datos<Icon name="chevron" size={18} className="chev" /></summary>
          <div className="fold-body"><div className="dict">{d.columnas.map(c => <div key={c.nombre}><code>{c.nombre}</code><br />{c.descripcion}</div>)}</div></div>
        </details>
        <details className="fold">
          <summary><Icon name="spark" size={18} />Cómo se generaron los datos ficticios<Icon name="chevron" size={18} className="chev" /></summary>
          <div className="fold-body">
            <p style={{ marginTop: 0 }}>El script <code>backend/scripts/generar_dataset.py</code> simula 6 meses de operación con reglas realistas:</p>
            <ul className="rules">
              <li><Icon name="flame" size={17} />Viernes y sábado son los días más fuertes; 19:00 y 20:00 la hora pico; lunes el día más flojo.</li>
              <li><Icon name="trend" size={17} />Sube la demanda en quincena (días 14-16 y 29-1) y baja en festivos colombianos y en diciembre.</li>
              <li><Icon name="pitch" size={17} />Cancha 1 es la favorita (mejor iluminación).</li>
              <li><Icon name="users" size={17} />115 clientes de cuatro arquetipos (fiel, fin de semana, ocasional, impredecible) más 5 perfiles demo con patrones marcados.</li>
              <li><Icon name="x" size={17} />La probabilidad de cancelar crece con la antelación, los domingos y según el cliente.</li>
            </ul>
            <p style={{ marginBottom: 0 }}>La IA no conoce estas reglas: las <b>descubre</b> a partir de las reservas. Compara el arquetipo real del CSV <code>database/dataset/reservas_sinteticas.csv</code> con el tipo que asigna K-means.</p>
          </div>
        </details>
      </div>
    </div>
  )
}
