# backend/src/jadawel/core/user_files/handler.py

- UserFileHandler · class · L57-L565 — class UserFileHandler
- _is_active_content_extension · method · L58-L59 — def _is_active_content_extension(self, extension: str) -> bool
- _is_active_content_mime_type · method · L61-L62 — def _is_active_content_mime_type(self, mime_type: str) -> bool
- _resolve_mime_type_and_active_content · method · L64-L98 — def _resolve_mime_type_and_active_content( self, file_name: str, extension: str, stream ) -> tuple[str, bool]
- _neutralize_active_content · method · L100-L105 — def _neutralize_active_content(self, user_file: UserFile) -> UserFile
- is_user_file_name · method · L107-L113 — def is_user_file_name(self, user_file_name: str) -> bool
- get_user_file_url · method · L115-L122 — def get_user_file_url(self, user_file)
- get_user_file_by_name · method · L124-L139 — def get_user_file_by_name( self, user_file_name: str, base_queryset: Optional[QuerySet] = None ) -> UserFile
- user_file_path · method · L141-L155 — def user_file_path(self, user_file_name)
- user_file_sha256 · method · L157-L171 — def user_file_sha256(self, user_file_name: str) -> str
- user_file_thumbnail_path · method · L173-L189 — def user_file_thumbnail_path(self, user_file_name, thumbnail_name)
- generate_unique · method · L191-L226 — def generate_unique(self, sha256_hash, extension, length=32, max_tries=1000)
- generate_and_save_image_thumbnails · method · L228-L289 — def generate_and_save_image_thumbnails( self, image: "Image", user_file_name: str, storage: Storage | None = None, only_with_name: str | None = None, )
- upload_user_file · method · L291-L402 — def upload_user_file(self, user, file_name, stream, storage=None)
- upload_user_file_by_url · method · L404-L489 — def upload_user_file_by_url(self, user, url, file_name=None, storage=None)
- export_user_file · method · L491-L534 — def export_user_file( self, user_file: Optional[UserFile], files_zip: Optional[ExportZipFile] = None, storage: Optional[Storage] = None, cache: Dict[str, Any] = None, ) -> Optional[Dict[str, str]]
- import_user_file · method · L536-L565 — def import_user_file( self, serialized_user_file: Dict[str, str], files_zip: Optional[ZipFile] = None, storage: Optional[Storage] = None, ) -> Optional[UserFile]
