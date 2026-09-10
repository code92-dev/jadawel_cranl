# backend/src/jadawel/contrib/integrations/local_jadawel/utils.py

- guess_json_type_from_response_serializer_field · function · L45-L118 — def guess_json_type_from_response_serializer_field( serializer_field: Union[Field, Serializer], ) -> Dict[str, Any]
- _handle_file · function · L121-L156 — def _handle_file(file_obj: dict, user: AbstractUser) -> dict
- prepare_files_for_db · function · L159-L195 — def prepare_files_for_db(value: Any, user: AbstractUser) -> List[dict]
- guess_cast_function_from_response_serializer_field · function · L198-L237 — def guess_cast_function_from_response_serializer_field( serializer_field: Union[Field, Serializer], service: LocalJadawelUpsertRow ) -> Optional[Callable]
