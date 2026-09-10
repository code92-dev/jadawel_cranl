# backend/src/jadawel/contrib/database/export/models.py

- ExportJob · class · L30-L89 — class ExportJob(models.Model)
- is_cancelled_or_expired · method · L51-L52 — def is_cancelled_or_expired(self)
- unfinished_jobs · method · L55-L58 — def unfinished_jobs(user)
- workspace_id · method · L61-L64 — def workspace_id(self): # FIXME: Temporarily setting the current workspace ID for URL generation in # storage backends, enabling permission checks at download time.
- jobs_requiring_cleanup · method · L67-L84 — def jobs_requiring_cleanup(current_time)
- Meta · class · L86-L89 — class Meta
