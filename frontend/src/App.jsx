/* FINWISE_OVERVIEW_V1 */
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, PieChart, Pie, Cell } from 'recharts'

import { useEffect, useRef, useState } from 'react'
import {
  ArrowUpRight,
  BarChart3,
  Bot,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Search,
  CircleHelp,
  FileSpreadsheet,
  FileText,
  LayoutDashboard,
  LoaderCircle,
  MessageSquareText,
  Paperclip,
  Plus,
  Send,
  ShieldCheck,
  Sparkles,
  Upload,
  X,
  Download,
  Copy,
} from 'lucide-react'

import {
  askAdvisor,
  uploadDocument,
  registerUser,
  loginUser,
  getCurrentUser,
  getDocuments,
  getToken,
  clearToken,
  getTransactionSummary,
  getTransactions,
} from './api.js'

function formatInline(text, searchTerm = '') {
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g)

  function highlight(value, keyPrefix) {
    if (!searchTerm.trim()) return value

    const escaped = searchTerm.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const pieces = value.split(new RegExp(`(${escaped})`, 'gi'))

    return pieces.map((piece, index) =>
      piece.toLowerCase() === searchTerm.trim().toLowerCase()
        ? <mark className="search-highlight" key={`${keyPrefix}-${index}`}>{piece}</mark>
        : piece
    )
  }

  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{highlight(part.slice(2, -2), `bold-${index}`)}</strong>
    }

    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={index}>{highlight(part.slice(1, -1), `italic-${index}`)}</em>
    }

    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={index}>{highlight(part.slice(1, -1), `code-${index}`)}</code>
    }

    return <span key={index}>{highlight(part, `plain-${index}`)}</span>
  })
}

