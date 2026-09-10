# backend/tests/jadawel/contrib/builder/elements/mixins/test_collection_element_type_mixin.py

- collection_element_mixin_fixture · function · L20-L54 — def collection_element_mixin_fixture(data_fixture)
- test_import_context_addition_sets_schema_property · function · L58-L87 — def test_import_context_addition_sets_schema_property(data_fixture)
- test_import_export_collection_element_type · function · L91-L125 — def test_import_export_collection_element_type(collection_element_mixin_fixture)
- test_extract_properties · function · L129-L144 — def test_extract_properties(collection_element_mixin_fixture)
- test_mixin_prepare_value_for_db · function · L148-L230 — def test_mixin_prepare_value_for_db()
- Base · class · L151-L153 — class Base
- prepare_value_for_db · method · L152-L153 — def prepare_value_for_db(self, values, instance=None)
- Test · class · L155-L156 — class Test(CollectionElementTypeMixin, Base)
