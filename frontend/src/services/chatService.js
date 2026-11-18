import api from './api'

const chatService = {
  // Conversations for a project.
  getConversations: async (projectId) => {
    const response = await api.get(
      `/api/projects/${projectId}/chats`
    )

    return response.data
  },

  // Messages of a single conversation.
  getMessages: async (projectId, conversationId) => {
    const response = await api.get(
      `/api/projects/${projectId}/chats/${conversationId}`
    )

    return response.data
  },

  // Ask a question. Omitting conversationId starts a new conversation.
  sendMessage: async (projectId, question, conversationId = null) => {
    const payload = { question }

    if (conversationId) {
      payload.conversation_id = conversationId
    }

    const response = await api.post(
      `/api/projects/${projectId}/chat`,
      payload
    )

    return response.data
  },
}

export default chatService
