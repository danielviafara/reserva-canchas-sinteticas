import React, { useEffect, useState } from 'react'
import { api } from '../api'
import Icon from './Icon.jsx'
import { pct, fechaLarga } from '../utils'

export default function AdminIA() {
  const [d, setD] = useState(null)
  const [err, setErr] = useState('')
  const [modo, setModo] = useState('prediccion')

  useEffect(() => { api.adminIA().then(setD).catch(() => setErr('No se pudo entrenar el modelo. ¿Está corriendo el backend?')) }, [])

  if (err) return <div className="toast err"><Icon name="info" size={18} />{err}</div>
  if (!d) return <div className="kpis">{[0, 1, 2, 3].map(i => <div key={i} className="skeleton" />)}</div>

  const m = d.cancelacion.metricas
  const maxCoef = Math.max(...d.cancelacion.coeficientes.map(c => Math.abs(c.peso)), 0.01)
  const cols = d.heatmap[0]?.celdas.length || 1

  return (
    <div>
      {/* ------------------------------------------------ KPIs */}
      <div className="kpis" style={{ marginTop: 0 }}>
        <Kpi icon="pitch" k="Ocupación histórica" v={pct(d.kpis.ocupacion)} u="%" s="Cupos ocupados sobre cupos ofrecidos" />
        <Kpi icon="trend" k="Próximos 7 días" v={pct(d.kpis.ocupacion_7d_esperada)} u="%" s="Ocupación que predice la IA" />
        <Kpi icon="ticket" k="Reservas · 30 días" v={d.kpis.reservas_mes} s="Reservas confirmadas del último mes" />
        <Kpi icon="x" k="Cancelación" v={pct(d.kpis.tasa_cancelacion)} u="%" s="De todas las reservas pasadas" />
      </div>

      {/* ------------------------------------------------ insights */}
      <h3 className="h-sm" style={{ margin: '34px 0 0', display: 'flex', alignItems: 'center', gap: 10 }}><Icon name="spark" size={20} />Lo que encontró la IA</h3>
      <div className="insights">
        {d.insights.map(i => (
          <div className="ins" key={i.titulo}>
            <div className="ic"><Icon name={i.icono} size={17} /></div>
            <div className="t">{i.titulo}</div>
            <div className="x">{i.texto}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginTop: 16 }}>
        {/* ------------------------------------------------ mapa de calor */}
        <div className="card">
          <div className="card-h">
            <div><h3 className="h-sm">Mapa de demanda</h3><p>{modo === 'prediccion' ? 'Probabilidad de ocupación que aprendió el modelo.' : 'Ocupación real de las últimas 8 semanas.'}</p></div>
            <div className="seg">
              <button className={modo === 'prediccion' ? 'on' : ''} onClick={() => setModo('prediccion')}>IA</button>
              <button className={modo === 'real' ? 'on' : ''} onClick={() => setModo('real')}>Real</button>
            </div>
          </div>
          <div className="heat">
            <div className="heat-row" style={{ '--cols': cols }}>
              <span />{d.heatmap[0]?.celdas.map(c => <span key={c.hora} className="tiny" style={{ textAlign: 'center' }}>{c.hora}</span>)}
            </div>
            {d.heatmap.map(h => (
              <div className="heat-row" key={h.dia} style={{ '--cols': cols }}>
                <span className="dl">{h.dia.slice(0, 3)}</span>
                {h.celdas.map(c => {
                  const v = modo === 'prediccion' ? c.prediccion : c.real
                  return <span key={c.hora} className={'heat-cell' + (v > 0.55 ? ' hi' : '')} style={{ '--v': Math.min(1, v) }}
                    title={`${h.dia} ${c.hora} · IA ${pct(c.prediccion)} % · real ${pct(c.real)} %`}>{pct(v)}</span>
                })}
              </div>
            ))}
          </div>
          <div className="heat-legend"><span>0 %</span><span className="bar" /><span>100 %</span></div>
        </div>

        {/* ------------------------------------------------ pronostico */}
        <div className="card">
          <div className="card-h"><div><h3 className="h-sm">Pronóstico 7 días</h3><p>Lo que ya está reservado frente a lo que la IA espera que se llene.</p></div></div>
          <div className="bars">
            {d.pronostico.map(p => (
              <div className="col" key={p.fecha} title={`${fechaLarga(p.fecha)} · esperado ${pct(p.esperado)} % · reservado ${pct(p.reservado)} %`}>
                <span className="pv">{pct(p.esperado)}</span>
                <div className="stack">
                  <div className="exp" style={{ height: pct(p.esperado) + '%' }} />
                  <div className="res" style={{ height: pct(p.reservado) + '%' }} />
                </div>
                <span className="lb">{p.dia}</span>
              </div>
            ))}
          </div>
          <div className="legend">
            <span><i style={{ background: 'var(--chalk)' }} />Ya reservado</span>
            <span><i style={{ background: 'rgba(212,255,58,.35)', borderTop: '2px solid var(--volt)' }} />Esperado por la IA (%)</span>
          </div>
        </div>
      </div>

      <div className="grid-2" style={{ marginTop: 16 }}>
        {/* ------------------------------------------------ riesgo */}
        <div className="card">
          <div className="card-h"><div><h3 className="h-sm">Riesgo de cancelación</h3><p>Reservas de esta semana que el modelo cree que podrían caerse.</p></div></div>
          {!d.cancelacion.en_riesgo.length ? <div className="empty">Sin reservas próximas.</div> : (
            <div className="table-wrap"><table>
              <thead><tr><th>Cuándo</th><th>Cliente</th><th>Riesgo</th></tr></thead>
              <tbody>{d.cancelacion.en_riesgo.map(r => {
                const nivel = r.riesgo >= 0.4 ? 'alta' : r.riesgo >= 0.25 ? 'media' : 'baja'
                return (
                  <tr key={r.reserva_id}>
                    <td><b>{r.dia.slice(0, 3)} {r.fecha.slice(8)} · {r.hora}</b><div className="tiny">{r.cancha}</div></td>
                    <td>{r.cliente}</td>
                    <td><div className="risk"><div className={'meter ' + nivel}><i style={{ width: pct(r.riesgo) + '%' }} /></div><b className="num">{pct(r.riesgo)}%</b></div></td>
                  </tr>
                )
              })}</tbody>
            </table></div>
          )}
        </div>

        {/* ------------------------------------------------ coeficientes */}
        <div className="card">
          <div className="card-h">
            <div><h3 className="h-sm">¿Qué hace que alguien cancele?</h3><p>Pesos de la regresión logística. Rojo sube el riesgo, verde lo baja.</p></div>
          </div>
          <div className="coefs">
            {d.cancelacion.coeficientes.map(c => {
              const w = Math.abs(c.peso) / maxCoef * 50
              return (
                <div className="coef" key={c.variable}>
                  <span>{c.variable}</span>
                  <div className="axis"><i className={c.peso >= 0 ? 'pos' : 'neg'} style={{ width: w + '%' }} /></div>
                  <span className="w">{c.peso > 0 ? '+' : ''}{c.peso.toFixed(2)}</span>
                </div>
              )
            })}
          </div>
          <div className="kpis" style={{ gridTemplateColumns: 'repeat(3,1fr)' }}>
            <MiniKpi k="Detecta" v={(m.lift ?? '—') + '×'} s={`El 20 % más riesgoso cancela ${pct(m.tasa_top20)} % vs ${pct(m.tasa_prueba)} % promedio`} />
            <MiniKpi k="AUC" v={m.auc ?? '—'} s="0,5 = azar · 1 = perfecto" />
            <MiniKpi k="Exactitud" v={pct(m.exactitud) + '%'} s={`vs ${pct(m.exactitud_base)} % de la línea base · ${m.registros_prueba} de prueba`} />
          </div>
        </div>
      </div>

      {/* ------------------------------------------------ segmentos */}
      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-h"><div><h3 className="h-sm">Tipos de jugador</h3><p>Grupos que descubrió K-means a partir del comportamiento de {d.dataset.clientes} clientes.</p></div><Icon name="users" size={22} /></div>
        <div className="segs">
          {d.segmentos.map(s => (
            <div className="sg" key={s.nombre}>
              <div className="n"><b>{s.nombre}</b><span>{s.clientes}</span></div>
              <p>{s.descripcion}</p>
              <dl>
                <div><dt>Reservas / mes</dt><dd>{s.frecuencia_mes}</dd></div>
                <div><dt>Cancelan</dt><dd>{pct(s.tasa_cancelacion)}%</dd></div>
                <div><dt>Fin de semana</dt><dd>{pct(s.pct_fin_de_semana)}%</dd></div>
                <div><dt>Regularidad</dt><dd>{pct(s.regularidad)}%</dd></div>
              </dl>
            </div>
          ))}
        </div>
      </div>

      {/* ------------------------------------------------ explicacion */}
      <div className="block" style={{ marginTop: 16 }}>
        <details className="fold" style={{ borderTop: 0 }}>
          <summary><Icon name="brain" size={18} />Cómo funciona la inteligencia artificial<Icon name="chevron" size={18} className="chev" /></summary>
          <div className="fold-body">
            <p style={{ marginTop: 0 }}>
              El modelo se entrena con <b>{d.dataset.reservas.toLocaleString('es-CO')} reservas</b> ({d.dataset.desde} a {d.dataset.hasta}) leídas de la base de datos.
              Se vuelve a entrenar solo cuando se crea o cancela una reserva. Último entrenamiento: {d.entrenado_en.replace('T', ' ')}.
            </p>
            <div className="steps">
              <div className="step"><div className="sn">01</div><b>Predicción de demanda</b><p>Para cada día y hora calcula la tasa de ocupación histórica. Las semanas recientes pesan más (vida media de 6 semanas) y un <i>suavizado bayesiano</i> evita conclusiones exageradas con pocos datos. Luego ajusta por la popularidad de cada cancha.</p></div>
              <div className="step"><div className="sn">02</div><b>Riesgo de cancelación</b><p>Una <i>regresión logística</i> entrenada con descenso de gradiente usa la antelación, el día, la hora y el historial del cliente. Se valida con un corte temporal 80/20: aprende del pasado y se evalúa en las reservas más recientes.</p></div>
              <div className="step"><div className="sn">03</div><b>Segmentación</b><p><i>K-means</i> (k = 4) agrupa a los clientes por frecuencia, tasa de cancelación, % de fin de semana, antelación y regularidad (cuánto repite día y hora), normalizados entre 0 y 1. Cada grupo se nombra según su rasgo dominante.</p></div>
              <div className="step"><div className="sn">04</div><b>Recomendación</b><p>A cada jugador se le sugieren franjas libres con el puntaje <code>afinidad × √(1 − demanda)</code>: horarios que suele jugar y que todavía puede conseguir.</p></div>
            </div>
            <p className="tiny" style={{ marginBottom: 0, marginTop: 16 }}>
              Datos ficticios generados con <code>python -m scripts.generar_dataset</code> (ver <code>database/dataset/</code>). Implementación en <code>backend/app/services/ia_service.py</code>, sin librerías externas.
            </p>
          </div>
        </details>
      </div>
    </div>
  )
}

function Kpi({ icon, k, v, u, s }) {
  return <div className="kpi"><div className="k"><Icon name={icon} size={15} />{k}</div><div className="v">{v}{u && <small>{u}</small>}</div><div className="s">{s}</div></div>
}
function MiniKpi({ k, v, s }) {
  return <div className="kpi" style={{ padding: 14 }}><div className="k">{k}</div><div className="v" style={{ fontSize: 30 }}>{v}</div><div className="s">{s}</div></div>
}
