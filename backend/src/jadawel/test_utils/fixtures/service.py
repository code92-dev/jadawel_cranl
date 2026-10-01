from uuid import uuid4

from jadawel.contrib.integrations.ai.models import AIAgentService
from jadawel.contrib.integrations.core.models import (
    CoreHTTPRequestService,
    CoreHTTPTriggerService,
    CoreIteratorService,
    CorePeriodicService,
    CoreResponseService,
    CoreRouterService,
    CoreSMTPEmailService,
)
from jadawel.contrib.integrations.local_jadawel.models import (
    LocalJadawelAggregateRows,
    LocalJadawelDeleteRow,
    LocalJadawelGetRow,
    LocalJadawelListRows,
    LocalJadawelRowsCreated,
    LocalJadawelRowsDeleted,
    LocalJadawelRowsUpdated,
    LocalJadawelTableServiceFilter,
    LocalJadawelTableServiceSort,
    LocalJadawelUpsertRow,
)
from jadawel.contrib.integrations.slack.models import SlackWriteMessageService
from jadawel.core.services.registries import service_type_registry


class ServiceFixtures:
    def create_local_jadawel_get_row_service(self, **kwargs) -> LocalJadawelGetRow:
        service = self.create_service(LocalJadawelGetRow, **kwargs)
        return service

    def create_local_jadawel_list_rows_service(self, **kwargs) -> LocalJadawelListRows:
        service = self.create_service(LocalJadawelListRows, **kwargs)
        return service

    def create_local_jadawel_upsert_row_service(
        self, **kwargs
    ) -> LocalJadawelUpsertRow:
        service = self.create_service(LocalJadawelUpsertRow, **kwargs)
        return service

    def create_local_jadawel_delete_row_service(
        self, **kwargs
    ) -> LocalJadawelDeleteRow:
        service = self.create_service(LocalJadawelDeleteRow, **kwargs)
        return service

    def create_local_jadawel_aggregate_rows_service(
        self, **kwargs
    ) -> LocalJadawelAggregateRows:
        service = self.create_service(LocalJadawelAggregateRows, **kwargs)
        return service

    def create_local_jadawel_rows_created_service(
        self, **kwargs
    ) -> LocalJadawelRowsCreated:
        service = self.create_service(LocalJadawelRowsCreated, **kwargs)
        return service

    def create_local_jadawel_rows_updated_service(
        self, **kwargs
    ) -> LocalJadawelRowsUpdated:
        service = self.create_service(LocalJadawelRowsUpdated, **kwargs)
        return service

    def create_local_jadawel_rows_deleted_service(
        self, **kwargs
    ) -> LocalJadawelRowsDeleted:
        service = self.create_service(LocalJadawelRowsDeleted, **kwargs)
        return service

    def create_local_jadawel_table_service_filter(
        self, **kwargs
    ) -> LocalJadawelTableServiceFilter:
        if "type" not in kwargs:
            kwargs["type"] = "equal"
        if "order" not in kwargs:
            kwargs["order"] = 0
        return LocalJadawelTableServiceFilter.objects.create(**kwargs)

    def create_local_jadawel_table_service_sort(
        self, **kwargs
    ) -> LocalJadawelTableServiceSort:
        return LocalJadawelTableServiceSort.objects.create(**kwargs)

    def create_core_http_request_service(self, **kwargs) -> CoreHTTPRequestService:
        service = self.create_service(CoreHTTPRequestService, **kwargs)
        return service

    def create_core_smtp_email_service(self, **kwargs) -> CoreSMTPEmailService:
        if "from_email" not in kwargs:
            kwargs["from_email"] = "'sender@example.com'"
        if "to_emails" not in kwargs:
            kwargs["to_emails"] = "'recipient@example.com'"
        if "subject" not in kwargs:
            kwargs["subject"] = "'Test Subject'"
        if "body" not in kwargs:
            kwargs["body"] = "'Test email body'"
        if "body_type" not in kwargs:
            kwargs["body_type"] = "plain"

        service = self.create_service(CoreSMTPEmailService, **kwargs)
        return service

    def create_ai_agent_service(self, **kwargs):
        return self.create_service(AIAgentService, **kwargs)

    def create_slack_write_message_service(self, **kwargs):
        return self.create_service(SlackWriteMessageService, **kwargs)

    def create_core_iterator_service(self, **kwargs):
        return self.create_service(CoreIteratorService, **kwargs)

    def create_core_response_service(self, **kwargs):
        return self.create_service(CoreResponseService, **kwargs)

    def create_core_router_service(self, **kwargs):
        return self.create_service(CoreRouterService, **kwargs)

    def create_core_router_service_edge(self, service: CoreRouterService, **kwargs):
        output_node = kwargs.pop("output_node", None)
        skip_output_node = kwargs.pop("skip_output_node", False)
        edge_label = kwargs.get("label", "Edge")
        output_label = kwargs.pop("output_label", f"{edge_label} output node")

        edge = service.edges.create(**kwargs)

        if output_node is None and not skip_output_node:
            router_node = service.automation_workflow_node
            self.create_local_jadawel_create_row_action_node(
                reference_node=router_node,
                output=edge.uid,
                position="south",
                workflow=router_node.workflow,
                label=output_label,
            )

        return edge

    def create_core_http_trigger_service(self, **kwargs) -> CoreSMTPEmailService:
        if "uid" not in kwargs:
            kwargs["uid"] = uuid4()

        return self.create_service(CoreHTTPTriggerService, **kwargs)

    def create_core_periodic_service(self, **kwargs) -> CorePeriodicService:
        return self.create_service(CorePeriodicService, **kwargs)

    def create_service(self, model_class, **kwargs):
        if "integration" not in kwargs:
            integration = None
            integrations_args = kwargs.pop("integration_args", {})
            service_type = service_type_registry.get_by_model(model_class)
            if service_type.get_integration_type():
                integration = self.create_integration(
                    service_type.get_integration_type().model_class, **integrations_args
                )
        else:
            integration = kwargs.pop("integration", None)
            kwargs.pop("integration_args", None)

        service = model_class.objects.create(integration=integration, **kwargs)

        return service
