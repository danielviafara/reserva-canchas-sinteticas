import React, { useState } from 'react'
import Auth from './components/Auth.jsx'
import Navbar from './components/Navbar.jsx'
import Disponibilidad from './components/Disponibilidad.jsx'
import MisReservas from './components/MisReservas.jsx'
import Admin from './components/Admin.jsx'

function leerUsuario() {
  try { return JSON.parse(localStorage.getItem('goltime_user')) } catch { return null }
}

export default function App() {
  const [usuario, setUsuario] = useState(leerUsuario())
  const [vista, setVista] = useState(() => (leerUsuario()?.rol === 'admin' ? 'admin' : 'disponibilidad'))

  function onLogin(u) {
    localStorage.setItem('goltime_user', JSON.stringify(u)); setUsuario(u)
    setVista(u.rol === 'admin' ? 'admin' : 'disponibilidad')
  }
  function onLogout() { localStorage.removeItem('goltime_token'); localStorage.removeItem('goltime_user'); setUsuario(null) }

  if (!usuario) return <Auth onLogin={onLogin} />

  return (
    <div className="shell">
      <Navbar usuario={usuario} vista={vista} setVista={setVista} onLogout={onLogout} />
      {vista === 'disponibilidad' && <Disponibilidad usuario={usuario} irAMis={() => setVista('mis')} />}
      {vista === 'mis' && <MisReservas irAReservar={() => setVista('disponibilidad')} />}
      {vista === 'admin' && usuario.rol === 'admin' && <Admin />}
    </div>
  )
}
