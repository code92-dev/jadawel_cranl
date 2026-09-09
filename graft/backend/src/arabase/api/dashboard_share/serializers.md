# backend/src/arabase/api/dashboard_share/serializers.py

- DashboardShareSerializer · class · L10-L24 — class DashboardShareSerializer(serializers.ModelSerializer)
- Meta · class · L18-L24 — class Meta
- UpdateDashboardSharePasswordSerializer · class · L32-L44 — class UpdateDashboardSharePasswordSerializer(serializers.Serializer)
- PublicDashboardAuthSerializer · class · L47-L52 — class PublicDashboardAuthSerializer(serializers.Serializer): # Deliberately not length-checked: this is the guess, not the policy, and # rejecting a short one early would confirm the shape of the real password.
- PublicDashboardAuthResponseSerializer · class · L55-L61 — class PublicDashboardAuthResponseSerializer(serializers.Serializer)
- PublicDashboardSerializer · class · L64-L78 — class PublicDashboardSerializer(serializers.ModelSerializer)
- Meta · class · L71-L78 — class Meta
- PublicDashboardDataSourceSerializer · class · L81-L141 — class PublicDashboardDataSourceSerializer(PublicServiceSerializer)
- get_id · method · L109-L110 — def get_id(self, instance)
- get_name · method · L113-L114 — def get_name(self, instance)
- get_dashboard_id · method · L117-L118 — def get_dashboard_id(self, instance)
- get_order · method · L121-L122 — def get_order(self, instance)
- get_date_field_id · method · L125-L126 — def get_date_field_id(self, instance)
- Meta · class · L128-L141 — class Meta(PublicServiceSerializer.Meta)
