
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

async function handleResponse(response) {
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const detail = data.detail
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg).join(', ')
      : detail

    throw new Error(
      message || `Request failed with status ${response.status}`
    )
  }

  return data
}

export async function askAdvisor(question) {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question }),
  })

  return handleResponse(response)
}

export async function uploadDocument(file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    const formData = new FormData()

    formData.append('file', file)

    xhr.open('POST', `${API_BASE_URL}/api/documents/upload`)

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
