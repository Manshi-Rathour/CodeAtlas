import { useState } from 'react'
import { SendHorizontal, LoaderCircle } from 'lucide-react'

import './Chat.css'

const MAX_QUESTION_LENGTH = 5000

function ChatInput({ onSend, isLoading }) {
  const [question, setQuestion] = useState('')

  const handleSubmit = (event) => {
    event.preventDefault()

    const trimmed = question.trim()

    if (!trimmed || isLoading) return

    onSend(trimmed)
    setQuestion('')
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      handleSubmit(event)
    }
  }

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <textarea
        rows={2}
        maxLength={MAX_QUESTION_LENGTH}
        placeholder="Ask anything about this codebase..."
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isLoading}
      />

      <div className="chat-input-footer">
        <span>
          {question.length}/{MAX_QUESTION_LENGTH} · Enter to send,
          Shift + Enter for a new line
        </span>

        <button
          type="submit"
          disabled={!question.trim() || isLoading}
        >
          {isLoading ? (
            <LoaderCircle size={16} className="spin" />
          ) : (
            <SendHorizontal size={16} />
          )}

          {isLoading ? 'Thinking...' : 'Send'}
        </button>
      </div>
    </form>
  )
}

export default ChatInput
