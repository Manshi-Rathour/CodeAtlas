import { useEffect, useRef, useState } from 'react'
import { Bot, User } from 'lucide-react'

import MarkdownViewer from '../documentation/MarkdownViewer'
import SourceReference from './SourceReference'

import './Chat.css'

// Answer text is revealed in small batches to mimic live typing.
const TYPING_INTERVAL_MS = 24
const TYPING_STEPS = 175

function ChatMessage({ message, onTypingProgress }) {
  const isUser = message.role === 'user'
  const sources = message.sources || []

  const fullContent = message.content || ''
  const shouldAnimate = Boolean(message.animate) && !isUser

  const [visibleLength, setVisibleLength] = useState(
    shouldAnimate ? 0 : fullContent.length
  )

  // Keep the latest callback without restarting the typing timer.
  const progressRef = useRef(onTypingProgress)

  useEffect(() => {
    progressRef.current = onTypingProgress
  }, [onTypingProgress])

  useEffect(() => {
    if (!shouldAnimate || fullContent.length === 0) {
      return undefined
    }

    let shown = 0
    const step = Math.max(
      2,
      Math.ceil(fullContent.length / TYPING_STEPS)
    )

    const timer = window.setInterval(() => {
      shown = Math.min(shown + step, fullContent.length)
      setVisibleLength(shown)

      // Keep the chat panel following the revealed text.
      if (progressRef.current) {
        progressRef.current()
      }

      if (shown >= fullContent.length) {
        window.clearInterval(timer)
      }
    }, TYPING_INTERVAL_MS)

    return () => window.clearInterval(timer)
  }, [shouldAnimate, fullContent])

  const isTyping =
    shouldAnimate && visibleLength < fullContent.length

  const displayedContent = isTyping
    ? fullContent.slice(0, visibleLength)
    : fullContent

  return (
    <article
      className={`chat-message ${isUser ? 'user' : 'assistant'}${
        isTyping ? ' typing' : ''
      }`}
    >
      <div className="chat-avatar">
        {isUser ? <User size={17} /> : <Bot size={17} />}
      </div>

      <div className="chat-message-body">
        <div className="chat-message-role">
          {isUser ? 'You' : 'CodeAtlas AI'}
        </div>

        {isUser ? (
          <p className="chat-user-text">{message.content}</p>
        ) : (
          <div className="chat-answer">
            <MarkdownViewer content={displayedContent} />

            {isTyping && (
              <span
                className="chat-typing-caret"
                aria-hidden="true"
              />
            )}
          </div>
        )}

        {!isUser && !isTyping && sources.length > 0 && (
          <div className="chat-sources">
            <span className="chat-sources-label">
              Sources used ({sources.length})
            </span>

            {sources.map((source, index) => (
              <SourceReference
                key={`${source.file_path}-${source.start_line}-${index}`}
                source={source}
              />
            ))}
          </div>
        )}
      </div>
    </article>
  )
}

export default ChatMessage
