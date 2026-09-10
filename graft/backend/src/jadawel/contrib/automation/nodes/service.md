# backend/src/jadawel/contrib/automation/nodes/service.py

- AutomationNodeService · class · L45-L507 — class AutomationNodeService
- __init__ · method · L46-L47 — def __init__(self)
- get_node · method · L49-L67 — def get_node(self, user: AbstractUser, node_id: int) -> AutomationNode
- get_nodes · method · L69-L101 — def get_nodes( self, user: AbstractUser, workflow: AutomationWorkflow, specific: Optional[bool] = True, ) -> Iterable[AutomationNode]
- _check_position · method · L103-L132 — def _check_position( self, workflow: AutomationWorkflow, reference_node: AutomationNode | None, position: NodePositionType, output: str, )
- create_node · method · L134-L212 — def create_node( self, user: AbstractUser, node_type: AutomationNodeType, workflow: AutomationWorkflow, reference_node_id: int | None = None, position: NodePositionType = "south", # south, child output: str = "", **kwargs, ) -> AutomationNode
- update_node · method · L214-L262 — def update_node( self, user: AbstractUser, node_id: int, **kwargs, ) -> UpdatedAutomationNode
- delete_node · method · L264-L306 — def delete_node( self, user: AbstractUser | None, node_id: int, ignore_user_for_signal=False ) -> AutomationNode
- duplicate_node · method · L308-L349 — def duplicate_node( self, user: AbstractUser, source_node_id: AutomationNode, ) -> AutomationNode
- replace_node · method · L351-L434 — def replace_node( self, user: AbstractUser, node_id: int, new_node_type_str: str, existing_node: AutomationNode | None = None, ) -> ReplacedAutomationNode
- move_node · method · L436-L507 — def move_node( self, user: AbstractUser, node_id_to_move: int, reference_node_id: int | None, position: NodePositionType, output: str, ) -> AutomationNodeMove
