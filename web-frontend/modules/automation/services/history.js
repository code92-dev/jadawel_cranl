export default (client) => {
  return {
    getWorkflowHistory(workflowId) {
      return client.get(`automation/workflows/${workflowId}/history/`)
    },
    cancelWorkflowHistory(workflowHistoryId) {
      return client.post(
        `automation/workflow_histories/${workflowHistoryId}/cancel/`
      )
    },
  }
}
