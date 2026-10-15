import React, { useState } from 'react'
import { api } from '../api'

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
      const r = modo === 'login'
        ? await api.login(email, password)
        : await api.register(nombre, email, password)
      localStorage.setItem('goltime_token', r.access_token)
      onLogin(r.usuario)
    } catch (ex) {
      setErr(ex.detail || 'No fue posible continuar')
    } finally { setCargando(false) }
  }

  return (
    <div className="auth-wrap">
      <div className="brand" style={{ textAlign: 'center', fontSize: 28, marginBottom: 6 }}>Gol<span>Time</span></div>
      <p className="sub" style={{ textAlign: 'center' }}>Reserva de canchas sintéticas</p>
      <div className="panel">
        <h2>{modo === 'login' ? 'Iniciar sesión' : 'Crear cuenta'}</h2>
        <p className="sub">{modo === 'login' ? 'Ingresa para reservar tu cancha.' : 'Regístrate para empezar a reservar.'}</p>
        <form onSubmit={enviar}>
          {modo === 'registro' && (
            <div className="field">
              <label>Nombre</label>
              <input value={nombre} onChange={e => setNombre(e.target.value)} required minLength={2} />
            </div>
          )}
          <div className="field">
            <label>Correo</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <div className="field">
            <label>Contraseña</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={6} />
          </div>
          <button className="btn" style={{ width: '100%' }} disabled={cargando}>
            {cargando ? 'Procesando...' : (modo === 'login' ? 'Entrar' : 'Registrarme')}
          </button>
        </form>
        {err && <div className="msg err">{err}</div>}
        <div className="switch">
          {modo === 'login' ? '¿No tienes cuenta?' : '¿Ya tienes cuenta?'}{' '}
          <button onClick={() => { setErr(''); setModo(modo === 'login' ? 'registro' : 'login') }}>
            {modo === 'login' ? 'Crear una' : 'Iniciar sesión'}
          </button>
        </div>
        {modo === 'login' && <div className="hint">Demo: daniel@correo.com · cliente123</div>}
      </div>
    </div>
  )
}
