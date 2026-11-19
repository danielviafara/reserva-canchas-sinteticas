import React, { useEffect, useState } from 'react'
import { api } from '../api'
import Icon from './Icon.jsx'
import Silueta from './Silueta.jsx'
import { NIVEL, pct, parse, fechaLarga } from '../utils'

const SILUETA_SEGMENTO = { Fieles: 'celebracionEspalda', 'Fin de semana': 'celebracion', 'En riesgo': 'cabezazo', Ocasionales: 'remate', Nuevo: 'remate' }

// Vista del jugador: el patron de juego que la IA reconoce en su historial.
export default function MiJuego({ irAReservar }) {
  const [d, setD] = useState(null)
  const [err, setErr] = useState('')
  useEffect(() => { api.miPerfil().then(setD).catch(() => setErr('No se pudo calcular tu perfil.')) }, [])
  return (
    <section>
      <div className="page-head page-head-sil">
        <Silueta name="cabezazo" className="deco" />
        <div>
          <span className="kicker">Análisis con IA</span>
          <h1 className="display h-lg" style={{ marginTop: 12 }}>Mi juego</h1>
          <p className="lead">Lo que la inteligencia artificial aprendió de tus reservas: cuándo juegas, qué tan constante eres y qué te conviene reservar.</p>
        </div>
        <button className="btn glow" onClick={() => irAReservar()}>Reservar<Icon name="arrow" size={18} className="go" /></button>
      </div>
      {err && <div className="toast err"><Icon name="info" size={18} />{err}</div>}
      {!d && !err && <div className="kpis">{[0, 1, 2, 3].map(i => <div key={i} className="skeleton" />)}</div>}
      {d && <PerfilJugador d={d} vista="cliente" onReservar={irAReservar} />}
    </section>
  )
}

