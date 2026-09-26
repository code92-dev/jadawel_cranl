/** Sanad (سند), the in-app AI assistant — docs/SANAD_AI_ASSISTANT.md. */
export default (client) => {
  return {
    fetchModels(workspaceId) {
      return client.get(`/arabase/sanad/workspace/${workspaceId}/models/`)
    },
    fetchChats(workspaceId) {
      return client.get(`/arabase/sanad/workspace/${workspaceId}/chats/`)
    },
    createChat(workspaceId) {
      return client.post(`/arabase/sanad/workspace/${workspaceId}/chats/`)
    },
    fetchChat(chatId) {
      return client.get(`/arabase/sanad/chats/${chatId}/`)
    },
    deleteChat(chatId) {
      return client.delete(`/arabase/sanad/chats/${chatId}/`)
    },
    /** Answered asynchronously: poll `fetchChat` until the reply settles. */
    sendMessage(chatId, content, model, context) {
      return client.post(`/arabase/sanad/chats/${chatId}/messages/`, {
        content,
        model,
        context,
      })
    },
    decide(chatId, decisions) {
      return client.post(`/arabase/sanad/chats/${chatId}/decisions/`, {
        decisions,
      })
    },
  }
}
