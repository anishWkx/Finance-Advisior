
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const TOKEN_KEY = 'finwise-access-token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

function authHeaders() {
  const token = getToken()

  return token
    ? { Authorization: `Bearer ${token}` }
    : {}
}

async function handleResponse(response) {
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const detail = data.detail
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg).join(', ')
      : detail

    const error = new Error(
      message || `Request failed with status ${response.status}`
    )
    error.status = response.status
    throw error
  }

  return data
}

export async function registerUser(name, email, password) {
  const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name, email, password }),
  })

  const data = await handleResponse(response)
  saveToken(data.access_token)
  return data
}

export async function loginUser(email, password) {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  })

  const data = await handleResponse(response)
  saveToken(data.access_token)
  return data
}

export async function getCurrentUser() {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 15000)

  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: authHeaders(),
      signal: controller.signal,
    })

    return await handleResponse(response)
  } finally {
    clearTimeout(timeoutId)
  }
}

export async function askAdvisor(question) {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify({ question }),
  })

  return handleResponse(response)
}

export async function getTransactionSummary(documentId) {
  const response = await fetch(
    `${API_BASE_URL}/api/transactions/summary?document_id=${encodeURIComponent(documentId)}`,
    {
      headers: authHeaders(),
    }
  )

  return handleResponse(response)
}

export async function getTransactions(documentId) {
  const response = await fetch(
    `${API_BASE_URL}/api/transactions/?document_id=${encodeURIComponent(documentId)}`,
    {
      headers: authHeaders(),
    }
  )

  return handleResponse(response)
}

export async function getDocuments() {
  const response = await fetch(`${API_BASE_URL}/api/documents/`, {
    headers: authHeaders(),
  })

  return handleResponse(response)
}

export async function uploadDocument(file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    const formData = new FormData()

    formData.append('file', file)

    xhr.open('POST', `${API_BASE_URL}/api/documents/upload`)

    const token = getToken()

    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    }

    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        const percentage = Math.round(
          (event.loaded / event.total) * 100
        )
        onProgress(percentage)
      }
    })

    xhr.addEventListener('load', async () => {
      try {
        const response = {
          ok: xhr.status >= 200 && xhr.status < 300,
          status: xhr.status,
          json: async () => JSON.parse(xhr.responseText || '{}'),
        }

        resolve(await handleResponse(response))
      } catch (error) {
        reject(error)
      }
    })

    xhr.addEventListener('error', () => {
      reject(new Error('Network error while uploading document.'))
    })

    xhr.addEventListener('abort', () => {
      reject(new Error('Document upload was cancelled.'))
    })

    xhr.send(formData)
  })
}