export function PerfilJugador({ d, vista = 'cliente', onReservar }) {
  const tu = vista === 'cliente'
  const s = d.stats, c = d.comunidad || {}
  const maxHeat = Math.max(1, ...d.heatmap.flatMap(h => h.celdas.map(x => x.veces)))
  const maxMes = Math.max(1, ...d.mensual.map(m => m.jugadas + m.canceladas))
  const cols = d.heatmap[0]?.celdas.length || 1
  const comp = (a, b, menorEsMejor) => {
    if (!b) return ''
    const r = a / b
    if (r > 1.15) return menorEsMejor ? 'por encima del promedio' : `${r.toFixed(1)}× el promedio`
    if (r < 0.85) return menorEsMejor ? 'mejor que el promedio' : 'por debajo del promedio'
    return 'en el promedio'
  }

  return (
    <div>
      {/* ---------------------------------------------- segmento + patron */}
      <div className="ai-block" style={{ marginTop: tu ? 24 : 0 }}>
        <div className="ai-in profile-hero">
          <div className="seg-badge"><Silueta name={SILUETA_SEGMENTO[d.segmento.nombre] || 'remate'} /></div>
          <div className="grow">
            <span className="pill ai"><Icon name="spark" size={13} />{tu ? 'Tu tipo de jugador' : 'Tipo de jugador'} · K-means</span>
            <h2 className="display h-lg" style={{ marginTop: 10 }}>{d.segmento.nombre}</h2>
            <p className="muted" style={{ margin: '6px 0 0' }}>{d.segmento.descripcion}</p>
          </div>
          <div className="pattern-quote">
            <div className="lbl-up" style={{ color: 'var(--volt)' }}>Patrón detectado</div>
            <p>{d.patron}</p>
          </div>
        </div>
      </div>

      {/* ---------------------------------------------- KPIs */}
      <div className="kpis">
        <div className="kpi"><div className="k"><Icon name="trophy" size={15} />Partidos jugados</div><div className="v">{s.jugadas}</div><div className="s">{s.reservas} reservas · {s.proximas} próxima{s.proximas === 1 ? '' : 's'}</div></div>
        <div className="kpi"><div className="k"><Icon name="trend" size={15} />Reservas / mes</div><div className="v">{s.frecuencia_mes}</div><div className="s">Comunidad: {c.frecuencia_mes} · {comp(s.frecuencia_mes, c.frecuencia_mes)}</div></div>
        <div className="kpi"><div className="k"><Icon name="x" size={15} />Cancelación</div><div className="v">{pct(s.tasa_cancelacion)}<small>%</small></div><div className="s">Comunidad: {pct(c.tasa_cancelacion)} % · {comp(s.tasa_cancelacion, c.tasa_cancelacion, true)}</div></div>
        <div className="kpi"><div className="k"><Icon name="stopwatch" size={15} />Regularidad</div><div className="v">{pct(s.regularidad)}<small>%</small></div><div className="s">{tu ? 'De tus reservas en tu' : 'De sus reservas en su'} combinación favorita</div></div>
      </div>

      <div className="grid-2" style={{ marginTop: 16 }}>
        {/* ---------------------------------------------- heatmap personal */}
        <div className="card">
          <div className="card-h"><div><h3 className="h-sm">{tu ? 'Tu mapa de juego' : 'Mapa de juego'}</h3><p>Partidos confirmados por día y hora. Lo más brillante es {tu ? 'tu' : 'su'} rutina.</p></div></div>
          <div className="heat">
            <div className="heat-row" style={{ '--cols': cols }}>
              <span />{d.heatmap[0]?.celdas.map(x => <span key={x.hora} className="tiny" style={{ textAlign: 'center' }}>{x.hora}</span>)}
            </div>
            {d.heatmap.map(h => (
              <div className="heat-row" key={h.dia} style={{ '--cols': cols }}>
                <span className="dl">{h.dia.slice(0, 3)}</span>
                {h.celdas.map(x => {
                  const v = x.veces / maxHeat
                  return <span key={x.hora} className={'heat-cell' + (v > 0.55 ? ' hi' : '') + (x.veces ? '' : ' zero')} style={{ '--v': v }} title={`${h.dia} ${x.hora}: ${x.veces} partidos`}>{x.veces || ''}</span>
                })}
              </div>
            ))}
          </div>
        </div>

        {/* ---------------------------------------------- historial mensual */}
        <div className="card">
          <div className="card-h"><div><h3 className="h-sm">Últimos 6 meses</h3><p>Reservas por mes: jugadas y canceladas.</p></div></div>
          <div className="bars">
            {d.mensual.map(m => (
              <div className="col" key={m.mes} title={`${m.mes}: ${m.jugadas} jugadas, ${m.canceladas} canceladas`}>
                <span className="pv">{m.jugadas + m.canceladas || ''}</span>
                <div className="stack" style={{ flexDirection: 'column', justifyContent: 'flex-end' }}>
                  <div style={{ height: (m.canceladas / maxMes * 100) + '%', background: 'var(--signal)', width: '100%', borderRadius: '3px 3px 0 0' }} />
                  <div className="res" style={{ height: (m.jugadas / maxMes * 100) + '%', background: 'var(--volt)' }} />
                </div>
                <span className="lb">{m.mes}</span>
              </div>
            ))}
          </div>
          <div className="legend"><span><i style={{ background: 'var(--volt)' }} />Jugadas</span><span><i style={{ background: 'var(--signal)' }} />Canceladas</span></div>
        </div>
      </div>

      <div className="grid-2" style={{ marginTop: 16 }}>
        {/* ---------------------------------------------- favoritos */}
        <div className="card">
          <div className="card-h"><div><h3 className="h-sm">Combinaciones favoritas</h3><p>Día y hora que más se repiten en {tu ? 'tu' : 'su'} historial.</p></div></div>
          {!d.favoritos.combos.length ? <div className="empty">Sin partidos todavía.</div> : (
            <div className="list" style={{ marginTop: 0 }}>
              {d.favoritos.combos.map((x, i) => (
                <div className="li" key={x.dia + x.hora}>
                  <span className="ic num" style={{ fontSize: 18 }}>{i + 1}</span>
                  <div className="grow"><b>{x.dia} · {x.hora}</b>
                    <div className="match" style={{ marginTop: 6 }}><div className="meter"><i style={{ width: pct(x.porcentaje) + '%' }} /></div><span>{x.veces} veces · {pct(x.porcentaje)} %</span></div>
                  </div>
                </div>
              ))}
            </div>
          )}
          <div className="tiny" style={{ marginTop: 14, display: 'flex', gap: 18, flexWrap: 'wrap' }}>
            <span><Icon name="pitch" size={14} /> Cancha favorita: <b style={{ color: 'var(--chalk)' }}>{d.favoritos.cancha || '—'}</b></span>
            <span><Icon name="clock" size={14} /> Reserva con <b style={{ color: 'var(--chalk)' }}>{s.antelacion_dias} días</b> de antelación</span>
          </div>
        </div>

        {/* ---------------------------------------------- proximo + riesgo */}
        <div className="card">
          <div className="card-h"><div><h3 className="h-sm">Próximo partido</h3><p>Con la probabilidad de cancelación que estima la regresión logística.</p></div></div>
          {!d.proxima ? <div className="empty"><Icon name="calendar" size={30} />No hay partidos agendados.</div> : (() => {
            const nivel = d.proxima.riesgo >= 0.4 ? 'alta' : d.proxima.riesgo >= 0.25 ? 'media' : 'baja'
            return (
              <>
                <div className="ticket">
                  <div className="tk-row">
                    <div><div className="tk-l">{d.proxima.cancha}</div><div className="tk-v" style={{ fontSize: 24 }}>{fechaLarga(d.proxima.fecha)}</div></div>
                    <div style={{ textAlign: 'right' }}><div className="tk-l">Hora</div><div className="tk-v">{d.proxima.hora}</div></div>
                  </div>
                </div>
                <div className="demand" style={{ marginTop: 18 }}>
                  <div className="lbl"><span>Riesgo de cancelación</span><b>{pct(d.proxima.riesgo)} %</b></div>
                  <div className={'meter ' + nivel}><i style={{ width: pct(d.proxima.riesgo) + '%' }} /></div>
                </div>
                <p className="tiny" style={{ marginBottom: 0 }}>
                  {nivel === 'alta' ? 'Riesgo alto: conviene confirmar asistencia antes del partido.' : nivel === 'media' ? 'Riesgo moderado.' : 'Riesgo bajo: casi seguro se juega.'}
                </p>
              </>
            )
          })()}
        </div>
      </div>

      {/* ---------------------------------------------- recomendaciones */}
      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-h">
          <div><h3 className="h-sm">{tu ? 'Por eso te recomendamos' : 'Lo que la IA le recomienda'}</h3><p>Franjas libres de los próximos 7 días que encajan con este patrón.</p></div>
          <Icon name="spark" size={22} />
        </div>
        {!d.recomendaciones.items.length ? <div className="empty">No hay franjas libres que encajen esta semana.</div> : (
          <div className="picks">
            {d.recomendaciones.items.map(r => (
              <div className="pick" key={r.fecha + r.franja_id}>
                <div className="when"><span className="num">{r.hora_inicio}</span><span className="d">{r.dia} {parse(r.fecha).getDate()}</span></div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                  <span className="tiny"><Icon name="pitch" size={13} /> {r.cancha}</span>
                  <span className={'pill ' + r.nivel}>{NIVEL[r.nivel]}</span>
                </div>
                <div className="why">{r.motivo}</div>
                <div className="match"><span>Coincidencia</span><div className="meter"><i style={{ width: pct(r.afinidad) + '%' }} /></div><b>{pct(r.afinidad)} %</b></div>
                {onReservar && <button className="btn sm" onClick={() => onReservar(r)}>Reservar<Icon name="arrow" size={15} className="go" /></button>}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="block" style={{ marginTop: 16 }}>
        <details className="fold" style={{ borderTop: 0 }}>
          <summary><Icon name="brain" size={18} />Cómo se calcula este perfil<Icon name="chevron" size={18} className="chev" /></summary>
          <div className="fold-body">
            <div className="steps">
              <div className="step"><div className="sn">01</div><b>Hábitos</b><p>Se cuentan las reservas confirmadas por día, hora, cancha y combinación día + hora. La <i>regularidad</i> es el % de reservas en la combinación favorita.</p></div>
              <div className="step"><div className="sn">02</div><b>Tipo de jugador</b><p>K-means agrupa a todos los clientes por frecuencia, cancelación, fin de semana, antelación y regularidad. {tu ? 'Quedaste' : 'Este jugador quedó'} en el grupo <b>{d.segmento.nombre}</b>.</p></div>
              <div className="step"><div className="sn">03</div><b>Riesgo</b><p>La regresión logística mira la antelación, el día, la hora y su historial de cancelaciones para estimar si el próximo partido se cae.</p></div>
              <div className="step"><div className="sn">04</div><b>Recomendación</b><p><code>coincidencia = 0,6·combinación + 0,25·día + 0,15·hora</code>, ponderada por su cancha favorita y por <code>√(1 − demanda)</code>.</p></div>
            </div>
          </div>
        </details>
      </div>
    </div>
  )
}
