# backend/src/arabase/apps.py

- ArabaseConfig · class · L6-L164 — class ArabaseConfig(AppConfig)
- ready · method · L18-L164 — def ready(self): # Registry registrations land here as each phase is implemented, e.g.: # # from jadawel.contrib.database.fields.registries import field_type_registry # from arabase.fields.hijri import HijriDateFieldType # field_type_registry.register(HijriDateFieldType()) # # Keep imports inside ready() (not at module top) so Django app loading # order is respected.
