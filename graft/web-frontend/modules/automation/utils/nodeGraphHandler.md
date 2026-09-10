# web-frontend/modules/automation/utils/nodeGraphHandler.js

- replace · function · L3-L10 — replace = (array, itemToReplace, replacement)
- NodeGraphHandler · class · L12-L259 — class NodeGraphHandler
- constructor · method · L13-L16 — constructor(workflow)
- getNode · method · L18-L20 — getNode(nodeId)
- getInfo · method · L22-L27 — getInfo(node)
- hasNodes · method · L29-L31 — hasNodes()
- getFirstNode · method · L33-L38 — getFirstNode()
- getChildren · method · L40-L44 — getChildren(targetNode)
- getNextNodes · method · L46-L58 — getNextNodes(targetNode, output = null)
- getNodeAtPosition · method · L60-L89 — getNodeAtPosition(referenceNode, position, output)
- getPreviousPositions · method · L91-L136 — getPreviousPositions(targetNode)
- explore · function · L92-L129 — explore = (currentPosition, path)
- getNodePosition · method · L138-L160 — getNodePosition(node)
- insert · method · L162-L201 — insert(node, referenceNode, position, output)
- remove · method · L203-L241 — remove(node)
- move · method · L243-L250 — move(nodeToMove, referenceNode, position, output)
- replace · method · L252-L258 — replace(nodeToReplace, newNode)
