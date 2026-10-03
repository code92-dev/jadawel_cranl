from typing import Any, Dict, Generator, Union

from django.contrib.auth.models import AbstractUser
from django.db.models import Prefetch

from rest_framework import serializers

from jadawel.api.services.serializers import (
    PolymorphicServiceRequestSerializer,
    PolymorphicServiceSerializer,
    PublicPolymorphicServiceSerializer,
)
from jadawel.contrib.builder.data_sources.builder_dispatch_context import (
    BuilderDispatchContext,
)
from jadawel.contrib.builder.elements.element_types import NavigationElementManager
from jadawel.contrib.builder.workflow_actions.models import (
    AIAgentWorkflowAction,
    CoreHTTPRequestWorkflowAction,
    CoreSMTPEmailWorkflowAction,
    LocalJadawelCreateRowWorkflowAction,
    LocalJadawelDeleteRowWorkflowAction,
    LocalJadawelUpdateRowWorkflowAction,
    LogoutWorkflowAction,
    NotificationWorkflowAction,
    OpenPageWorkflowAction,
    RefreshDataSourceWorkflowAction,
    SlackWriteMessageWorkflowAction,
)
from jadawel.contrib.builder.workflow_actions.registries import (
    BuilderWorkflowActionType,
)
from jadawel.contrib.builder.workflow_actions.types import BuilderWorkflowActionDict
from jadawel.contrib.integrations.ai.service_types import AIAgentServiceType
from jadawel.contrib.integrations.core.service_types import (
    CoreHTTPRequestServiceType,
    CoreSMTPEmailServiceType,
)
from jadawel.contrib.integrations.local_jadawel.service_types import (
    LocalJadawelDeleteRowServiceType,
    LocalJadawelUpsertRowServiceType,
)
from jadawel.contrib.integrations.slack.service_types import (
    SlackWriteMessageServiceType,
)
from jadawel.core.db import specific_queryset
from jadawel.core.formula.field import JADAWEL_FORMULA_VERSION_INITIAL
from jadawel.core.formula.serializers import FormulaSerializerField
from jadawel.core.formula.types import JADAWEL_FORMULA_MODE_SIMPLE, JadawelFormulaObject
from jadawel.core.integrations.models import Integration
from jadawel.core.registry import Instance
from jadawel.core.services.handler import ServiceHandler
from jadawel.core.services.models import Service
from jadawel.core.services.registries import service_type_registry
from jadawel.core.services.types import DispatchResult
from jadawel.core.workflow_actions.models import WorkflowAction


class NotificationWorkflowActionType(BuilderWorkflowActionType):
    type = "notification"
    model_class = NotificationWorkflowAction
    simple_formula_fields = ["title", "description"]
    serializer_field_names = ["title", "description"]
    serializer_field_overrides = {
        "title": FormulaSerializerField(
            help_text="The title of the notification. Must be an formula.",
            required=False,
        ),
        "description": FormulaSerializerField(
            help_text="The description of the notification. Must be an formula.",
            required=False,
        ),
    }

    class SerializedDict(BuilderWorkflowActionDict):
        title: JadawelFormulaObject
        description: JadawelFormulaObject

    @property
    def allowed_fields(self):
        return super().allowed_fields + ["title", "description"]

    def get_pytest_params(self, pytest_data_fixture) -> Dict[str, JadawelFormulaObject]:
        return {
            "title": JadawelFormulaObject(
                formula="'hello'",
                version=JADAWEL_FORMULA_VERSION_INITIAL,
                mode=JADAWEL_FORMULA_MODE_SIMPLE,
            ),
            "description": JadawelFormulaObject(
                formula="'there'",
                version=JADAWEL_FORMULA_VERSION_INITIAL,
                mode=JADAWEL_FORMULA_MODE_SIMPLE,
            ),
        }


