# backend/src/jadawel/contrib/database/field_rules/actions.py

- CreateFieldRuleActionType · class · L23-L104 — class CreateFieldRuleActionType(UndoableActionType)
- Params · class · L37-L44 — class Params
- do · method · L47-L78 — def do( cls, user: AbstractUser, table: Table, rule_type: str, in_rule_data: dict ) -> FieldRule
- scope · method · L81-L82 — def scope(cls, table_id) -> ActionScopeStr
- undo · method · L85-L94 — def undo( cls, user: AbstractUser, params: Params, action_being_undone: Action, )
- redo · method · L97-L104 — def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action)
- UpdateFieldRuleActionType · class · L107-L182 — class UpdateFieldRuleActionType(UndoableActionType)
- Params · class · L121-L129 — class Params
- do · method · L132-L159 — def do(cls, user: AbstractUser, rule: FieldRule, in_rule_data: dict) -> FieldRule
- scope · method · L162-L163 — def scope(cls, table_id) -> ActionScopeStr
- undo · method · L166-L175 — def undo( cls, user: AbstractUser, params: Params, action_being_undone: Action, )
- redo · method · L178-L182 — def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action)
- DeleteFieldRuleActionType · class · L185-L261 — class DeleteFieldRuleActionType(UndoableActionType)
- Params · class · L199-L206 — class Params
- do · method · L209-L235 — def do(cls, user: AbstractUser, rule: FieldRule) -> FieldRule
- scope · method · L238-L239 — def scope(cls, table_id) -> ActionScopeStr
- undo · method · L242-L254 — def undo( cls, user: AbstractUser, params: Params, action_being_undone: Action, )
- redo · method · L257-L261 — def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action)
