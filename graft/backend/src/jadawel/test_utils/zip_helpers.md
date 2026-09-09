# backend/src/jadawel/test_utils/zip_helpers.py

- remove_file_from_zip · function · L9-L26 — def remove_file_from_zip(zip_path: str, new_zip_path: str, file_to_remove: str) -> str
- get_file_content_from_zip · function · L29-L43 — def get_file_content_from_zip(zip_path: str, file_to_get: str) -> Optional[AnyStr]
- change_file_content_in_zip · function · L46-L68 — def change_file_content_in_zip( zip_path: str, new_zip_path: str, file_to_change: str, new_content: AnyStr ) -> str
- add_file_to_zip · function · L71-L91 — def add_file_to_zip( zip_path: str, new_zip_path: str, file_name: str, content: bytes ) -> str
