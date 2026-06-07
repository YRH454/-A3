const BASE = 'http://localhost:8000/api/v1'

// ---- Auth ----
export async function loginApi(email: string, password: string) {
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw await res.json()
  return res.json()
}

export async function registerApi(username: string, email: string, password: string) {
  const res = await fetch(`${BASE}/auth/register`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password }),
  })
  if (!res.ok) throw await res.json()
  return res.json()
}

export async function guestLoginApi() {
  const res = await fetch(`${BASE}/auth/guest`, { method: 'POST' })
  if (!res.ok) throw await res.json()
  return res.json()
}

// ---- Profile ----
export async function startProfile(userId: number, token?: string) {
  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${BASE}/profile/start?user_id=${userId}`, { method: 'POST', headers })
  if (!res.ok) throw new Error(`Start error: ${res.status}`)
  return res.json()
}

export async function sendMessage(userId: number, message: string) {
  const res = await fetch(`${BASE}/profile/chat`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, message }),
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

// ---- SSE stream ----
export function streamChat(
  userId: number, message: string,
  onChunk: (data: any) => void, onDone: () => void, onError: (err: Error) => void,
) {
  const url = `${BASE}/profile/chat/stream?user_id=${userId}&message=${encodeURIComponent(message)}`
  const es = new EventSource(url)
  es.onmessage = (e) => {
    if (e.data === '[DONE]') { es.close(); onDone(); return }
    try { onChunk(JSON.parse(e.data)) } catch { /* ignore */ }
  }
  es.onerror = () => { es.close(); onError(new Error('连接中断')) }
  return () => es.close()
}

export async function getProfile(userId: number) {
  const res = await fetch(`${BASE}/profile/${userId}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}