class OpenPageWorkflowActionType(BuilderWorkflowActionType):
    type = "open_page"
    model_class = OpenPageWorkflowAction
    simple_formula_fields = NavigationElementManager.simple_formula_fields

    @property
    def serializer_field_names(self):
        return (
            super().serializer_field_names
            + NavigationElementManager.serializer_field_names
        )

    @property
    def allowed_fields(self):
        return super().allowed_fields + NavigationElementManager.allowed_fields

    @property
    def serializer_field_overrides(self):
        return (
            super().serializer_field_overrides
            | NavigationElementManager().get_serializer_field_overrides()
        )

    class SerializedDict(
        BuilderWorkflowActionDict,
        NavigationElementManager.SerializedDict,
    ): ...

    def get_pytest_params(self, pytest_data_fixture):
        return NavigationElementManager().get_pytest_params(pytest_data_fixture)

    def formula_generator(
        self, workflow_action: WorkflowAction
    ) -> Generator[str | Instance, str, None]:
        """
        Generator that iterates over formulas for the OpenPageWorkflowActionType.

        In addition to formula fields, formulas can also be stored in the
        page_parameters JSON field.
        """

        yield from super().formula_generator(workflow_action)

        for index, page_parameter in enumerate(workflow_action.page_parameters):
            new_formula = yield JadawelFormulaObject.to_formula(
                page_parameter.get("value")
            )
            if new_formula is not None:
                workflow_action.page_parameters[index]["value"] = new_formula
                yield workflow_action

        for index, query_parameter in enumerate(workflow_action.query_parameters or []):
            new_formula = yield JadawelFormulaObject.to_formula(
                query_parameter.get("value")
            )
            if new_formula is not None:
                workflow_action.query_parameters[index]["value"] = new_formula
                yield workflow_action

    def deserialize_property(
        self,
        prop_name,
        value,
        id_mapping: Dict,
        files_zip=None,
        storage=None,
        cache=None,
        **kwargs,
    ) -> Any:
        return super().deserialize_property(
            prop_name,
            NavigationElementManager().deserialize_property(
                prop_name, value, id_mapping, **kwargs
            ),
            id_mapping,
            files_zip=files_zip,
            storage=storage,
            cache=cache,
            **kwargs,
        )


class LogoutWorkflowActionType(BuilderWorkflowActionType):
    type = "logout"
    model_class = LogoutWorkflowAction

    class SerializedDict(BuilderWorkflowActionDict): ...

    def get_pytest_params(self, pytest_data_fixture) -> Dict[str, Any]:
        return {}


class RefreshDataSourceWorkflowActionType(BuilderWorkflowActionType):
    type = "refresh_data_source"
    model_class = RefreshDataSourceWorkflowAction
    serializer_field_names = ["data_source_id"]
    serializer_field_overrides = {
        "data_source_id": serializers.IntegerField(
            allow_null=True,
            default=None,
            required=False,
            help_text="The ID of the Data Source to be refreshed.",
        ),
    }

    class SerializedDict(BuilderWorkflowActionDict):
        data_source_id: int

    def get_pytest_params(self, pytest_data_fixture) -> Dict[str, Any]:
        return {}

    @property
    def allowed_fields(self):
        return super().allowed_fields + ["data_source_id"]

    def deserialize_property(
        self,
        prop_name,
        value,
        id_mapping: Dict,
        files_zip=None,
        storage=None,
        cache=None,
        **kwargs,
    ) -> Any:
        data_sources = id_mapping.get("builder_data_sources", {})
        if prop_name == "data_source_id" and value in data_sources:
            return data_sources[value]

        return super().deserialize_property(
            prop_name,
            value,
            id_mapping,
            files_zip=files_zip,
            storage=storage,
            cache=cache,
            **kwargs,
        )


