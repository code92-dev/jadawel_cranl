# backend/src/jadawel/core/export_serialized.py

- CoreExportSerializedStructure · class · L6-L32 — class CoreExportSerializedStructure: # Explicitly defines the core fields necessary to create an Application. # This is needed by `DatabaseApplicationType.import_serialized` to prevent # additional data being passed up to `ApplicationType.import_serialized` # when the `Application` is being created.
- filter_application_fields · method · L14-L23 — def filter_application_fields( cls, serialized_values: Dict[str, Any] ) -> Dict[str, Any]
- application · method · L26-L32 — def application(id, name, order, type)
