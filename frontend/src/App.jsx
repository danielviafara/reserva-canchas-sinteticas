import React, { useState } from 'react'
import Auth from './components/Auth.jsx'
import Navbar from './components/Navbar.jsx'
import Disponibilidad from './components/Disponibilidad.jsx'
import MisReservas from './components/MisReservas.jsx'

function leerUsuario() {
  try { return JSON.parse(localStorage.getItem('goltime_user')) } catch { return null }
}

export default function App() {
  const [usuario, setUsuario] = useState(leerUsuario())
  const [vista, setVista] = useState('disponibilidad')

  function onLogin(u) { localStorage.setItem('goltime_user', JSON.stringify(u)); setUsuario(u) }
  function onLogout() { localStorage.removeItem('goltime_token'); localStorage.removeItem('goltime_user'); setUsuario(null) }

  if (!usuario) return <div className="container"><Auth onLogin={onLogin} /></div>

  return (
    <div className="container">
      <Navbar usuario={usuario} vista={vista} setVista={setVista} onLogout={onLogout} />
      {vista === 'disponibilidad' ? <Disponibilidad /> : <MisReservas />}
    </div>
  )
}
