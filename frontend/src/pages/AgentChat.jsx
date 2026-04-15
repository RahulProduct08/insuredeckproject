import React, { useState, useEffect, useRef } from 'react'
import { createAgentConversation, sendAgentMessage } from '../api.js'
import { PaperAirplaneIcon, ArrowPathIcon } from '@heroicons/react/24/solid'
import { ShieldCheckIcon } from '@heroicons/react/24/outline'

function AgentAvatar() {
  return (
    <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center shrink-0 shadow">
      <ShieldCheckIcon className="w-4 h-4 text-white" />
    </div>
  )
}

function Message({ role, content }) {
  if (role === 'user') {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[70%] bg-brand-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed shadow-sm">
          {content}
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-end gap-2 mb-4">
      <AgentAvatar />
      <div className="max-w-[70%] bg-white text-slate-700 rounded-2xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed shadow-sm border border-slate-100 whitespace-pre-wrap">
        {content}
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2 mb-4">
      <AgentAvatar />
      <div className="bg-white border border-slate-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
        <div className="flex gap-1 items-center h-4">
          <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  )
}

export default function AgentChat() {
  const [conversationId, setConversationId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [initializing, setInitializing] = useState(true)
  const [error, setError] = useState(null)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  function startSession() {
    setInitializing(true)
    setMessages([])
    setConversationId(null)
    setError(null)
    createAgentConversation()
      .then(data => {
        setConversationId(data.conversation_id)
        setMessages([{
          role: 'assistant',
          content: "Hi there! I'm Alex, your insurance advisor. It's great to connect with you today! 😊\n\nI'm here to help you find the right coverage for your needs — whether that's for your home, car, life, or family.\n\nTo get started, could I get your name?",
        }])
      })
      .catch(() => setError('Could not connect to the advisor. Please try again.'))
      .finally(() => setInitializing(false))
  }

  useEffect(() => { startSession() }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function handleSend() {
    const text = input.trim()
    if (!text || loading || !conversationId) return

    setInput('')
    inputRef.current?.focus()
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)
    setError(null)

    try {
      const data = await sendAgentMessage(conversationId, text)
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply }])
    } catch (err) {
      setError("Something went wrong. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      {/* Header */}
      <div className="shrink-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-brand-600 flex items-center justify-center shadow">
              <ShieldCheckIcon className="w-5 h-5 text-white" />
            </div>
            <span className="absolute bottom-0 right-0 w-3 h-3 bg-emerald-400 border-2 border-white rounded-full" />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-800">Alex — Insurance Advisor</div>
            <div className="text-xs text-emerald-500 font-medium">Online · Ready to help</div>
          </div>
        </div>
        <button
          onClick={startSession}
          disabled={initializing}
          title="Start a new conversation"
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-brand-600 border border-slate-200 hover:border-brand-300 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-40"
        >
          <ArrowPathIcon className="w-3.5 h-3.5" />
          New Chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {initializing ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-slate-400">
            <div className="w-10 h-10 rounded-full bg-brand-100 flex items-center justify-center animate-pulse">
              <ShieldCheckIcon className="w-5 h-5 text-brand-500" />
            </div>
            <span className="text-sm">Connecting you with Alex...</span>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <Message key={i} role={msg.role} content={msg.content} />
            ))}
            {loading && <TypingIndicator />}
            {error && (
              <div className="text-center text-red-500 text-xs py-2 bg-red-50 rounded-lg px-4">
                {error}
              </div>
            )}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      {/* Suggested replies — only shown at start */}
      {!loading && messages.length === 1 && (
        <div className="shrink-0 px-6 pb-3 flex flex-wrap gap-2">
          {["I need home insurance", "Looking for life insurance", "Car insurance quote", "Not sure what I need"].map(s => (
            <button
              key={s}
              onClick={() => { setInput(s); setTimeout(handleSend, 0) }}
              className="text-xs bg-white border border-brand-200 text-brand-600 hover:bg-brand-50 px-3 py-1.5 rounded-full transition-colors shadow-sm"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="shrink-0 bg-white border-t border-slate-200 px-6 py-4">
        <div className="flex gap-3 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading || initializing || !conversationId}
            placeholder="Type your message..."
            rows={1}
            className="flex-1 bg-slate-50 border border-slate-200 focus:border-brand-400 focus:bg-white outline-none text-slate-700 text-sm rounded-2xl px-4 py-3 resize-none placeholder-slate-400 disabled:opacity-40 transition-colors"
            style={{ minHeight: '46px', maxHeight: '120px' }}
            onInput={e => {
              e.target.style.height = 'auto'
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
            }}
          />
          <button
            onClick={handleSend}
            disabled={loading || initializing || !input.trim() || !conversationId}
            className="shrink-0 w-11 h-11 bg-brand-600 hover:bg-brand-700 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-full flex items-center justify-center transition-colors shadow-sm"
          >
            <PaperAirplaneIcon className="w-4 h-4" />
          </button>
        </div>
        <p className="text-center text-xs text-slate-400 mt-2">Press Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  )
}
