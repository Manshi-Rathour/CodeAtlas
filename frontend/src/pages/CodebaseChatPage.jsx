import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  MessageSquare,
  Plus,
  RefreshCw,
  Sparkles,
  AlertCircle,
} from 'lucide-react'

import Sidebar from '../components/common/Sidebar'
import DashboardTopbar from '../components/common/DashboardTopbar'
import ProjectNav from '../components/common/ProjectNav'
import ChatWindow from '../components/chat/ChatWindow'
import ChatInput from '../components/chat/ChatInput'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import EmptyState from '../components/common/EmptyState'

import projectService from '../services/projectService'
import chatService from '../services/chatService'

import './CodebaseChatPage.css'

const SUGGESTED_QUESTIONS = [
  'Explain this project and its main purpose.',
  'Where is authentication implemented?',
  'How does the frontend communicate with the backend?',
  'Explain the database connection and data access layer.',
  'Summarize the responsibilities of the main directories.',
]

function CodebaseChatPage() {
  const { projectId } = useParams()
  const navigate = useNavigate()

  const [project, setProject] = useState(null)
  const [conversations, setConversations] = useState([])

  const [activeConversationId, setActiveConversationId] = useState(null)
  const [messages, setMessages] = useState([])

  const [isLoadingPage, setIsLoadingPage] = useState(true)
  const [isLoadingMessages, setIsLoadingMessages] = useState(false)
  const [isSending, setIsSending] = useState(false)

  const [pageError, setPageError] = useState('')
  const [sendError, setSendError] = useState('')

  // When a brand-new conversation is created the stored messages are
  // reloaded, so remember that the latest answer should be typed out.
  const pendingTypingRef = useRef(false)

  const loadConversations = useCallback(async () => {
    const response = await chatService.getConversations(projectId)
    setConversations(response)
    return response
  }, [projectId])

  // Load the project and its existing conversations.
  useEffect(() => {
    let isActive = true

    const loadPage = async () => {
      setIsLoadingPage(true)
      setPageError('')

      try {
        const [projectResponse, conversationResponse] =
          await Promise.all([
            projectService.getProject(projectId),
            chatService.getConversations(projectId),
          ])

        if (!isActive) return

        setProject(projectResponse)
        setConversations(conversationResponse)

        if (conversationResponse.length > 0) {
          setActiveConversationId(
            conversationResponse[0].conversation_id
          )
        }
      } catch (err) {
        if (isActive) {
          setPageError(
            err.response?.data?.detail ||
            'Unable to load AI chat for this project.'
          )
        }
      } finally {
        if (isActive) {
          setIsLoadingPage(false)
        }
      }
    }

    loadPage()

    return () => {
      isActive = false
    }
  }, [projectId])

  // Load messages whenever the active conversation changes.
  useEffect(() => {
    if (!activeConversationId) {
      setMessages([])
      return
    }

    let isActive = true

    const loadMessages = async () => {
      setIsLoadingMessages(true)
      setSendError('')

      try {
        const response = await chatService.getMessages(
          projectId,
          activeConversationId
        )

        if (isActive) {
          if (pendingTypingRef.current && response.length > 0) {
            pendingTypingRef.current = false

            let lastAssistantIndex = -1

            response.forEach((message, index) => {
              if (message.role === 'assistant') {
                lastAssistantIndex = index
              }
            })

            setMessages(
              response.map((message, index) =>
                index === lastAssistantIndex
                  ? { ...message, animate: true }
                  : message
              )
            )
          } else {
            setMessages(response)
          }
        }
      } catch (err) {
        if (isActive) {
          setMessages([])
          setSendError(
            err.response?.data?.detail ||
            'Unable to load this conversation.'
          )
        }
      } finally {
        if (isActive) {
          setIsLoadingMessages(false)
        }
      }
    }

    loadMessages()

    return () => {
      isActive = false
    }
  }, [projectId, activeConversationId])

  const handleSend = async (question) => {
    const optimisticMessage = {
      id: `pending-${Date.now()}`,
      role: 'user',
      content: question,
      sources: [],
    }

    setMessages((current) => [...current, optimisticMessage])
    setIsSending(true)
    setSendError('')
    setIsLoadingMessages(false)

    try {
      const result = await chatService.sendMessage(
        projectId,
        question,
        activeConversationId
      )

      const answer = {
        id: `answer-${Date.now()}`,
        role: 'assistant',
        content: result.answer,
        sources: result.sources || [],
      }

      if (activeConversationId) {
        setMessages((current) => [
          ...current,
          { ...answer, animate: true },
        ])
      } else {
        // Setting the conversation ID reloads the stored messages and
        // the reload marks the new answer for the typing effect.
        pendingTypingRef.current = true
        setActiveConversationId(result.conversation_id)
      }

      await loadConversations()
    } catch (err) {
      setSendError(
        err.response?.data?.detail ||
        'The AI could not answer this question. Please try again.'
      )
    } finally {
      setIsSending(false)
    }
  }

  const handleNewChat = () => {
    pendingTypingRef.current = false
    setActiveConversationId(null)
    setMessages([])
    setSendError('')
  }

  const handleRefresh = async () => {
    setPageError('')

    try {
      await loadConversations()

      if (activeConversationId) {
        const response = await chatService.getMessages(
          projectId,
          activeConversationId
        )
        setMessages(response)
      }
    } catch (err) {
      setPageError(
        err.response?.data?.detail ||
        'Unable to refresh conversations.'
      )
    }
  }

  const activeConversation = conversations.find(
    (conversation) =>
      conversation.conversation_id === activeConversationId
  )

  if (isLoadingPage) {
    return (
      <div className="dashboard-layout">
        <Sidebar />
        <main className="dashboard-main chat-page-main">
          <LoadingSpinner label="Loading AI chat..." />
        </main>
      </div>
    )
  }

  if (pageError || !project) {
    return (
      <div className="dashboard-layout">
        <Sidebar />
        <main className="dashboard-main chat-page-main">
          <div className="chat-page-content">
            <ErrorMessage
              title="Unable to load AI chat"
              message={pageError || 'Project not found.'}
              onRetry={() => window.location.reload()}
            />
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main chat-page-main">
        <DashboardTopbar>
          Workspace <span>/</span> Projects <span>/</span>
          {project.name} <span>/</span> AI Chat
        </DashboardTopbar>

        <div className="chat-page-content">
          <button
            className="project-back-button"
            onClick={() => navigate(`/dashboard/projects/${projectId}`)}
          >
            <ArrowLeft size={17} />
            Back to Project
          </button>

          <ProjectNav projectId={projectId} />

          <section className="chat-page-heading">
            <div>
              <div className="chat-page-eyebrow">
                <Sparkles size={16} />
                AI CODE UNDERSTANDING
              </div>

              <h1>Ask about {project.name}</h1>

              <p>
                Questions are answered from your analyzed source code,
                with references to the files that were used.
              </p>
            </div>

            <button
              className="chat-refresh-button"
              onClick={handleRefresh}
              title="Refresh conversations"
            >
              <RefreshCw size={16} />
              Refresh
            </button>
          </section>

          <div className="chat-layout">
            <aside className="chat-conversations">
              <div className="chat-conversations-header">
                <span>
                  <MessageSquare size={15} />
                  Conversations
                </span>

                <button
                  onClick={handleNewChat}
                  title="Start a new conversation"
                >
                  <Plus size={16} />
                </button>
              </div>

              {conversations.length === 0 ? (
                <p className="chat-conversations-empty">
                  No conversations yet. Ask your first question.
                </p>
              ) : (
                <div className="chat-conversation-list">
                  {conversations.map((conversation) => (
                    <button
                      key={conversation.conversation_id}
                      className={`chat-conversation-item ${
                        conversation.conversation_id ===
                        activeConversationId
                          ? 'active'
                          : ''
                      }`}
                      onClick={() =>
                        setActiveConversationId(
                          conversation.conversation_id
                        )
                      }
                    >
                      <strong>
                        {conversation.title || 'Untitled conversation'}
                      </strong>

                      <span>
                        {conversation.message_count} messages
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </aside>

            <section className="chat-panel">
              <div className="chat-panel-header">
                <div>
                  <h2>
                    {activeConversation?.title || 'New conversation'}
                  </h2>

                  <span>
                    {activeConversation
                      ? `${activeConversation.message_count} messages`
                      : 'Ask a question to get started'}
                  </span>
                </div>

                <button
                  className="chat-new-button"
                  onClick={handleNewChat}
                >
                  <Plus size={15} />
                  New Chat
                </button>
              </div>

              {sendError && (
                <div className="chat-inline-error">
                  <AlertCircle size={16} />
                  {sendError}
                </div>
              )}

              {isLoadingMessages ? (
                <LoadingSpinner
                  label="Loading conversation..."
                  compact
                />
              ) : (
                <ChatWindow
                  messages={messages}
                  isLoading={isSending}
                  emptyState={
                    <EmptyState
                      icon={MessageSquare}
                      title="Ask your first question"
                      message="CodeAtlas searches the analyzed code chunks and asks the local model to explain them. Try one of these:"
                      action={
                        <div className="chat-suggestions">
                          {SUGGESTED_QUESTIONS.map((suggestion) => (
                            <button
                              key={suggestion}
                              onClick={() => handleSend(suggestion)}
                              disabled={isSending}
                            >
                              {suggestion}
                            </button>
                          ))}
                        </div>
                      }
                    />
                  }
                />
              )}

              <ChatInput
                onSend={handleSend}
                isLoading={isSending}
              />
            </section>
          </div>
        </div>
      </main>
    </div>
  )
}

export default CodebaseChatPage
