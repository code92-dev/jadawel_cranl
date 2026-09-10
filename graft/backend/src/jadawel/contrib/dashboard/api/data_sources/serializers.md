# backend/src/jadawel/contrib/dashboard/api/data_sources/serializers.py

- DashboardDataSourceSerializer · class · L9-L90 — class DashboardDataSourceSerializer(ServiceSerializer)
- _get_service_instance · method · L28-L34 — def _get_service_instance(self, instance): # We generate the service schema using a `Service` instance. # If the `instance` is a `DashboardDataSource` instance, traverse its # 1-1 relation to `Service` and serialize it.
- get_type · method · L37-L42 — def get_type(self, instance)
- get_id · method · L45-L46 — def get_id(self, instance)
- get_name · method · L49-L50 — def get_name(self, instance)
- get_dashboard_id · method · L53-L54 — def get_dashboard_id(self, instance)
- get_order · method · L57-L58 — def get_order(self, instance)
- get_schema · method · L61-L65 — def get_schema(self, instance)
- get_context_data · method · L68-L73 — def get_context_data(self, instance)
- get_context_data_schema · method · L76-L81 — def get_context_data_schema(self, instance)
- Meta · class · L83-L90 — class Meta(ServiceSerializer.Meta)
- UpdateDashboardDataSourceSerializer · class · L93-L97 — class UpdateDashboardDataSourceSerializer(UpdateServiceSerializer)
- Meta · class · L96-L97 — class Meta(ServiceSerializer.Meta)
