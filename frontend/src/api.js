// Capa de acceso a la API. La app nunca es la fuente de verdad: siempre consulta al backend.
const BASE = import.meta.env.VITE_API_URL || '/api'

function token() { return localStorage.getItem('goltime_token') }

async function req(path, { method = 'GET', body, auth = false } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (auth && token()) headers['Authorization'] = 'Bearer ' + token()
  const res = await fetch(BASE + path, { method, headers, body: body ? JSON.stringify(body) : undefined })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw { status: res.status, detail: data.detail || 'Error' }
  return data
}

export const api = {
  register: (nombre, email, password) => req('/auth/register', { method: 'POST', body: { nombre, email, password } }),
  login: (email, password) => req('/auth/login', { method: 'POST', body: { email, password } }),
  canchas: () => req('/canchas'),
  disponibilidad: (cancha_id, fecha) => req(`/disponibilidad?cancha_id=${cancha_id}&fecha=${fecha}`),
  reservar: (cancha_id, franja_id, fecha) => req('/reservas', { method: 'POST', auth: true, body: { cancha_id, franja_id, fecha } }),
  misReservas: () => req('/reservas', { auth: true }),
  cancelar: (id) => req(`/reservas/${id}/cancelar`, { method: 'POST', auth: true }),
}
