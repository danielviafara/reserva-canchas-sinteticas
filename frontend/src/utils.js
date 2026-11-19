// Utilidades de fecha en hora LOCAL (toISOString usa UTC y en Colombia, de noche, ya es "mañana").
export const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
export const hoy = () => iso(new Date())
export const parse = (s) => { const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d) }
export const DIAS = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']
export const DIAS_LARGO = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
export const MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
export const proximosDias = (n) => Array.from({ length: n }, (_, i) => { const d = new Date(); d.setDate(d.getDate() + i); return d })
export const yaPaso = (fecha, hora) => new Date(`${fecha}T${hora}`) < new Date()
export const pct = (x) => `${Math.round((x || 0) * 100)}`
export const fechaLarga = (s) => { const d = parse(s); return `${DIAS_LARGO[d.getDay()]} ${d.getDate()} ${MESES[d.getMonth()].toLowerCase()}` }
export const NIVEL = { alta: 'Se llena rápido', media: 'Demanda media', baja: 'Suele estar libre' }
