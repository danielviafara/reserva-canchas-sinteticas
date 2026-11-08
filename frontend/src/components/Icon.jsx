import React from 'react'

const BASE = {
  viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor',
  strokeWidth: 1.75, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true,
}

const PATHS = {
  pitch: <><rect x="3" y="4.5" width="18" height="15" rx="2.5" /><path d="M12 4.5v15" /><circle cx="12" cy="12" r="2.4" /></>,
  calendar: <><rect x="3.5" y="5" width="17" height="15.5" rx="3" /><path d="M3.5 9.5h17M8 2.5v4M16 2.5v4" /></>,
  ticket: <><path d="M4 8.5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2 2 2 0 0 0 0 4v1a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-1a2 2 0 0 0 0-4z" /><path d="M14 6.8v10.4" /></>,
  shield: <><path d="M12 3l7 3v5c0 4.6-3 7.6-7 9-4-1.4-7-4.4-7-9V6z" /><path d="M9.3 12l1.9 1.9 3.5-4" /></>,
  clock: <><circle cx="12" cy="12" r="8.5" /><path d="M12 7.3V12l3 1.8" /></>,
  check: <><circle cx="12" cy="12" r="8.5" /><path d="M8.4 12.2l2.3 2.3 4.9-5" /></>,
  x: <><circle cx="12" cy="12" r="8.5" /><path d="M9.2 9.2l5.6 5.6M14.8 9.2l-5.6 5.6" /></>,
  phone: <><path d="M5 4.5h3L9.5 8.5 7.7 10a11 11 0 0 0 4.8 4.8l1.5-1.8 4 1.5v3a2 2 0 0 1-2.2 2A15.5 15.5 0 0 1 3 6.7 2 2 0 0 1 5 4.5z" /></>,
  mail: <><rect x="3" y="5.5" width="18" height="13" rx="2.5" /><path d="M3.6 7.6l8.4 5.6 8.4-5.6" /></>,
  logout: <><path d="M14 4.5H7.5a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2H14" /><path d="M16 12H9.7M13.8 8.7l3.3 3.3-3.3 3.3" /></>,
  plus: <><circle cx="12" cy="12" r="8.5" /><path d="M12 8.5v7M8.5 12h7" /></>,
  bolt: <><path d="M13.5 3l-7.5 10.5h5l-1 7.5 7.5-10.5h-5z" /></>,
}

export default function Icon({ name, size = 18 }) {
  return <svg {...BASE} width={size} height={size}>{PATHS[name] || null}</svg>
}
