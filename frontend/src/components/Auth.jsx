import React, { useState } from 'react'
import { api } from '../api'
import Icon from './Icon.jsx'
import { Wordmark } from './Navbar.jsx'
import Silueta from './Silueta.jsx'

// Cuentas generadas por backend/scripts/generar_dataset.py (contrasena demo1234).
const DEMOS = [
  ['Daniel', 'Fiel entre semana', 'daniel@correo.com', 'cliente123'],
  ['Laura', 'Fin de semana', 'laura@demo.goltime.co', 'demo1234'],
  ['Andrés', 'En riesgo', 'andres@demo.goltime.co', 'demo1234'],
  ['Camila', 'Ocasional', 'camila@demo.goltime.co', 'demo1234'],
  ['Julián', 'Cupos libres', 'julian@demo.goltime.co', 'demo1234'],
  ['Admin', 'Administrador', 'admin@goltime.com', 'admin123'],
]

export default function Auth({ onLogin }) {
  const [modo, setModo] = useState('login')
  const [nombre, setNombre] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [cargando, setCargando] = useState(false)

  async function enviar(e) {
    e.preventDefault()
    setErr(''); setCargando(true)
    try {
      const r = modo === 'login' ? await api.login(email, password) : await api.register(nombre, email, password)
      localStorage.setItem('goltime_token', r.access_token)
      onLogin(r.usuario)
    } catch (ex) {
      setErr(ex.detail || 'No fue posible continuar')
    } finally { setCargando(false) }
  }

  const demo = (e, p) => { setModo('login'); setEmail(e); setPassword(p); setErr('') }

  return (
    <div className="auth">
      <aside className="auth-art">
        <Silueta name="cabezazo" className="auth-sil" />
        <Wordmark />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <span className="kicker">Canchas sintéticas · Fútbol 5</span>
          <h1 className="display h-xl" style={{ marginTop: 14 }}>Tu cancha.<br /><span className="volt">Tu hora.</span><br /><span className="outline-text">Sin choques.</span></h1>
          <p className="lead" style={{ color: '#B7C0BB' }}>Reserva en segundos, con disponibilidad en tiempo real y sugerencias inteligentes según cómo juegas.</p>
        </div>
      </aside>

      <main className="auth-form">
        <div className="auth-card">
          <span className="kicker">{modo === 'login' ? 'Bienvenido de vuelta' : 'Únete al equipo'}</span>
          <h2 className="display h-lg" style={{ marginTop: 10 }}>{modo === 'login' ? 'Entra a jugar' : 'Crea tu cuenta'}</h2>

          <div className="switcher">
            <button className={modo === 'login' ? 'on' : ''} onClick={() => { setModo('login'); setErr('') }}>Iniciar sesión</button>
            <button className={modo === 'registro' ? 'on' : ''} onClick={() => { setModo('registro'); setErr('') }}>Registrarme</button>
          </div>

          <form onSubmit={enviar}>
            {modo === 'registro' && (
              <div className="field"><label>Nombre</label>
                <div className="input"><Icon name="user" size={17} /><input value={nombre} onChange={e => setNombre(e.target.value)} required minLength={2} placeholder="Tu nombre" /></div></div>
            )}
            <div className="field"><label>Correo</label>
              <div className="input"><Icon name="mail" size={17} /><input type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="tu@correo.com" /></div></div>
            <div className="field"><label>Contraseña</label>
              <div className="input"><Icon name="shield" size={17} /><input type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={6} placeholder="Mínimo 6 caracteres" /></div></div>
            <button className="btn wide glow" disabled={cargando} style={{ marginTop: 8 }}>
              {cargando ? 'Procesando…' : (modo === 'login' ? 'Entrar a la cancha' : 'Crear cuenta')}
              <Icon name="arrow" size={18} className="go" />
            </button>
          </form>
          {err && <div className="toast err"><Icon name="info" size={18} />{err}</div>}

          {modo === 'login' && (
            <div className="demo">
              Perfiles de demostración (cada uno con un patrón de juego distinto):
              <div className="demo-grid">
                {DEMOS.map(([n, rol, e, p]) => (
                  <button key={e} type="button" className="demo-chip" onClick={() => demo(e, p)}><b>{n}</b><span>{rol}</span></button>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
