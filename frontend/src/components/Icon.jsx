import React from 'react'

// Iconos de linea minimalistas (24x24, trazo 1.6). Todos heredan el color del texto.
const BASE = {
  viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor',
  strokeWidth: 1.6, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true,
}

const PATHS = {
  // deporte
  ball: <><circle cx="12" cy="12" r="9" /><path d="M12 7.6l3.6 2.6-1.4 4.2H9.8l-1.4-4.2z" /><path d="M12 3v4.6M15.6 10.2l4.9-1.6M14.2 14.4l2.9 4.1M9.8 14.4l-2.9 4.1M8.4 10.2L3.5 8.6" /></>,
  pitch: <><rect x="2.5" y="5" width="19" height="14" rx="1.5" /><path d="M12 5v14" /><circle cx="12" cy="12" r="2.6" /><path d="M2.5 9.5h2.5v5H2.5M21.5 9.5H19v5h2.5" /></>,
  goal: <><path d="M3 19V6h18v13" /><path d="M3 10h18M3 14h18M8 6v13M12 6v13M16 6v13" opacity=".45" /></>,
  whistle: <><path d="M3 11.5a5.5 5.5 0 1 0 9.9 3.3L21 11V8h-9.6A5.5 5.5 0 0 0 3 11.5z" /><circle cx="8.5" cy="13" r="1.4" /><path d="M14 5V3" /></>,
  boot: <><path d="M4 6h5l1 4 9 2.6a2 2 0 0 1 1.4 1.9V17H4z" /><path d="M4 17v1.5M8 17v1.5M12 17v1.5M16 17v1.5M9.6 10.6l-1.2 2M13 11.5l-1 2" /></>,
  jersey: <><path d="M8 3.5l-4.5 2.2 1.6 4.3 2-.8V20.5h9.8V9.2l2 .8 1.6-4.3L16 3.5c-.6 1.4-2.1 2.3-4 2.3s-3.4-.9-4-2.3z" /></>,
  trophy: <><path d="M7.5 4h9v4.5a4.5 4.5 0 0 1-9 0z" /><path d="M7.5 6H4.5a3 3 0 0 0 3 3.5M16.5 6h3a3 3 0 0 1-3 3.5M12 13v4M8.5 20.5h7M9.5 17h5v3.5h-5z" /></>,
  stopwatch: <><circle cx="12" cy="13.5" r="7.5" /><path d="M12 13.5V10M10 2.5h4M12 2.5V6M18.4 7.2l1.4-1.4" /></>,
  flood: <><path d="M6 21l3-9M18 21l-3-9" /><rect x="5" y="3" width="14" height="6" rx="1.2" /><path d="M8 6h.01M12 6h.01M16 6h.01" /></>,
  // ui
  calendar: <><rect x="3.5" y="5" width="17" height="15.5" rx="2" /><path d="M3.5 9.5h17M8 2.5v4M16 2.5v4" /></>,
  ticket: <><path d="M4 7.5a1.5 1.5 0 0 1 1.5-1.5h13A1.5 1.5 0 0 1 20 7.5v2a2.5 2.5 0 0 0 0 5v2a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 16.5v-2a2.5 2.5 0 0 0 0-5z" /><path d="M14.5 6v12" strokeDasharray="1.6 2" /></>,
  shield: <><path d="M12 3l7 3v5c0 4.6-3 7.6-7 9-4-1.4-7-4.4-7-9V6z" /><path d="M9.3 12l1.9 1.9 3.5-4" /></>,
  clock: <><circle cx="12" cy="12" r="8.5" /><path d="M12 7.3V12l3 1.8" /></>,
  check: <><path d="M5 12.5l4.5 4.5L19 7.5" /></>,
  x: <><path d="M6.5 6.5l11 11M17.5 6.5l-11 11" /></>,
  phone: <><path d="M5 4.5h3L9.5 8.5 7.7 10a11 11 0 0 0 4.8 4.8l1.5-1.8 4 1.5v3a2 2 0 0 1-2.2 2A15.5 15.5 0 0 1 3 6.7 2 2 0 0 1 5 4.5z" /></>,
  mail: <><rect x="3" y="5.5" width="18" height="13" rx="2" /><path d="M3.6 7.6l8.4 5.6 8.4-5.6" /></>,
  user: <><circle cx="12" cy="8.5" r="3.8" /><path d="M4.5 20.5a7.5 7.5 0 0 1 15 0" /></>,
  users: <><circle cx="9" cy="8.5" r="3.4" /><path d="M2.8 20a6.2 6.2 0 0 1 12.4 0M15.5 5.3a3.4 3.4 0 0 1 0 6.4M18 14.2a6.2 6.2 0 0 1 3.2 5.8" /></>,
  logout: <><path d="M14 4.5H7.5a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2H14" /><path d="M16 12H9.7M13.8 8.7l3.3 3.3-3.3 3.3" /></>,
  plus: <><path d="M12 5v14M5 12h14" /></>,
  bolt: <><path d="M13.5 3l-7.5 10.5h5l-1 7.5 7.5-10.5h-5z" /></>,
  arrow: <><path d="M4.5 12h15M13.5 6l6 6-6 6" /></>,
  chevron: <><path d="M6 9.5l6 6 6-6" /></>,
  search: <><circle cx="11" cy="11" r="6.5" /><path d="M20 20l-4.4-4.4" /></>,
  info: <><circle cx="12" cy="12" r="8.5" /><path d="M12 11v5.5M12 7.8h.01" /></>,
  pin: <><path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z" /><circle cx="12" cy="10" r="2.4" /></>,
  // ia / datos
  spark: <><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" /><path d="M19 15.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z" /></>,
  brain: <><path d="M9 4.5a3 3 0 0 0-3 3 3 3 0 0 0-1.5 5.3A3 3 0 0 0 7.5 17a2.5 2.5 0 0 0 4.5 1.5V6a2.5 2.5 0 0 0-3-1.5zM15 4.5a3 3 0 0 1 3 3 3 3 0 0 1 1.5 5.3 3 3 0 0 1-3 4.2 2.5 2.5 0 0 1-4.5 1.5" /></>,
  chart: <><path d="M4 20V4M4 20h16" /><path d="M8 16v-4M12 16V8M16 16v-6M20 16v-9" /></>,
  trend: <><path d="M3.5 17l5.5-5.5 4 4L20.5 8" /><path d="M15 8h5.5v5.5" /></>,
  flame: <><path d="M12 21c-3.9 0-6.5-2.6-6.5-6.2 0-3.4 2.6-5.3 3.5-8.3 1 1.3 1.6 2.7 1.6 4 1.5-1 2.9-3.4 2.9-6.5 3.2 2.4 5 6.2 5 9.8C18.5 18.4 15.9 21 12 21z" /></>,
  layers: <><path d="M12 3.5l8.5 4.5-8.5 4.5L3.5 8z" /><path d="M3.5 12l8.5 4.5 8.5-4.5M3.5 16l8.5 4.5 8.5-4.5" /></>,
}

export default function Icon({ name, size = 18, className }) {
  return <svg {...BASE} width={size} height={size} className={className}>{PATHS[name] || null}</svg>
}
