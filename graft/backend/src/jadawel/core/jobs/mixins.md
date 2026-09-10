# backend/src/jadawel/core/jobs/mixins.py

- JobWithUserDataMixin · class · L16-L63 — class JobWithUserDataMixin(models.Model)
- save_user_data_if_not_present · method · L24-L35 — def save_user_data_if_not_present(self, user: AbstractUser) -> None
- restore_user_data_if_present · method · L37-L47 — def restore_user_data_if_present(self, user: AbstractUser) -> None
- save · method · L49-L51 — def save(self, *args, **kwargs)
- __getattribute__ · method · L53-L60 — def __getattribute__(self, name: str) -> Any
- Meta · class · L62-L63 — class Meta
- JobWithUserIpAddress · class · L66-L93 — class JobWithUserIpAddress(JobWithUserDataMixin)
- _save_user_data_if_not_present · method · L71-L80 — def _save_user_data_if_not_present(self, user: AbstractUser) -> None
- _restore_user_data_if_present · method · L82-L90 — def _restore_user_data_if_present(self, user: AbstractUser) -> None
- Meta · class · L92-L93 — class Meta
- JobWithWebsocketId · class · L96-L130 — class JobWithWebsocketId(JobWithUserDataMixin)
- _save_user_data_if_not_present · method · L108-L117 — def _save_user_data_if_not_present(self, user: AbstractUser) -> None
- _restore_user_data_if_present · method · L119-L127 — def _restore_user_data_if_present(self, user: AbstractUser) -> None
- Meta · class · L129-L130 — class Meta
- JobWithUndoRedoIds · class · L133-L178 — class JobWithUndoRedoIds(JobWithUserDataMixin)
- _save_user_data_if_not_present · method · L150-L162 — def _save_user_data_if_not_present(self, user: AbstractUser) -> None
- _restore_user_data_if_present · method · L164-L175 — def _restore_user_data_if_present(self, user: AbstractUser) -> None
- Meta · class · L177-L178 — class Meta
