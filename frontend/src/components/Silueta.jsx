import React from 'react'
import celebracion from '../assets/siluetas/celebracion.png'
import celebracionEspalda from '../assets/siluetas/celebracion_espalda.png'
import cabezazo from '../assets/siluetas/cabezazo.png'
import remate from '../assets/siluetas/remate.png'
import duelo from '../assets/siluetas/duelo.png'

// Siluetas de jugadores usadas como mascara: toman el color del texto (currentColor),
// asi se pintan con los colores de la marca desde CSS.
export const SILUETAS = { celebracion, celebracionEspalda, cabezazo, remate, duelo }

export default function Silueta({ name, className = '', style }) {
  const src = SILUETAS[name]
  return <span aria-hidden="true" className={'sil ' + className}
    style={{ WebkitMaskImage: `url(${src})`, maskImage: `url(${src})`, ...style }} />
}
