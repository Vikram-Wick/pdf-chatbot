const dropArea = document.getElementById('dropArea')
const fileInput = document.getElementById('fileInput')
const progressBar = document.getElementById('progressBar')
const uploadStatus = document.getElementById('uploadStatus')
const chatWindow = document.getElementById('chatWindow')
const thinking = document.getElementById('thinking')
const questionInput = document.getElementById('questionInput')
const sendBtn = document.getElementById('sendBtn')
const clearBtn = document.getElementById('clearBtn')
const readyBadge = document.getElementById('readyBadge')
const themeToggle = document.getElementById('themeToggle')

function appendMessage(role, content, citations = []) {
  const msg = document.createElement('div')
  msg.className = `message ${role}`
  const bubble = document.createElement('div')
  bubble.className = 'bubble'
  bubble.innerHTML = marked.parse(content)
  msg.appendChild(bubble)

  if (role === 'bot' && citations && citations.length) {
    const cite = document.createElement('div')
    cite.className = 'citations'
    cite.textContent = 'Sources: '
    citations.forEach((c) => {
      const span = document.createElement('span')
      span.className = 'citation'
      span.textContent = `${c.source || 'PDF'} p.${c.page || '?'}`
      cite.appendChild(span)
    })
    bubble.appendChild(cite)
  }

  chatWindow.appendChild(msg)
  chatWindow.scrollTop = chatWindow.scrollHeight
}

function setThinking(visible) {
  thinking.classList.toggle('hidden', !visible)
}

function setReady(ready) {
  readyBadge.textContent = ready ? 'Ready to chat!' : 'Upload PDFs to start'
}

async function uploadFiles(files) {
  if (!files || !files.length) return
  uploadStatus.textContent = 'Uploading...'
  progressBar.style.width = '20%'

  const form = new FormData()
  Array.from(files).forEach((f) => form.append('files', f))

  try {
    const res = await fetch('/upload', { method: 'POST', body: form })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Upload failed')

    progressBar.style.width = '100%'
    uploadStatus.textContent = `${data.message} Processed ${data.pages} pages.`
    setReady(true)
    appendMessage('bot', 'Your documents are processed. Ask me anything!')
  } catch (e) {
    progressBar.style.width = '0%'
    uploadStatus.textContent = `Error: ${e.message}`
    setReady(false)
  }
}

async function sendMessage() {
  const q = questionInput.value.trim()
  if (!q) return

  appendMessage('user', q)
  questionInput.value = ''
  sendBtn.disabled = true
  setThinking(true)

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Chat error')

    appendMessage('bot', data.answer, data.citations || [])
  } catch (e) {
    appendMessage('bot', `Sorry, I had trouble: ${e.message}`)
  } finally {
    sendBtn.disabled = false
    setThinking(false)
  }
}

async function loadHistory() {
  try {
    const res = await fetch('/history')
    const data = await res.json()
    ;(data.history || []).forEach((msg) => {
      appendMessage(
        msg.role === 'assistant' ? 'bot' : 'user',
        msg.content,
        msg.citations || []
      )
    })
  } catch (_) {
    /* ignore */
  }
}

async function clearChat() {
  try {
    const res = await fetch('/clear', { method: 'POST' })
    await res.json()
    chatWindow.innerHTML = ''
    setReady(false)
    progressBar.style.width = '0%'
    uploadStatus.textContent = ''
  } catch (_) {
    /* ignore */
  }
}

// Drag & drop handlers
;['dragenter', 'dragover'].forEach((evt) => {
  dropArea.addEventListener(evt, (e) => {
    e.preventDefault()
    dropArea.classList.add('hover')
  })
})
;['dragleave', 'drop'].forEach((evt) => {
  dropArea.addEventListener(evt, (e) => {
    e.preventDefault()
    dropArea.classList.remove('hover')
  })
})

dropArea.addEventListener('click', () => fileInput.click())
dropArea.addEventListener('drop', (e) => uploadFiles(e.dataTransfer.files))
fileInput.addEventListener('change', (e) => uploadFiles(e.target.files))

sendBtn.addEventListener('click', sendMessage)
questionInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendMessage()
})
clearBtn.addEventListener('click', clearChat)

// Theme toggle
function updateTheme() {
  const mode = localStorage.getItem('theme') || 'light'
  document.body.classList.toggle('dark', mode === 'dark')
}
updateTheme()
themeToggle.addEventListener('click', () => {
  const mode = document.body.classList.contains('dark') ? 'light' : 'dark'
  localStorage.setItem('theme', mode)
  updateTheme()
})

// Initialize
loadHistory()
