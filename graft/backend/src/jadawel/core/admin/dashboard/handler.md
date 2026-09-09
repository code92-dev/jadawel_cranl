# backend/src/jadawel/core/admin/dashboard/handler.py

- AdminDashboardHandler · class · L11-L190 — class AdminDashboardHandler
- get_counts_from_delta_range · method · L12-L102 — def get_counts_from_delta_range( self, queryset, date_field_name, delta_mapping, expression="pk", now=None, distinct=False, additional_filters=None, include_previous=False, )
- get_count · function · L79-L90 — def get_count(start, end)
- get_new_user_counts · method · L104-L111 — def get_new_user_counts(self, delta_mapping, now=None, include_previous=False)
- get_active_user_count · method · L113-L123 — def get_active_user_count(self, delta_mapping, now=None, include_previous=False)
- get_new_user_count_per_day · method · L125-L155 — def get_new_user_count_per_day(self, delta, now=None)
- get_active_user_count_per_day · method · L157-L190 — def get_active_user_count_per_day(self, delta, now=None)
