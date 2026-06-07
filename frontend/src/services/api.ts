const BASE = 'http://localhost:8000/api/v1'

export async function sendMessage(userId: number, message: string) {
  const res = await fetch(`${BASE}/profile/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, message }),
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export function streamChat(
  userId: number,
  message: string,
  onChunk: (data: any) => void,
  onDone: () => void,
  onError: (err: Error) => void,
) {
  const url = `${BASE}/profile/chat/stream?user_id=${userId}&message=${encodeURIComponent(message)}`
  const eventSource = new EventSource(url)

  eventSource.onmessage = (event) => {
    if (event.data === '[DONE]') {
      eventSource.close()
      onDone()
      return
    }
    try {
      const data = JSON.parse(event.data)
      onChunk(data)
    } catch {
      // ignore parse errors for partial data
    }
  }

  eventSource.onerror = () => {
    eventSource.close()
    onError(new Error('连接中断，请重试'))
  }

  return () => eventSource.close()
}

export async function getProfile(userId: number) {
  const res = await fetch(`${BASE}/profile/${userId}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}