function FormattedAnswer({ content, searchTerm = '' }) {
  const lines = content.split('\n')
  const elements = []
  let bulletItems = []
  let pendingBullet = false

  function flushBullets() {
    if (!bulletItems.length) return

    elements.push(
      <ul className="formatted-list" key={`list-${elements.length}`}>
        {bulletItems.map((item, index) => (
          <li key={index}>{formatInline(item, searchTerm)}</li>
        ))}
      </ul>
    )

    bulletItems = []
  }

  lines.forEach((line, index) => {
    const trimmed = line.trim()

    if (!trimmed) {
      flushBullets()
      pendingBullet = false
      return
    }

    if (/^\*\*Finwise advisor\*\*$/i.test(trimmed)) return

    if (/^\*\*([•●▪\-*])\*\*$/.test(trimmed)) {
      flushBullets()
      pendingBullet = true
      return
    }

    const bullet = /^(?:[-*•●▪]\s+)(.*)$/.exec(trimmed)

    if (bullet) {
      bulletItems.push(bullet[1])
      pendingBullet = false
      return
    }

    if (/^###\s/.test(trimmed)) {
      flushBullets()
      pendingBullet = false
      elements.push(
        <h4 key={index}>{formatInline(trimmed.replace(/^###\s+/, ''), searchTerm)}</h4>
      )
      return
    }

    if (/^##\s/.test(trimmed) || /^#\s/.test(trimmed)) {
      flushBullets()
      pendingBullet = false
      elements.push(
        <h3 key={index}>
          {formatInline(trimmed.replace(/^#{1,2}\s+/, ''), searchTerm)}
        </h3>
      )
      return
    }

    const boldOnly = /^\*\*(.+)\*\*$/.exec(trimmed)

    if (boldOnly) {
      flushBullets()
      pendingBullet = false
      elements.push(<h4 key={index}>{boldOnly[1]}</h4>)
      return
    }

    const numbered = /^(\d+)[.)]\s+(.*)$/.exec(trimmed)

    if (numbered) {
      flushBullets()
      pendingBullet = false
      elements.push(
        <div className="answer-list-item" key={index}>
          <span>{numbered[1]}.</span>
          <div>{formatInline(numbered[2], searchTerm)}</div>
        </div>
      )
      return
    }

    if (pendingBullet) {
      bulletItems.push(trimmed)
      pendingBullet = false
      return
    }

    flushBullets()
    elements.push(<p key={index}>{formatInline(trimmed, searchTerm)}</p>)
  })

  flushBullets()

  return <div className="formatted-answer">{elements}</div>
}

function cleanSourceName(value) {
  if (!value) return 'Uploaded document'

  return String(value)
    .replace(/^svg(?=[A-Za-z0-9])/i, '')
    .replace(/^sources?\s*/i, '')
    .trim()
}

function getSourceDetails(source) {
  if (typeof source === 'string') {
    return { name: cleanSourceName(source), page: '' }
  }

  return {
    name: cleanSourceName(
      source?.filename ||
      source?.file_name ||
      source?.source ||
      source?.name ||
      source?.document ||
      'Uploaded document'
    ),
    page: (source?.page || source?.page_number)
      ? `Page ${source.page || source.page_number}`
      : '',
  }
}

function SourceList({ sources }) {
  if (!Array.isArray(sources) || sources.length === 0) return null

  return (
    <div className="sources">
      <span className="sources-label">SOURCES</span>
      {sources.map((source, index) => {
        const details = getSourceDetails(source)

        return (
          <span className="source-pill" key={index}>
            <FileText size={11} />
            {details.name}
            {details.page && <b>{details.page}</b>}
          </span>
        )
      })}
    </div>
  )
}

function formatAmount(value) {
  if (value === null || value === undefined || value === '') return '—'

  const amount = Number(value)
  if (!Number.isFinite(amount)) return String(value)

  return amount.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

const transactionCellStyle = {
  padding: '10px 8px',
  color: '#475467',
  borderBottom: '1px solid #eef0f4',
  whiteSpace: 'nowrap',
}

function App() {
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [chatSearch, setChatSearch] = useState('')
  const [searchMatchIndex, setSearchMatchIndex] = useState(0)
  const [busy, setBusy] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadStage, setUploadStage] = useState('')
  const [notice, setNotice] = useState('')
  const [documentSearch, setDocumentSearch] = useState('')
  const [selectedDocument, setSelectedDocument] = useState(null)
  const [copiedMessage, setCopiedMessage] = useState(null)
  const [documents, setDocuments] = useState([])
  const [activeNav, setActiveNav] = useState('overview')
  const [user, setUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [authMode, setAuthMode] = useState('login')
  const [authName, setAuthName] = useState('')
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authError, setAuthError] = useState('')
  const [authSubmitting, setAuthSubmitting] = useState(false)
  const [historyUserId, setHistoryUserId] = useState(null)

  const [transactionAnalytics, setTransactionAnalytics] = useState(null)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)
  const [analyticsError, setAnalyticsError] = useState('')

  const [transactionHistory, setTransactionHistory] = useState([])
  const [transactionsLoading, setTransactionsLoading] = useState(false)
  const [transactionsError, setTransactionsError] = useState('')

  const fileInput = useRef(null)
  const questionInput = useRef(null)
  const chatEnd = useRef(null)

  const totalDocumentChunks = documents.reduce(
    (total, doc) => total + (Number(doc.chunks) || 0),
    0
  )

  const totalStorageBytes = documents.reduce((total, doc) => {
    const match = String(doc.size || '').match(/^([\d.]+)\s*(B|KB|MB|GB)$/i)
    if (!match) return total

    const amount = Number(match[1])
    const unit = match[2].toUpperCase()
    const multiplier = { B: 1, KB: 1024, MB: 1024 ** 2, GB: 1024 ** 3 }

    return total + amount * multiplier[unit]
  }, 0)

  const totalStorageLabel = totalStorageBytes >= 1024 ** 3
    ? `${(totalStorageBytes / (1024 ** 3)).toFixed(2)} GB`
    : totalStorageBytes >= 1024 ** 2
      ? `${(totalStorageBytes / (1024 ** 2)).toFixed(1)} MB`
      : totalStorageBytes >= 1024
        ? `${(totalStorageBytes / 1024).toFixed(1)} KB`
        : `${totalStorageBytes} B`

  const filteredMessages = messages
    .map((message, index) => ({ message, index }))
    .filter(({ message }) =>
      !chatSearch.trim() ||
      (message.content || '').toLowerCase().includes(chatSearch.trim().toLowerCase())
    )

  const filteredDocuments = documents.filter((doc) =>
    doc.name.toLowerCase().includes(documentSearch.trim().toLowerCase())
  )

  useEffect(() => {
    if (!getToken()) {
      setAuthLoading(false)
      return
    }

    getCurrentUser()
      .then(setUser)
      .catch(() => {
        clearToken()
        setUser(null)
      })
      .finally(() => setAuthLoading(false))
  }, [])

  useEffect(() => {
    if (!user?.id) return

    let cancelled = false
    const chatKey = `finwise-chat-history:${user.id}`
    const documentsKey = `finwise-recent-documents:${user.id}`

    try {
      setMessages(JSON.parse(localStorage.getItem(chatKey) || '[]'))
      setDocuments(JSON.parse(localStorage.getItem(documentsKey) || '[]'))
    } catch {
      setMessages([])
      setDocuments([])
    }

    setHistoryUserId(user.id)

    getDocuments()
      .then((result) => {
        if (cancelled) return

        const serverDocuments = (result.documents || []).map((document) => ({
          documentId: document.document_id,
          name: document.name,
          fileType: document.file_type,
          createdAt: document.created_at,
          size: formatFileSize(document.file_size_bytes || 0),
          chunks: document.chunk_count || 0,
          status: 'Processed',
        }))

        setDocuments(serverDocuments)
      })
      .catch((error) => {
        console.warn('Could not load documents from server:', error)
      })

    return () => {
      cancelled = true
    }
  }, [user?.id])

  useEffect(() => {
    if (!user?.id || historyUserId !== user.id) return

    localStorage.setItem(
      `finwise-recent-documents:${user.id}`,
      JSON.stringify(documents)
    )
  }, [documents, historyUserId, user?.id])

  useEffect(() => {
    if (!user?.id || historyUserId !== user.id) return

    try {
      localStorage.setItem(
        `finwise-chat-history:${user.id}`,
        JSON.stringify(messages)
      )
    } catch (error) {
      console.warn('Could not save chat history:', error)
      setNotice('Chat history could not be saved. Browser storage may be full.')
    }
  }, [messages, historyUserId, user?.id])

  // Load financial analytics for the selected document.
  useEffect(() => {
    const documentId = selectedDocument?.documentId

    if (!documentId) {
      setTransactionAnalytics(null)
      setAnalyticsError('')
      setAnalyticsLoading(false)
      return
    }

    let cancelled = false

    async function loadAnalytics() {
      setAnalyticsLoading(true)
      setAnalyticsError('')
      setTransactionAnalytics(null)

      try {
        const result = await getTransactionSummary(documentId)
        if (!cancelled) setTransactionAnalytics(result)
      } catch (error) {
        if (!cancelled) {
          setAnalyticsError(error.message || 'Could not load financial analytics.')
        }
      } finally {
        if (!cancelled) setAnalyticsLoading(false)
      }
    }

    loadAnalytics()

    return () => {
      cancelled = true
    }
  }, [selectedDocument?.documentId])

  // Load transaction history for the selected document.
  useEffect(() => {
    const documentId = selectedDocument?.documentId

    if (!documentId) {
      setTransactionHistory([])
      setTransactionsError('')
      setTransactionsLoading(false)
      return
    }

    let cancelled = false

    async function loadTransactions() {
      setTransactionsLoading(true)
      setTransactionsError('')
      setTransactionHistory([])

      try {
        const result = await getTransactions(documentId)
        if (!cancelled) {
          setTransactionHistory(result.transactions || [])
        }
      } catch (error) {
        if (!cancelled) {
          setTransactionsError(error.message || 'Could not load transaction history.')
        }
      } finally {
        if (!cancelled) setTransactionsLoading(false)
      }
    }

    loadTransactions()

    return () => {
      cancelled = true
    }
  }, [selectedDocument?.documentId])

  useEffect(() => {
    const input = questionInput.current
    if (!input) return

    input.style.height = 'auto'
    const height = Math.min(input.scrollHeight, 140)
    input.style.height = `${height}px`
    input.style.overflowY = input.scrollHeight > 140 ? 'auto' : 'hidden'
  }, [question])

  function navigateTo(section) {
    setActiveNav(section)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function sendQuestion(value = question) {
    const text = value.trim()
    if (!text || busy) return

    setQuestion('')
    setNotice('')

    setMessages((previous) => [
      ...previous,
      { role: 'user', content: text, timestamp: new Date().toISOString() },
    ])

    setBusy(true)

    setTimeout(() => {
      chatEnd.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }, 50)

    try {
      const response = await askAdvisor(text)

      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          content: response.answer || 'I could not generate an answer. Please try again.',
          sources: response.sources || [],
          timestamp: new Date().toISOString(),
        },
      ])
    } catch (error) {
      setNotice(error.message || 'Unable to connect to the advisor.')

      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          content: 'I could not process your question right now. Please check that the backend server is running and try again.',
          sources: [],
        },
      ])
    } finally {
      setBusy(false)
      setTimeout(() => chatEnd.current?.scrollIntoView({ behavior: 'smooth' }), 100)
    }
  }

  function formatFileSize(bytes) {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  async function handleFiles(fileList) {
    const selectedFiles = Array.from(fileList || [])
    if (!selectedFiles.length || uploading) return

    const allowedExtensions = ['pdf', 'csv', 'xlsx']

    for (const file of selectedFiles) {
      const extension = file.name.split('.').pop().toLowerCase()

      if (!allowedExtensions.includes(extension)) {
        setNotice(`Unsupported file: ${file.name}. Upload PDF, CSV or XLSX.`)
        continue
      }

      setUploading(true)
      setUploadProgress(0)
      setUploadStage('Uploading file...')
      setNotice('')

      try {
        const response = await uploadDocument(file, (percentage) => {
          setUploadProgress(percentage)
          if (percentage >= 100) setUploadStage('Processing document...')
        })

        const uploadedDocument = {
          documentId: response.document_id,
          name: file.name,
          size: formatFileSize(file.size),
          status: 'Uploaded',
          chunks: response.total_chunks ??
            response.chunks_created ??
            response.chunks ??
            null,
        }

        setDocuments((previous) => [
          uploadedDocument,
          ...previous.filter((doc) => doc.name !== file.name),
        ])

        setSelectedDocument(uploadedDocument)
        setNotice(`${file.name} uploaded successfully.`)
      } catch (error) {
        setNotice(`Upload failed: ${error.message}`)
      } finally {
        setUploading(false)
        setUploadProgress(0)
        setUploadStage('')
      }
    }

    if (fileInput.current) fileInput.current.value = ''
  }

  function handleDrop(event) {
    event.preventDefault()
    handleFiles(event.dataTransfer.files)
  }

  async function handleCopyAnswer(content, index) {
    try {
      await navigator.clipboard.writeText(content || '')
      setCopiedMessage(index)
    } catch {
      setNotice('Could not copy answer. Please try selecting the text manually.')
    }
  }

  function downloadSources() {
    if (busy) return

    const uniqueSources = new Map()

    messages.forEach((message) => {
      if (message.role !== 'assistant' || !Array.isArray(message.sources)) return

      message.sources.forEach((source) => {
        const details = getSourceDetails(source)
        const key = `${details.name.toLowerCase()}|${details.page.toLowerCase()}`
        if (!uniqueSources.has(key)) uniqueSources.set(key, details)
      })
    })

    if (!uniqueSources.size) {
      setNotice('No source references are available in this conversation.')
      return
    }

    const content = [
      'FINWISE - EXPORTED SOURCE REFERENCES',
      `Exported: ${new Date().toLocaleString()}`,
      '='.repeat(50),
      '',
      ...Array.from(uniqueSources.values()).map((source, index) =>
        `${index + 1}. ${source.name}${source.page ? ` - ${source.page}` : ''}`
      ),
      '',
      `Total unique references: ${uniqueSources.size}`,
    ].join('\n')

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `finwise-sources-${new Date().toISOString().slice(0, 10)}.txt`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  function downloadConversation() {
    if (!messages.length || busy) return

    const conversation = messages.map((message) => {
      const role = message.role === 'user' ? 'YOU' : 'FINWISE ADVISOR'
      const sources = (message.sources || []).map((source, index) => {
        const name = source.name || source.filename || source.source ||
          source.file_name || `Source ${index + 1}`
        const page = source.page || source.page_number
        return `  - ${name}${page ? ` (Page ${page})` : ''}`
      })

      return [
        `${role}:`,
        message.content || '',
        ...(sources.length ? ['Sources:', ...sources] : []),
      ].join('\n')
    }).join('\n\n' + '='.repeat(55) + '\n\n')

    const content = [
      'FINWISE - FINANCIAL ADVISOR CONVERSATION',
      `Exported: ${new Date().toLocaleString()}`,
      '='.repeat(55),
      '',
      conversation,
    ].join('\n')

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `finwise-chat-${new Date().toISOString().slice(0, 10)}.txt`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  async function handleAuthSubmit(event) {
    event.preventDefault()
    setAuthError('')
    setAuthSubmitting(true)

    try {
      const result = authMode === 'register'
        ? await registerUser(authName, authEmail, authPassword)
        : await loginUser(authEmail, authPassword)

      setUser(result.user)
      setAuthPassword('')
    } catch (error) {
      setAuthError(error.message || 'Authentication failed. Please try again.')
    } finally {
      setAuthSubmitting(false)
    }
  }

  function handleLogout() {
    clearToken()
    setUser(null)
    setHistoryUserId(null)
    setMessages([])
    setDocuments([])
    setSelectedDocument(null)
    setTransactionAnalytics(null)
    setTransactionHistory([])
    setAnalyticsError('')
    setTransactionsError('')
    setQuestion('')
    setActiveNav('overview')
  }

  const financialSummary = transactionAnalytics?.summary

  const cashFlowChartData = financialSummary ? [
    { name: 'Deposits', amount: Number(financialSummary.total_deposits) || 0 },
    { name: 'Withdrawals', amount: Number(financialSummary.total_withdrawals) || 0 },
  ] : []

  const spendingChartData = Object.entries(
    transactionAnalytics?.spending_by_category || {}
  ).map(([name, amount]) => ({
    name,
    amount: Number(amount) || 0,
  })).filter(item => item.amount > 0)

  const chartCurrency = value =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(Number(value) || 0)

  const prompts = [
    'Explain the different stages of business financing.',
    'What is the difference between debt and equity financing?',
    'Explain venture capital in simple terms.',
  ]

  if (authLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: '#f7f8fc', color: '#334155' }}>
        Checking your Finwise session...
      </div>
    )
  }

  if (!user) {
    const fieldStyle = {
      width: '100%',
      boxSizing: 'border-box',
      padding: '13px 14px',
      border: '1px solid #dce1ea',
      borderRadius: '9px',
      fontSize: '14px',
      background: '#fff',
    }

    return (
      <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: '24px', background: '#f7f8fc', fontFamily: 'Inter, sans-serif' }}>
        <form onSubmit={handleAuthSubmit} style={{ width: '100%', maxWidth: '410px', boxSizing: 'border-box', padding: '36px', borderRadius: '18px', background: '#fff', border: '1px solid #e8ebf2', boxShadow: '0 12px 40px rgba(20,30,60,.07)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '30px', fontSize: '25px', fontWeight: 750, color: '#17233c' }}>
            <span style={{ display: 'grid', placeItems: 'center', width: '38px', height: '38px', borderRadius: '10px', background: '#315bea', color: '#fff' }}>
              <BarChart3 size={21} />
            </span>
            Finwise<span style={{ color: '#315bea' }}>.</span>
          </div>

          <h1 style={{ margin: '0 0 8px', fontSize: '25px', color: '#17233c' }}>
            {authMode === 'login' ? 'Welcome back' : 'Create your account'}
          </h1>
          <p style={{ margin: '0 0 25px', color: '#718096', fontSize: '14px', lineHeight: 1.6 }}>
            {authMode === 'login'
              ? 'Sign in to continue to your financial advisor.'
              : 'Create an account to get started with Finwise.'}
          </p>

          {authMode === 'register' && (
            <label style={{ display: 'block', marginBottom: '16px', color: '#344054', fontSize: '13px', fontWeight: 600 }}>
              Full name
              <input required minLength={2} maxLength={80} value={authName} onChange={e => setAuthName(e.target.value)} placeholder="Your name" style={{ ...fieldStyle, marginTop: '7px' }} />
            </label>
          )}

          <label style={{ display: 'block', marginBottom: '16px', color: '#344054', fontSize: '13px', fontWeight: 600 }}>
            Email address
            <input required type="email" value={authEmail} onChange={e => setAuthEmail(e.target.value)} placeholder="you@example.com" style={{ ...fieldStyle, marginTop: '7px' }} />
          </label>

          <label style={{ display: 'block', marginBottom: '18px', color: '#344054', fontSize: '13px', fontWeight: 600 }}>
            Password
            <input required type="password" minLength={authMode === 'register' ? 8 : 1} value={authPassword} onChange={e => setAuthPassword(e.target.value)} placeholder={authMode === 'register' ? 'At least 8 characters' : 'Enter your password'} style={{ ...fieldStyle, marginTop: '7px' }} />
          </label>

          {authError && (
            <p role="alert" style={{ margin: '0 0 16px', color: '#c03939', fontSize: '13px' }}>
              {authError}
            </p>
          )}

          <button type="submit" disabled={authSubmitting} style={{ width: '100%', padding: '13px', border: 0, borderRadius: '9px', background: '#315bea', color: '#fff', fontSize: '14px', fontWeight: 650, cursor: 'pointer', opacity: authSubmitting ? 0.7 : 1 }}>
            {authSubmitting ? 'Please wait...' : authMode === 'login' ? 'Sign in' : 'Create account'}
          </button>

          <p style={{ margin: '22px 0 0', textAlign: 'center', color: '#718096', fontSize: '13px' }}>
            {authMode === 'login' ? "Don't have an account?" : 'Already have an account?'}{' '}
            <button type="button" onClick={() => { setAuthMode(authMode === 'login' ? 'register' : 'login'); setAuthError('') }} style={{ border: 0, background: 'none', color: '#315bea', fontWeight: 650, cursor: 'pointer' }}>
              {authMode === 'login' ? 'Create account' : 'Sign in'}
            </button>
          </p>
        </form>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><BarChart3 size={19} /></div>
          Finwise<span className="brand-dot">.</span>
        </div>

        <div className="workspace-label">WORKSPACE</div>

        <nav className="nav-list">
          <button className={`nav-item ${activeNav === 'overview' ? 'active' : ''}`} onClick={() => navigateTo('overview')}>
            <LayoutDashboard size={17} /> Overview
          </button>
          <button className={`nav-item ${activeNav === 'advisor' ? 'active' : ''}`} onClick={() => navigateTo('advisor')}>
            <MessageSquareText size={17} /> AI Advisor <span className="nav-count">AI</span>
          </button>
          <button className={`nav-item ${activeNav === 'documents' ? 'active' : ''}`} onClick={() => navigateTo('documents')}>
            <FileText size={17} /> Documents
          </button>
        </nav>

        <div className="sidebar-spacer" />

        <div className="privacy-card">
          <div className="privacy-icon"><ShieldCheck size={17} /></div>
          <div>
            <strong>Your data is private</strong>
            <p>Your uploaded documents are used to answer your questions.</p>
          </div>
        </div>

        <div style={{ marginTop: '16px', padding: '12px', border: '1px solid #e8ebf2', borderRadius: '10px' }}>
          <div style={{ fontSize: '13px', fontWeight: 650 }}>{user.name}</div>
          <div style={{ marginTop: '3px', fontSize: '11px', color: '#8792a5', overflowWrap: 'anywhere' }}>{user.email}</div>
          <button type="button" onClick={handleLogout} style={{ marginTop: '10px', padding: '7px 10px', border: '1px solid #e1e5ed', borderRadius: '7px', background: '#fff', cursor: 'pointer', fontSize: '12px' }}>
            Sign out
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span>
            <strong>
              {activeNav === 'overview' ? 'Overview' : activeNav === 'advisor' ? 'AI Advisor' : 'Documents'}
            </strong>
          </div>
          <div className="topbar-right"><span className="today-label">Your financial workspace</span></div>
        </header>

        <div className={`page-wrap page-${activeNav}`} id="overview">
          <section className="welcome-row">
            <div>
              <div className="eyebrow">DOCUMENT INTELLIGENCE DASHBOARD</div>
              <h1>Welcome to Finwise <span className="wave">✳</span></h1>
              <p className="welcome-sub">Your financial documents, insights, and AI-powered advisor.</p>
            </div>
            <button className="outline-button" onClick={() => navigateTo('documents')}>
              <Plus size={16} /> Add documents
            </button>
          </section>

          <section className="stats-grid">
            <div className="stat-card balance-card">
              <div className="stat-top"><span className="stat-label">DOCUMENTS UPLOADED</span><div className="stat-icon"><FileText size={16} /></div></div>
              <div className="stat-value">{documents.length}</div>
              <div className="stat-foot">Files in your workspace</div>
            </div>
            <div className="stat-card">
              <div className="stat-top"><span className="stat-label">PROCESSED CHUNKS</span><div className="stat-icon income"><Sparkles size={16} /></div></div>
              <div className="stat-value">{totalDocumentChunks}</div>
              <div className="stat-foot">Document sections indexed</div>
            </div>
            <div className="stat-card">
              <div className="stat-top"><span className="stat-label">STORAGE USED</span><div className="stat-icon spending"><Upload size={16} /></div></div>
              <div className="stat-value">{totalStorageLabel}</div>
              <div className="stat-foot">Total uploaded file size</div>
            </div>
            <div className="stat-card">
              <div className="stat-top"><span className="stat-label">QUESTIONS ASKED</span><div className="stat-icon savings"><MessageSquareText size={16} /></div></div>
              <div className="stat-value">{messages.filter((message) => message.role === 'user').length}</div>
              <div className="stat-foot">Questions in your chat history</div>
            </div>
          </section>

          {activeNav === 'overview' && (
            <section className="overview-dashboard" id="overview-analytics">
              <div className="overview-section-heading">
                <div>
                  <div className="eyebrow">FINANCIAL OVERVIEW</div>
                  <h2>Your financial snapshot</h2>
                  <p>Insights calculated from your selected financial document.</p>
                </div>
                <label className="overview-document-select">
                  <span>ANALYZE DOCUMENT</span>
                  <select
                    value={selectedDocument?.documentId || ''}
                    onChange={event => {
                      const selected = documents.find(
                        doc => doc.documentId === event.target.value
                      )
                      setSelectedDocument(selected || null)
                    }}
                  >
                    <option value="">Select a document</option>
                    {documents.map((doc, index) => (
                      <option
                        key={doc.documentId || `${doc.name}-${index}`}
                        value={doc.documentId || ''}
                        disabled={!doc.documentId}
                      >
                        {doc.name}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              {!selectedDocument ? (
                <div className="overview-empty">
                  <div className="overview-empty-icon"><BarChart3 size={24} /></div>
                  <h3>Select a financial document</h3>
                  <p>Choose an uploaded statement to view its transaction analytics, cash flow and spending breakdown.</p>
                  <button className="outline-button" onClick={() => navigateTo('documents')}>
                    <Plus size={15} /> Upload or select a document
                  </button>
                </div>
              ) : analyticsLoading ? (
                <div className="overview-empty">
                  <LoaderCircle size={22} className="spin" />
                  <p>Calculating your financial overview...</p>
                </div>
              ) : analyticsError ? (
                <div className="overview-empty">
                  <FileText size={23} />
                  <h3>Analytics unavailable</h3>
                  <p>{analyticsError.toLowerCase().includes('no transactions')
                    ? 'No structured transactions were found. Try selecting another bank statement or re-uploading this document.'
                    : analyticsError}</p>
                </div>
              ) : transactionAnalytics ? (
                <>
                  <div className="overview-kpi-grid">
                    <article className="overview-kpi">
                      <span> TOTAL DEPOSITS </span>
                      <strong className="positive">{formatAmount(financialSummary?.total_deposits)}</strong>
                      <small>Money received</small>
                    </article>
                    <article className="overview-kpi">
                      <span>TOTAL WITHDRAWALS</span>
                      <strong className="negative">{formatAmount(financialSummary?.total_withdrawals)}</strong>
                      <small>Money spent or withdrawn</small>
                    </article>
                    <article className="overview-kpi">
                      <span>NET CASH FLOW</span>
                      <strong className={Number(financialSummary?.net_cash_flow) >= 0 ? 'positive' : 'negative'}>
                        {formatAmount(financialSummary?.net_cash_flow)}
                      </strong>
                      <small>Deposits minus withdrawals</small>
                    </article>
                    <article className="overview-kpi">
                      <span>CLOSING BALANCE</span>
                      <strong>{formatAmount(financialSummary?.closing_balance)}</strong>
                      <small>Ending statement balance</small>
                    </article>
                  </div>

                  <div className="overview-chart-grid">
                    <article className="overview-chart-card">
                      <div className="overview-chart-heading">
                        <div>
                          <h3>Cash flow</h3>
                          <p>Deposits compared with withdrawals</p>
                        </div>
                        <span className="chart-period-label">STATEMENT TOTAL</span>
                      </div>
                      {cashFlowChartData.length ? (
                        <div className="overview-chart">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={cashFlowChartData} margin={{ top: 12, right: 12, left: 4, bottom: 4 }}>
                              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#edf0ed" />
                              <XAxis dataKey="name" axisLine={false} tickLine={false} />
                              <YAxis axisLine={false} tickLine={false} tickFormatter={value => `₹${Number(value).toLocaleString('en-IN')}`} width={78} />
                              <Tooltip formatter={value => chartCurrency(value)} />
                              <Bar dataKey="amount" radius={[6, 6, 0, 0]}>
                                {cashFlowChartData.map((entry, index) => (
                                  <Cell key={entry.name} fill={index === 0 ? '#22966b' : '#d97757'} />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      ) : <p className="chart-empty">No cash flow data available.</p>}
                    </article>

                    <article className="overview-chart-card">
                      <div className="overview-chart-heading">
                        <div>
                          <h3>Spending breakdown</h3>
                          <p>Expenses grouped by transaction category</p>
                        </div>
                      </div>
                      {spendingChartData.length ? (
                        <>
                          <div className="overview-chart overview-donut">
                            <ResponsiveContainer width="100%" height="100%">
                              <PieChart>
                                <Pie
                                  data={spendingChartData}
                                  dataKey="amount"
                                  nameKey="name"
                                  innerRadius="58%"
                                  outerRadius="82%"
                                  paddingAngle={3}
                                >
                                  {spendingChartData.map((entry, index) => (
                                    <Cell
                                      key={entry.name}
                                      fill={['#26966d', '#4779b8', '#e0a34c', '#8b78bd', '#d97757', '#63a5a0'][index % 6]}
                                    />
                                  ))}
                                </Pie>
                                <Tooltip formatter={value => chartCurrency(value)} />
                              </PieChart>
                            </ResponsiveContainer>
                          </div>
                          <div className="overview-category-list">
                            {spendingChartData.map((item, index) => (
                              <div className="overview-category-row" key={item.name}>
                                <span>
                                  <i style={{ background: ['#26966d', '#4779b8', '#e0a34c', '#8b78bd', '#d97757', '#63a5a0'][index % 6] }} />
                                  {item.name}
                                </span>
                                <strong>{formatAmount(item.amount)}</strong>
                              </div>
                            ))}
                          </div>
                        </>
                      ) : <p className="chart-empty">No categorized expenses available.</p>}
                    </article>
                  </div>

                  <div className="overview-balance-row">
                    <div>
                      <span>OPENING BALANCE</span>
                      <strong>{formatAmount(financialSummary?.opening_balance)}</strong>
                    </div>
                    <div>
                      <span>CLOSING BALANCE</span>
                      <strong>{formatAmount(financialSummary?.closing_balance)}</strong>
                    </div>
                    <div>
                      <span>TRANSACTIONS ANALYZED</span>
                      <strong>{financialSummary?.transaction_count ?? 0}</strong>
                    </div>
                  </div>
                  <p className="overview-data-note">
                    Based on {selectedDocument.name}. Spending categories use the current transaction-description keyword rules.
                  </p>
                </>
              ) : (
                <div className="overview-empty">
                  <p>Financial analytics will appear here when available.</p>
                </div>
              )}
            </section>
          )}

          <section className="content-grid">
            <div className="panel chat-panel" id="advisor">
              <div className="panel-heading">
                <div className="advisor-title">
                  <div className="advisor-icon"><Bot size={18} /></div>
                  <div>
                    <h2>AI Financial Advisor</h2>
                    <p>Ask questions about your uploaded financial documents</p>
                  </div>
                </div>

                <div className="chat-header-actions">
                  <button type="button" className="chat-new-button" onClick={() => {
                    if (busy || messages.length === 0) return
                    if (window.confirm('Start a new chat? Your current conversation will be cleared.')) {
                      setMessages([])
                      setQuestion('')
                      setNotice('')
                      setCopiedMessage(null)
                    }
                  }} disabled={busy || messages.length === 0} title="Start a new conversation">
                    <Plus size={13} /> New chat
                  </button>

                  {messages.length > 0 && (
                    <button type="button" className="chat-download-button" onClick={downloadConversation} disabled={busy} title="Download conversation as a text file">
                      <Download size={13} /> Download
                    </button>
                  )}

                  {messages.length > 0 && (
                    <button type="button" className="chat-download-button" onClick={downloadSources} disabled={busy || !messages.some(message => message.role === 'assistant' && Array.isArray(message.sources) && message.sources.length > 0)} title="Export source references">
                      <FileText size={13} /> Export Sources
                    </button>
                  )}

                  {messages.length > 0 && (
                    <button type="button" className="chat-clear-button" onClick={() => {
                      if (busy) return
                      setMessages([])
                      setQuestion('')
                      setNotice('')
                    }} disabled={busy} title="Clear conversation">
                      <X size={13} /> Clear chat
                    </button>
                  )}

                  <div className="online-status"><i /> Ready</div>
                </div>
              </div>

              <div className="chat-body">
                {messages.length > 0 && (
                  <div className="chat-search">
                    <Search size={14} />
                    <input
                      type="search"
                      value={chatSearch}
                      onChange={(event) => {
                        setChatSearch(event.target.value)
                        setSearchMatchIndex(0)
                      }}
                      onKeyDown={(event) => {
                        if (event.key === 'Escape') {
                          setChatSearch('')
                          setSearchMatchIndex(0)
                          event.currentTarget.blur()
                          return
                        }

                        if (event.key === 'Enter' && filteredMessages.length > 0) {
                          event.preventDefault()
                          const nextIndex = event.shiftKey
                            ? (searchMatchIndex - 1 + filteredMessages.length) % filteredMessages.length
                            : (searchMatchIndex + 1) % filteredMessages.length

                          setSearchMatchIndex(nextIndex)
                          requestAnimationFrame(() => {
                            document.querySelectorAll('.message')[nextIndex]?.scrollIntoView({ behavior: 'smooth', block: 'center' })
                          })
                        }
                      }}
                      placeholder="Search questions and answers..."
                      aria-label="Search conversation"
                    />

                    {chatSearch && (
                      <>
                        <span className="chat-search-count">
                          {filteredMessages.length === 0 ? '0 matches' : `${searchMatchIndex + 1} of ${filteredMessages.length}`}
                        </span>
                        <div className="chat-search-navigation">
                          <button type="button" disabled={filteredMessages.length === 0} onClick={() => {
                            const nextIndex = (searchMatchIndex - 1 + filteredMessages.length) % filteredMessages.length
                            setSearchMatchIndex(nextIndex)
                            document.querySelectorAll('.message')[nextIndex]?.scrollIntoView({ behavior: 'smooth', block: 'center' })
                          }} aria-label="Previous matching message" title="Previous match">
                            <ChevronLeft size={14} />
                          </button>
                          <button type="button" disabled={filteredMessages.length === 0} onClick={() => {
                            const nextIndex = (searchMatchIndex + 1) % filteredMessages.length
                            setSearchMatchIndex(nextIndex)
                            document.querySelectorAll('.message')[nextIndex]?.scrollIntoView({ behavior: 'smooth', block: 'center' })
                          }} aria-label="Next matching message" title="Next match">
                            <ChevronRight size={14} />
                          </button>
                        </div>
                        <button type="button" onClick={() => {
                          setChatSearch('')
                          setSearchMatchIndex(0)
                        }} aria-label="Clear conversation search" title="Clear search">
                          <X size={13} />
                        </button>
                      </>
                    )}
                  </div>
                )}

                {messages.length === 0 ? (
                  <div className="chat-empty">
                    <div className="sparkle-badge"><Sparkles size={20} /></div>
                    <h3>How can I help you today?</h3>
                    <p>Ask questions about your financial notes and documents. I'll find relevant information and explain it simply.</p>
                    <div className="prompt-list">
                      {prompts.map((prompt) => (
                        <button className="prompt-chip" key={prompt} onClick={() => sendQuestion(prompt)} disabled={busy}>
                          {prompt}<ArrowUpRight size={14} />
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="message-list">
                    {filteredMessages.map(({ message, index }) => (
                      <div
                        className={`message ${message.role === 'user' ? 'user' : ''} ${chatSearch.trim() && filteredMessages[searchMatchIndex]?.index === index ? 'search-active-match' : ''}`}
                        key={index}
                      >
                        <div className="message-avatar">{message.role === 'user' ? 'AM' : <Bot size={15} />}</div>
                        <div className="message-main">
                          <div className="message-author">
                            <span>{message.role === 'user' ? 'You' : 'Finwise advisor'}</span>
                            {message.timestamp && (
                              <time dateTime={message.timestamp}>
                                {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </time>
                            )}
                          </div>
                          <div className="message-text">
                            {message.role === 'assistant'
                              ? <FormattedAnswer content={message.content || ''} searchTerm={chatSearch} />
                              : <>{formatInline(message.content || '', chatSearch)}</>}
                          </div>

                          {message.role === 'assistant' && (
                            <button type="button" className="copy-answer-button" onClick={() => handleCopyAnswer(message.content, index)} title="Copy this answer">
                              {copiedMessage === index ? <><Check size={13} /> Copied</> : <><Copy size={13} /> Copy answer</>}
                            </button>
                          )}

                          {message.role === 'assistant' && <SourceList sources={message.sources} />}
                        </div>
                      </div>
                    ))}

                    {chatSearch && filteredMessages.length === 0 && (
                      <div className="chat-search-empty">
                        <Search size={18} />
                        <span>No matching messages found.</span>
                        <button type="button" onClick={() => setChatSearch('')}>Clear search</button>
                      </div>
                    )}

                    {busy && (
                      <div className="thinking">
                        <div className="thinking-avatar"><Bot size={15} /></div>
                        <div className="thinking-content">
                          <span className="thinking-label">Finwise advisor is thinking</span>
                          <div className="typing-dots" aria-label="Generating answer"><span /><span /><span /></div>
                        </div>
                      </div>
                    )}

                    <div ref={chatEnd} />
                  </div>
                )}
              </div>

              {notice && (
                <div className="notice">
                  <span>{notice}</span>
                  <button onClick={() => setNotice('')} aria-label="Dismiss notification"><X size={13} /></button>
                </div>
              )}

              <form className="chat-composer" onSubmit={(event) => {
                event.preventDefault()
                sendQuestion()
              }}>
                <button type="button" className="attach-button" title="Upload a document" onClick={() => fileInput.current?.click()}>
                  <Paperclip size={17} />
                </button>
                <textarea
                  ref={questionInput}
                  rows={1}
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && !event.shiftKey) {
                      event.preventDefault()
                      sendQuestion()
                    }
                  }}
                  placeholder="Ask your financial advisor..."
                  disabled={busy}
                  aria-label="Ask your financial advisor"
                />
                <span className="composer-hint">Enter to send</span>
                <button type="submit" className="send-button" disabled={!question.trim() || busy} aria-label="Send message">
                  {busy ? <LoaderCircle size={15} className="spin" /> : <Send size={15} />}
                </button>
              </form>

              <div className="chat-footnote"><ShieldCheck size={11} /> Answers are based on your uploaded documents.</div>
            </div>

            <div className="right-column">
              <section className="panel upload-panel" id="documents">
                <div className="side-panel-heading">
                  <div>
                    <h2>Your documents</h2>
                    <p>Upload files to your knowledge base</p>
                  </div>
                  <button className="icon-button" onClick={() => fileInput.current?.click()} title="Add document">
                    <Plus size={15} />
                  </button>
                </div>

                <input
                  ref={fileInput}
                  type="file"
                  accept=".pdf,.csv,.xlsx"
                  multiple
                  className="visually-hidden"
                  onChange={(event) => handleFiles(event.target.files)}
                />

                <button
                  type="button"
                  className="dropzone"
                  onClick={() => fileInput.current?.click()}
                  onDragOver={(event) => event.preventDefault()}
                  onDrop={handleDrop}
                  disabled={uploading}
                >
                  <div className="upload-icon">
                    {uploading ? <LoaderCircle size={17} className="spin" /> : <Upload size={17} />}
                  </div>
                  <strong>{uploading ? uploadStage : 'Click to upload or drag files'}</strong>
                  <span>PDF, CSV or XLSX files</span>
                  <small>
                    {uploading
                      ? uploadProgress >= 100 ? 'File received · Waiting for processing' : `${uploadProgress}% transferred`
                      : 'Upload your financial notes and reports'}
                  </small>
                  {uploading && (
                    <div className="upload-progress-wrap">
                      <div className="upload-progress-track" role="progressbar" aria-valuenow={uploadProgress} aria-valuemin={0} aria-valuemax={100}>
                        <span style={{ width: `${uploadProgress}%` }} />
                      </div>
                      <span className="upload-progress-label">
                        {uploadProgress >= 100 ? 'Processing may take a little time...' : `${uploadProgress}%`}
                      </span>
                    </div>
                  )}
                </button>

                <div className="document-stats">
                  <div className="document-stat"><span>TOTAL FILES</span><strong>{documents.length}</strong></div>
                  <div className="document-stat"><span>STORAGE USED</span><strong>{totalStorageLabel}</strong></div>
                  <div className="document-stat"><span>PROCESSED CHUNKS</span><strong>{totalDocumentChunks}</strong></div>
                </div>

                <div className="doc-list-heading">
                  <span>RECENT UPLOADS</span>
                  <span>{documents.length} FILES</span>
                </div>

                <div className="document-search">
                  <FileText size={14} />
                  <input
                    type="search"
                    value={documentSearch}
                    onChange={(event) => setDocumentSearch(event.target.value)}
                    placeholder="Search uploaded documents..."
                    aria-label="Search uploaded documents"
                  />
                  {documentSearch && (
                    <button type="button" onClick={() => setDocumentSearch('')} aria-label="Clear document search">
                      <X size={13} />
                    </button>
                  )}
                </div>

                {selectedDocument && (
                  <div className="document-details">
                    <div className="document-details-heading">
                      <strong>Document details</strong>
                      <button type="button" onClick={() => setSelectedDocument(null)} aria-label="Close document details">
                        <X size={14} />
                      </button>
                    </div>

                    <div className="document-detail-name">
                      <FileText size={15} />
                      <span title={selectedDocument.name}>{selectedDocument.name}</span>
                    </div>

                    <div className="document-detail-grid">
                      <div><span>FILE SIZE</span><strong>{selectedDocument.size || 'Not available'}</strong></div>
                      <div><span>STATUS</span><strong>{selectedDocument.status || 'Uploaded'}</strong></div>
                      <div><span>CHUNKS CREATED</span><strong>{selectedDocument.chunks ?? 'Not available'}</strong></div>
                    </div>

                    {/* Financial analytics */}
                    <div style={{ marginTop: '18px', paddingTop: '16px', borderTop: '1px solid #e8ebf2' }}>
                      <div className="document-details-heading" style={{ marginBottom: '12px' }}>
                        <strong>Financial analytics</strong>
                        <BarChart3 size={15} />
                      </div>

                      {!selectedDocument.documentId ? (
                        <p style={{ color: '#8792a5', fontSize: '12px', lineHeight: 1.6 }}>
                          This document was uploaded before analytics integration. Re-upload it to generate transaction analytics.
                        </p>
                      ) : analyticsLoading ? (
                        <p style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#718096', fontSize: '12px' }}>
                          <LoaderCircle size={14} className="spin" /> Loading financial analytics...
                        </p>
                      ) : analyticsError ? (
                        <p role="status" style={{ color: '#a65b36', fontSize: '12px', lineHeight: 1.6 }}>
                          {analyticsError.toLowerCase().includes('no transactions')
                            ? 'No structured bank transactions were found in this document.'
                            : analyticsError}
                        </p>
                      ) : transactionAnalytics ? (
                        <>
                          <div className="document-detail-grid">
                            <div><span>TRANSACTIONS</span><strong>{transactionAnalytics.summary.transaction_count}</strong></div>
                            <div><span>DEPOSITS</span><strong>{formatAmount(transactionAnalytics.summary.total_deposits)}</strong></div>
                            <div><span>WITHDRAWALS</span><strong>{formatAmount(transactionAnalytics.summary.total_withdrawals)}</strong></div>
                            <div><span>NET CASH FLOW</span><strong>{formatAmount(transactionAnalytics.summary.net_cash_flow)}</strong></div>
                            <div><span>OPENING BALANCE</span><strong>{formatAmount(transactionAnalytics.summary.opening_balance)}</strong></div>
                            <div><span>CLOSING BALANCE</span><strong>{formatAmount(transactionAnalytics.summary.closing_balance)}</strong></div>
                          </div>

                          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '18px', fontSize: '12px' }}>
                            <strong style={{ color: '#344054' }}>Spending by category</strong>
                            {Object.entries(transactionAnalytics.spending_by_category || {}).length > 0 ? (
                              Object.entries(transactionAnalytics.spending_by_category || {}).map(([category, amount]) => (
                                <div key={category} style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', color: '#718096' }}>
                                  <span>{category}</span>
                                  <strong style={{ color: '#344054' }}>{formatAmount(amount)}</strong>
                                </div>
                              ))
                            ) : (
                              <span style={{ color: '#8792a5' }}>No categorized expenses available.</span>
                            )}

                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', paddingTop: '10px', borderTop: '1px solid #e8ebf2', color: '#344054' }}>
                              <strong>Total expenses</strong>
                              <strong>{formatAmount(transactionAnalytics.total_expenses)}</strong>
                            </div>
                            <span style={{ color: '#98a2b3', fontSize: '10px', lineHeight: 1.5 }}>
                              Categories are currently assigned using transaction description keyword rules.
                            </span>
                          </div>
                        </>
                      ) : null}
                    </div>

                    {/* Transaction history */}
                    <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid #e8ebf2' }}>
                      <div className="document-details-heading" style={{ marginBottom: '12px' }}>
                        <strong>Transaction history</strong>
                        <span style={{ fontSize: '11px', color: '#8792a5' }}>
                          {transactionHistory.length} records
                        </span>
                      </div>

                      {!selectedDocument.documentId ? (
                        <p style={{ fontSize: '12px', color: '#8792a5' }}>
                          Re-upload this document to view its transactions.
                        </p>
                      ) : transactionsLoading ? (
                        <p style={{ fontSize: '12px', color: '#718096' }}>
                          <LoaderCircle size={13} className="spin" style={{ verticalAlign: 'middle', marginRight: '6px' }} />
                          Loading transactions...
                        </p>
                      ) : transactionsError ? (
                        <p role="status" style={{ fontSize: '12px', color: '#a65b36' }}>
                          {transactionsError}
                        </p>
                      ) : transactionHistory.length === 0 ? (
                        <p style={{ fontSize: '12px', color: '#8792a5' }}>
                          No transactions available for this document.
                        </p>
                      ) : (
                        <div style={{ overflowX: 'auto', width: '100%' }}>
                          <table style={{ width: '100%', minWidth: '620px', borderCollapse: 'collapse', fontSize: '11px', textAlign: 'left' }}>
                            <thead>
                              <tr style={{ background: '#f7f8fc' }}>
                                {['DATE', 'DESCRIPTION', 'CATEGORY', 'DEBIT', 'CREDIT', 'BALANCE'].map((heading) => (
                                  <th key={heading} style={{ ...transactionCellStyle, color: '#8792a5', fontWeight: 650 }}>
                                    {heading}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {transactionHistory.map((transaction, index) => {
                                const amount = Number(
                                  transaction.amount ??
                                  transaction.transaction_amount ??
                                  0
                                )

                                const type = String(
                                  transaction.transaction_type ??
                                  transaction.type ??
                                  transaction.direction ??
                                  ''
                                ).toLowerCase()

                                const debit = transaction.debit ??
                                  transaction.debit_amount ??
                                  (type.includes('debit') || type.includes('withdrawal') ? amount : 0)

                                const credit = transaction.credit ??
                                  transaction.credit_amount ??
                                  (type.includes('credit') || type.includes('deposit') ? amount : 0)

                                const date = transaction.transaction_date ?? transaction.date ?? '—'
                                const description = transaction.description ?? transaction.merchant ?? transaction.narration ?? '—'
                                const category = transaction.category ?? 'Other'
                                const balance = transaction.balance ?? transaction.running_balance

                                return (
                                  <tr key={transaction.id || index}>
                                    <td style={transactionCellStyle}>{date}</td>
                                    <td
                                      style={{ ...transactionCellStyle, maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis' }}
                                      title={description}
                                    >
                                      {description}
                                    </td>
                                    <td style={transactionCellStyle}>{category}</td>
                                    <td style={{ ...transactionCellStyle, color: Number(debit) > 0 ? '#d05b5b' : '#8792a5' }}>
                                      {Number(debit) > 0 ? formatAmount(debit) : '—'}
                                    </td>
                                    <td style={{ ...transactionCellStyle, color: Number(credit) > 0 ? '#16865b' : '#8792a5' }}>
                                      {Number(credit) > 0 ? formatAmount(credit) : '—'}
                                    </td>
                                    <td style={transactionCellStyle}>
                                      {balance !== undefined && balance !== null ? formatAmount(balance) : '—'}
                                    </td>
                                  </tr>
                                )
                              })}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {filteredDocuments.length ? (
                  filteredDocuments.map((doc, index) => (
                    <div className="doc-row" key={`${doc.name}-${index}`}>
                      <div className="file-icon">
                        {doc.name.toLowerCase().endsWith('.pdf')
                          ? <FileText size={16} />
                          : <FileSpreadsheet size={16} />}
                      </div>

                      <div className="doc-copy">
                        <strong title={doc.name}>{doc.name}</strong>
                        <span>{doc.size}</span>
                      </div>

                      <button
                        type="button"
                        className="doc-details-toggle"
                        title={`View details for ${doc.name}`}
                        aria-label={`View details for ${doc.name}`}
                        aria-expanded={selectedDocument?.name === doc.name}
                        onClick={() => setSelectedDocument(current =>
                          current?.name === doc.name ? null : doc
                        )}
                      >
                        <CircleHelp size={14} />
                      </button>

                      <button
                        type="button"
                        className="doc-remove"
                        title={`Remove ${doc.name} from recent uploads`}
                        aria-label={`Remove ${doc.name} from recent uploads`}
                        onClick={() => {
                          setDocuments(previous => previous.filter(item => item !== doc))
                          if (selectedDocument === doc) setSelectedDocument(null)
                        }}
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ))
                ) : (
                  <div className="empty-docs">
                    <FileText size={15} />
                    {documents.length ? 'No matching documents found.' : 'Your uploaded files will appear here.'}
                  </div>
                )}
              </section>

              <section className="tip-card">
                <div className="tip-head">
                  <div className="tip-icon"><Sparkles size={14} /></div>
                  FINWISE INSIGHT
                  <ChevronDown size={13} />
                </div>
                <h3>Make your documents work for you.</h3>
                <p>
                  Upload financial notes, reports and spreadsheets. Your AI advisor can retrieve relevant passages and explain them in simple language.
                </p>
                <a href="#advisor" onClick={() => setActiveNav('advisor')}>
                  Ask your advisor <ArrowUpRight size={12} />
                </a>
              </section>
            </div>
          </section>

          <footer className="page-footer">
            <span>Finwise · Your personal financial knowledge assistant</span>
            <button onClick={() => setNotice('Your advisor uses the documents uploaded to this workspace.')}>
              <CircleHelp size={12} /> Help & support
            </button>
          </footer>
        </div>
      </main>
    </div>
  )
}

export default App
