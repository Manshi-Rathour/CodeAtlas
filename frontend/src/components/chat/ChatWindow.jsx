import { useEffect, useRef } from 'react'
import { Bot, LoaderCircle } from 'lucide-react'

import ChatMessage from './ChatMessage'

import './Chat.css'

// A user is considered to be following the conversation when the chat
// panel is this close to the bottom.
const FOLLOW_THRESHOLD_PX = 80

function ChatWindow({ messages, isLoading, emptyState }) {
  const windowRef = useRef(null)
  const stickToBottomRef = useRef(true)

  const scrollToBottom = () => {
    const container = windowRef.current

    if (container) {
      container.scrollTop = container.scrollHeight
    }
  }

  // Only the chat panel scrolls; the page itself must never jump.
  const handleScroll = () => {
    const container = windowRef.current

    if (!container) {
      return
    }

    stickToBottomRef.current =
      container.scrollHeight -
        container.scrollTop -
        container.clientHeight <
      FOLLOW_THRESHOLD_PX
  }

  // Follow the answer while it is being revealed, unless the user has
  // scrolled up to read earlier messages.
  const handleTypingProgress = () => {
    if (stickToBottomRef.current) {
      scrollToBottom()
    }
  }

  useEffect(() => {
    const lastMessage = messages[messages.length - 1]

    // Always reveal the question the user just sent; otherwise follow
    // only when the user is already at the bottom.
    if (
      !lastMessage ||
      lastMessage.role === 'user' ||
      stickToBottomRef.current
    ) {
      stickToBottomRef.current = true
      scrollToBottom()
    }
  }, [messages, isLoading])

  if (messages.length === 0 && !isLoading) {
    return <div className="chat-window">{emptyState}</div>
  }

  return (
    <div className="chat-window" ref={windowRef} onScroll={handleScroll}>
      <div className="chat-messages">
        {messages.map((message, index) => (
          <ChatMessage
            key={message.id || `message-${index}`}
            message={message}
            onTypingProgress={handleTypingProgress}
          />
        ))}

        {isLoading && (
          <article className="chat-message assistant">
            <div className="chat-avatar">
              <Bot size={17} />
            </div>

            <div className="chat-message-body">
              <div className="chat-message-role">CodeAtlas AI</div>

              <div className="chat-thinking">
                <LoaderCircle size={16} className="spin" />
                Searching your codebase...
              </div>
            </div>
          </article>
        )}
      </div>
    </div>
  )
}

export default ChatWindow