class BuilderWorkflowServiceActionType(BuilderWorkflowActionType):
    service_type = None  # Must be implemented by subclasses.
    serializer_field_names = ["service"]
    request_serializer_field_overrides = {
        "service": PolymorphicServiceRequestSerializer(
            default=None,
            required=False,
            help_text="The service which this workflow action is associated with.",
        )
    }
    is_server_workflow = True
    serializer_field_overrides = {
        "service": PolymorphicServiceSerializer(
            help_text="The service which this workflow action is associated with."
        )
    }
    request_serializer_field_names = ["service"]

    public_serializer_field_overrides = {
        "service": PublicPolymorphicServiceSerializer(
            help_text="The service which this workflow action is associated with."
        )
    }

    class SerializedDict(BuilderWorkflowActionDict):
        service: Dict

    @property
    def allowed_fields(self):
        return super().allowed_fields + ["service"]

    def get_pytest_params_serialized(
        self, pytest_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        service_type = service_type_registry.get_by_model(pytest_params["service"])
        return {"service": service_type.export_serialized(pytest_params["service"])}

    def serialize_property(
        self,
        workflow_action: WorkflowAction,
        prop_name: str,
        files_zip=None,
        storage=None,
        cache=None,
    ):
        """
        You can customize the behavior of the serialization of a property with this
        hook.
        """

        if prop_name == "service":
            service = workflow_action.service.specific
            return service.get_type().export_serialized(
                service, files_zip=files_zip, storage=storage, cache=cache
            )

        return super().serialize_property(
            workflow_action,
            prop_name,
            files_zip=files_zip,
            storage=storage,
            cache=cache,
        )

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: Dict[str, Any],
        files_zip=None,
        storage=None,
        cache=None,
        **kwargs,
    ) -> Any:
        """
        If the workflow action has a relation to a service, this method will
        map the service's new `integration_id` and call `import_service` on
        the serialized service values.

        :param prop_name: the name of the property being transformed.
        :param value: the value of this property.
        :param id_mapping: the id mapping dict.
        :return: the deserialized version for this property.
        """

        if prop_name == "service" and value:
            integration = None
            serialized_service = value
            integration_id = serialized_service.get("integration_id", None)
            if integration_id:
                integration_id = id_mapping["integrations"].get(
                    integration_id, integration_id
                )
                integration = Integration.objects.get(id=integration_id)

            # Jadawel fork: no import_formula here. The action's import_formulas
            # (registries.py) also yields the service formulas, with the element
            # import context, so importing them here too remapped every id twice:
            # a new id that matched another old id in the export pointed the
            # formula at the wrong field or action.
            return ServiceHandler().import_service(
                integration,
                serialized_service,
                id_mapping,
                storage=storage,
                cache=cache,
                files_zip=files_zip,
            )
        return super().deserialize_property(
            prop_name,
            value,
            id_mapping,
            files_zip=files_zip,
            storage=storage,
            cache=cache,
            **kwargs,
        )

    def prepare_values(
        self,
        values: Dict[str, Any],
        user: AbstractUser,
        instance: Union[
            LocalJadawelCreateRowWorkflowAction, LocalJadawelUpdateRowWorkflowAction
        ] = None,
    ):
        """
        Responsible for preparing the service based workflow action. By default,
        the only step is to pass any `service` data into the service.

        :param values: The full workflow action values to prepare.
        :param user: The user on whose behalf the change is made.
        :param instance: A `BuilderWorkflowServiceAction` subclass instance.
        :return: The modified workflow action values, prepared.
        """

        service_type = service_type_registry.get(self.service_type)

        if not instance:
            # If we haven't received a workflow action instance, we're preparing
            # as part of creating a new action. If this happens, we need to create
            # a new upsert row service.
            service = ServiceHandler().create_service(service_type)
        else:
            service = instance.service.specific

        # If we received any service values, prepare them.
        service_values = values.pop("service", None) or {}
        prepared_service_values = service_type.prepare_values(
            service_values, user, service if instance else None
        )

        # Update the service instance with any prepared service values.
        ServiceHandler().update_service(
            service_type, service, **prepared_service_values
        )

        values["service"] = service
        return super().prepare_values(values, user, instance)

    def formula_generator(
        self, workflow_action: WorkflowAction
    ) -> Generator[str | Instance, str, None]:
        """
        This formula generator includes the service formulas.
        """

        yield from super().formula_generator(workflow_action)

        # Now yield from the service
        service = workflow_action.service.specific
        yield from service.get_type().formula_generator(service)

    def enhance_queryset(self, queryset):
        return (
            super()
            .enhance_queryset(queryset)
            .prefetch_related(
                Prefetch(
                    "service",
                    queryset=specific_queryset(
                        Service.objects.all(),
                        per_content_type_queryset_hook=(
                            lambda service,
                            queryset: service_type_registry.get_by_model(
                                service
                            ).enhance_queryset(queryset)
                        ),
                    ),
                )
            )
        )

    def dispatch(
        self, workflow_action: WorkflowAction, dispatch_context: BuilderDispatchContext
    ) -> DispatchResult:
        return ServiceHandler().dispatch_service(
            workflow_action.service.specific, dispatch_context
        )


