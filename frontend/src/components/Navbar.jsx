import React from 'react'
import Icon from './Icon.jsx'

export function Wordmark() {
  return <div className="wordmark"><span className="mk"><Icon name="ball" size={20} /></span><span>Gol<i>Time</i></span></div>
}

export default function Navbar({ usuario, vista, setVista, onLogout }) {
  const inicial = (usuario.nombre || 'U').trim().charAt(0).toUpperCase()
  const esAdmin = usuario.rol === 'admin'
  const items = [
    ['disponibilidad', 'calendar', 'Reservar'],
    ...(esAdmin ? [['admin', 'shield', 'Administración']] : [['mis', 'ticket', 'Mis reservas']]),
  ]
  return (
    <header className="topbar">
      <div className="topbar-in">
        <Wordmark />
        <nav className="nav">
          {items.map(([id, ic, txt]) => (
            <button key={id} className={vista === id ? 'on' : ''} onClick={() => setVista(id)}>
              <Icon name={ic} size={17} /><span>{txt}</span>
            </button>
          ))}
        </nav>
        <div className="grow" />
        <div className="me">
          <span className="av">{inicial}</span>
          <span className="who"><b>{usuario.nombre}</b><span>{esAdmin ? 'Administrador' : 'Jugador'}</span></span>
        </div>
        <button className="icon-btn" onClick={onLogout} title="Cerrar sesión" aria-label="Cerrar sesión"><Icon name="logout" size={17} /></button>
      </div>
    </header>
  )
}
