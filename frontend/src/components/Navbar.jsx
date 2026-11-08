import React from 'react'
import Icon from './Icon.jsx'

export default function Navbar({ usuario, vista, setVista, onLogout }) {
  const inicial = (usuario.nombre || 'U').trim().charAt(0).toUpperCase()
  const esAdmin = usuario.rol === 'admin'
  return (
    <nav className="nav">
      <div className="brand"><span className="mark"><Icon name="pitch" size={19} /></span>Gol<em>Time</em></div>
      <div className="tabs">
        <button className={'tab' + (vista === 'disponibilidad' ? ' active' : '')} onClick={() => setVista('disponibilidad')}>
          <Icon name="calendar" size={16} />Disponibilidad</button>
        {!esAdmin &&
          <button className={'tab' + (vista === 'mis' ? ' active' : '')} onClick={() => setVista('mis')}>
            <Icon name="ticket" size={16} />Mis reservas</button>}
        {esAdmin &&
          <button className={'tab' + (vista === 'admin' ? ' active' : '')} onClick={() => setVista('admin')}>
            <Icon name="shield" size={16} />Administración</button>}
      </div>
      <div className="spacer" />
      <div className="user"><span className="av">{inicial}</span><span className="txt">Hola, <span className="muted">{usuario.nombre}</span></span></div>
      <button className="btn ghost sm" onClick={onLogout}><Icon name="logout" size={15} />Salir</button>
    </nav>
  )
}