class LocalJadawelWorkflowActionType(BuilderWorkflowServiceActionType):
    pass


class UpsertRowWorkflowActionType(LocalJadawelWorkflowActionType):
    type = "upsert_row"
    service_type = LocalJadawelUpsertRowServiceType.type

    def get_pytest_params(self, pytest_data_fixture) -> Dict[str, int]:
        service = pytest_data_fixture.create_local_jadawel_upsert_row_service()
        return {"service": service}


class CreateRowWorkflowActionType(UpsertRowWorkflowActionType):
    type = "create_row"
    model_class = LocalJadawelCreateRowWorkflowAction


class UpdateRowWorkflowActionType(UpsertRowWorkflowActionType):
    type = "update_row"
    model_class = LocalJadawelUpdateRowWorkflowAction


class DeleteRowWorkflowActionType(LocalJadawelWorkflowActionType):
    type = "delete_row"
    model_class = LocalJadawelDeleteRowWorkflowAction
    service_type = LocalJadawelDeleteRowServiceType.type

    def get_pytest_params(self, pytest_data_fixture) -> Dict[str, int]:
        service = pytest_data_fixture.create_local_jadawel_delete_row_service()
        return {"service": service}


class CoreHttpRequestActionType(BuilderWorkflowServiceActionType):
    type = "http_request"
    model_class = CoreHTTPRequestWorkflowAction
    service_type = CoreHTTPRequestServiceType.type

    def get_pytest_params(self, pytest_data_fixture) -> Dict[str, int]:
        service = pytest_data_fixture.create_core_http_request_service()
        return {"service": service}


class CoreSMTPEmailActionType(BuilderWorkflowServiceActionType):
    type = "smtp_email"
    model_class = CoreSMTPEmailWorkflowAction
    service_type = CoreSMTPEmailServiceType.type

    def get_pytest_params(self, pytest_data_fixture) -> Dict[str, int]:
        service = pytest_data_fixture.create_core_smtp_email_service()
        return {"service": service}


class AIAgentWorkflowActionType(BuilderWorkflowServiceActionType):
    type = "ai_agent"
    model_class = AIAgentWorkflowAction
    service_type = AIAgentServiceType.type

    def get_pytest_params(self, pytest_data_fixture) -> Dict[str, int]:
        service = pytest_data_fixture.create_ai_agent_service()
        return {"service": service}


class SlackWriteMessageWorkflowActionType(BuilderWorkflowServiceActionType):
    type = "slack_write_message"
    model_class = SlackWriteMessageWorkflowAction
    service_type = SlackWriteMessageServiceType.type

    def get_pytest_params(self, pytest_data_fixture) -> Dict[str, int]:
        service = pytest_data_fixture.create_slack_write_message_service()
        return {"service": service}
