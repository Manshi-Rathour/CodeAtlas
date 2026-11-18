import { useEffect, useRef } from 'react'
import { Bot, LoaderCircle } from 'lucide-react'

import ChatMessage from './ChatMessage'

import './Chat.css'

function ChatWindow({ messages, isLoading, emptyState }) {
  const windowRef = useRef(null)
  const endRef = useRef(null)

  useEffect(() => {
    if (endRef.current) {
      endRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'end',
      })
    }
  }, [messages, isLoading])

  // Follow the answer while it is being revealed, but only when the
  // user has not scrolled up to read earlier messages.
  const handleTypingProgress = () => {
    const container = windowRef.current

    if (!container || !endRef.current) {
      return
    }

    const nearBottom =
      container.scrollHeight -
        container.scrollTop -
        container.clientHeight <
      160

    if (nearBottom) {
      endRef.current.scrollIntoView({
        behavior: 'auto',
        block: 'end',
      })
    }
  }

  if (messages.length === 0 && !isLoading) {
    return <div className="chat-window">{emptyState}</div>
  }

  return (
    <div className="chat-window" ref={windowRef}>
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

        <div ref={endRef} />
      </div>
    </div>
  )
}

export default ChatWindow
