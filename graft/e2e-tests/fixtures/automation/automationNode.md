# e2e-tests/fixtures/automation/automationNode.ts

- AutomationNode · class · L4-L10 — class AutomationNode
- constructor · method · L5-L9 — constructor( public id: number, public type: string, public workflow: AutomationWorkflow )
- createAutomationNode · function · L12-L28 — async function createAutomationNode( workflow: AutomationWorkflow, nodeType: string, referenceNodeId: number | null = null, position: string = "south", output: string = "" ): Promise<AutomationNode>
