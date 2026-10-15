import React from 'react'

export default function Navbar({ usuario, vista, setVista, onLogout }) {
  return (
    <nav className="nav">
      <div className="brand">Gol<span>Time</span></div>
      <div className="tabs">
        <button className={'tab' + (vista === 'disponibilidad' ? ' active' : '')} onClick={() => setVista('disponibilidad')}>Disponibilidad</button>
        <button className={'tab' + (vista === 'mis' ? ' active' : '')} onClick={() => setVista('mis')}>Mis reservas</button>
      </div>
      <div className="spacer" />
      <span className="who">Hola, {usuario.nombre}</span>
      <button className="btn ghost sm" onClick={onLogout}>Salir</button>
    </nav>
  )
}
