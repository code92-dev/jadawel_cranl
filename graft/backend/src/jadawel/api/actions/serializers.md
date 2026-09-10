# backend/src/jadawel/api/actions/serializers.py

- get_action_scopes_request_serializer · function · L12-L23 — def get_action_scopes_request_serializer() -> Type[serializers.Serializer]
- get_undo_request_serializer · function · L27-L67 — def get_undo_request_serializer() -> Type[serializers.Serializer]
- UndoRedoRequestSerializer · class · L42-L65 — class UndoRedoRequestSerializer(serializers.Serializer)
- data · method · L55-L65 — def data(self) -> List[ActionScopeStr]
- UndoRedoResultCodeField · class · L71-L97 — class UndoRedoResultCodeField(serializers.Field): # Please keep code values in sync with # web-frontend/modules/core/utils/undoRedoConstants.js:UNDO_REDO_RESULT_CODES
- __init__ · method · L78-L86 — def __init__(self, *args, **kwargs)
- get_attribute · method · L88-L89 — def get_attribute(self, instance)
- to_representation · method · L91-L97 — def to_representation(self, actions)
- UndoRedoActionSerializer · class · L100-L122 — class UndoRedoActionSerializer(serializers.ModelSerializer)
- Meta · class · L120-L122 — class Meta
- UndoRedoResponseSerializer · class · L125-L127 — class UndoRedoResponseSerializer(serializers.Serializer)
