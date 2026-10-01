from django.apps import AppConfig


class AutomationConfig(AppConfig):
    name = "jadawel.contrib.automation"

    def ready(self):
        from jadawel.contrib.automation.action_scopes import WorkflowActionScopeType
        from jadawel.contrib.automation.application_types import (
            AutomationApplicationType,
        )
        from jadawel.contrib.automation.nodes.actions import (
            CreateAutomationNodeActionType,
            DeleteAutomationNodeActionType,
            DuplicateAutomationNodeActionType,
            MoveAutomationNodeActionType,
            ReplaceAutomationNodeActionType,
            UpdateAutomationNodeActionType,
        )
        from jadawel.contrib.automation.nodes.node_types import (
            AIAgentActionNodeType,
            CoreHttpRequestNodeType,
            CoreHTTPTriggerNodeType,
            CoreInboundEmailTriggerNodeType,
            CoreIteratorNodeType,
            CorePeriodicTriggerNodeType,
            CoreResponseNodeType,
            CoreRouterActionNodeType,
            CoreSMTPEmailNodeType,
            LocalJadawelAggregateRowsNodeType,
            LocalJadawelCreateRowNodeType,
            LocalJadawelDeleteRowNodeType,
            LocalJadawelGetRowNodeType,
            LocalJadawelListRowsNodeType,
            LocalJadawelRowsCreatedNodeTriggerType,
            LocalJadawelRowsDeletedNodeTriggerType,
            LocalJadawelRowsUpdatedNodeTriggerType,
            LocalJadawelUpdateRowNodeType,
            SlackWriteMessageActionNodeType,
        )
        from jadawel.contrib.automation.nodes.object_scopes import (
            AutomationNodeObjectScopeType,
        )
        from jadawel.contrib.automation.nodes.operations import (
            CreateAutomationNodeOperationType,
            DeleteAutomationNodeOperationType,
            DuplicateAutomationNodeOperationType,
            ListAutomationNodeOperationType,
            OrderAutomationNodeOperationType,
            ReadAutomationNodeOperationType,
            RestoreAutomationNodeOperationType,
            UpdateAutomationNodeOperationType,
        )
        from jadawel.contrib.automation.nodes.registries import (
            ReplaceAutomationNodeTrashOperationType,
            automation_node_type_registry,
        )
        from jadawel.contrib.automation.nodes.trash_types import (
            AutomationNodeTrashableItemType,
        )
        from jadawel.contrib.automation.object_scopes import AutomationObjectScopeType
        from jadawel.contrib.automation.operations import (
            ListAutomationWorkflowsOperationType,
            OrderAutomationWorkflowsOperationType,
        )
        from jadawel.contrib.automation.trash_types import AutomationTrashableItemType
        from jadawel.contrib.automation.workflows.actions import (
            CreateAutomationWorkflowActionType,
            DeleteAutomationWorkflowActionType,
            DuplicateAutomationWorkflowActionType,
            OrderAutomationWorkflowActionType,
            UpdateAutomationWorkflowActionType,
        )
        from jadawel.contrib.automation.workflows.job_types import (
            DuplicateAutomationWorkflowJobType,
            PublishAutomationWorkflowJobType,
        )
        from jadawel.contrib.automation.workflows.object_scopes import (
            AutomationWorkflowObjectScopeType,
        )
        from jadawel.contrib.automation.workflows.operations import (
            CreateAutomationWorkflowOperationType,
            DeleteAutomationWorkflowOperationType,
            DuplicateAutomationWorkflowOperationType,
            PublishAutomationWorkflowOperationType,
            ReadAutomationWorkflowOperationType,
            RestoreAutomationWorkflowOperationType,
            UpdateAutomationWorkflowOperationType,
        )
        from jadawel.contrib.automation.workflows.trash_types import (
            AutomationWorkflowTrashableItemType,
        )
        from jadawel.core.action.registries import (
            action_scope_registry,
            action_type_registry,
        )
        from jadawel.core.jobs.registries import job_type_registry
        from jadawel.core.notifications.registries import notification_type_registry
        from jadawel.core.registries import (
            application_type_registry,
            object_scope_type_registry,
            operation_type_registry,
        )
        from jadawel.core.trash.registries import trash_item_type_registry

        application_type_registry.register(AutomationApplicationType())

        object_scope_type_registry.register(AutomationObjectScopeType())
        object_scope_type_registry.register(AutomationWorkflowObjectScopeType())
        object_scope_type_registry.register(AutomationNodeObjectScopeType())

        from jadawel.contrib.automation.workflows.last_viewed_types import (
            AutomationWorkflowLastViewedItemType,
        )
        from jadawel.core.registries import last_viewed_item_type_registry

        last_viewed_item_type_registry.register(AutomationWorkflowLastViewedItemType())

        operation_type_registry.register(CreateAutomationWorkflowOperationType())
        operation_type_registry.register(DeleteAutomationWorkflowOperationType())
        operation_type_registry.register(DuplicateAutomationWorkflowOperationType())
        operation_type_registry.register(ReadAutomationWorkflowOperationType())
        operation_type_registry.register(UpdateAutomationWorkflowOperationType())
        operation_type_registry.register(ListAutomationWorkflowsOperationType())
        operation_type_registry.register(OrderAutomationWorkflowsOperationType())
        operation_type_registry.register(RestoreAutomationWorkflowOperationType())
        operation_type_registry.register(PublishAutomationWorkflowOperationType())
        operation_type_registry.register(ListAutomationNodeOperationType())
        operation_type_registry.register(CreateAutomationNodeOperationType())
        operation_type_registry.register(UpdateAutomationNodeOperationType())
        operation_type_registry.register(ReadAutomationNodeOperationType())
        operation_type_registry.register(DeleteAutomationNodeOperationType())
        operation_type_registry.register(RestoreAutomationNodeOperationType())
        operation_type_registry.register(DuplicateAutomationNodeOperationType())
        operation_type_registry.register(OrderAutomationNodeOperationType())

        job_type_registry.register(DuplicateAutomationWorkflowJobType())
        job_type_registry.register(PublishAutomationWorkflowJobType())

        trash_item_type_registry.register(AutomationTrashableItemType())
        trash_item_type_registry.register(AutomationWorkflowTrashableItemType())
        trash_item_type_registry.register(AutomationNodeTrashableItemType())

        action_type_registry.register(CreateAutomationWorkflowActionType())
        action_type_registry.register(UpdateAutomationWorkflowActionType())
        action_type_registry.register(DeleteAutomationWorkflowActionType())
        action_type_registry.register(DuplicateAutomationWorkflowActionType())
        action_type_registry.register(OrderAutomationWorkflowActionType())
        action_type_registry.register(CreateAutomationNodeActionType())
        action_type_registry.register(UpdateAutomationNodeActionType())
        action_type_registry.register(DeleteAutomationNodeActionType())
        action_type_registry.register(DuplicateAutomationNodeActionType())
        action_type_registry.register(ReplaceAutomationNodeActionType())
        action_type_registry.register(MoveAutomationNodeActionType())

        from jadawel.contrib.automation.notification_types import (
            WorkflowDisabledNotificationType,
        )

        notification_type_registry.register(WorkflowDisabledNotificationType())

        action_scope_registry.register(WorkflowActionScopeType())

        from jadawel.core.registries import permission_manager_type_registry

        from .permission_manager import AllowIfTemplatePermissionManagerType

        prev_manager = permission_manager_type_registry.get(
            AllowIfTemplatePermissionManagerType.type
        )
        permission_manager_type_registry.unregister(
            AllowIfTemplatePermissionManagerType.type
        )
        permission_manager_type_registry.register(
            AllowIfTemplatePermissionManagerType(prev_manager)
        )

        automation_node_type_registry.register(LocalJadawelCreateRowNodeType())
        automation_node_type_registry.register(LocalJadawelUpdateRowNodeType())
        automation_node_type_registry.register(LocalJadawelDeleteRowNodeType())
        automation_node_type_registry.register(LocalJadawelGetRowNodeType())
        automation_node_type_registry.register(LocalJadawelListRowsNodeType())
        automation_node_type_registry.register(LocalJadawelAggregateRowsNodeType())
        automation_node_type_registry.register(CoreHttpRequestNodeType())
        automation_node_type_registry.register(CoreIteratorNodeType())
        automation_node_type_registry.register(CoreSMTPEmailNodeType())
        automation_node_type_registry.register(CoreRouterActionNodeType())
        automation_node_type_registry.register(CoreResponseNodeType())
        automation_node_type_registry.register(LocalJadawelRowsCreatedNodeTriggerType())
        automation_node_type_registry.register(LocalJadawelRowsUpdatedNodeTriggerType())
        automation_node_type_registry.register(LocalJadawelRowsDeletedNodeTriggerType())
        automation_node_type_registry.register(CorePeriodicTriggerNodeType())
        automation_node_type_registry.register(CoreHTTPTriggerNodeType())
        automation_node_type_registry.register(CoreInboundEmailTriggerNodeType())
        automation_node_type_registry.register(AIAgentActionNodeType())
        automation_node_type_registry.register(SlackWriteMessageActionNodeType())

        from jadawel.core.trash.registries import trash_operation_type_registry

        trash_operation_type_registry.register(
            ReplaceAutomationNodeTrashOperationType()
        )

        from jadawel.contrib.automation.data_providers.data_provider_types import (
            CurrentIterationDataProviderType,
            PreviousNodeProviderType,
        )
        from jadawel.contrib.automation.data_providers.registries import (
            automation_data_provider_type_registry,
        )

        automation_data_provider_type_registry.register(PreviousNodeProviderType())
        automation_data_provider_type_registry.register(
            CurrentIterationDataProviderType()
        )

        from jadawel.contrib.automation.nodes.permission_manager import (
            AutomationNodePermissionManager,
        )
        from jadawel.contrib.automation.workflows.permission_manager import (
            AutomationWorkflowPermissionManager,
        )
        from jadawel.core.registries import permission_manager_type_registry

        permission_manager_type_registry.register(AutomationWorkflowPermissionManager())
        permission_manager_type_registry.register(AutomationNodePermissionManager())

        # The signals must always be imported last because they use
        # the registries which need to be filled first.
        import jadawel.contrib.automation.nodes.ws.signals  # noqa: F403, F401
        import jadawel.contrib.automation.workflows.receivers  # noqa: F401
        import jadawel.contrib.automation.workflows.signals  # noqa: F403, F401
        import jadawel.contrib.automation.workflows.ws.signals  # noqa: F403, F401
        import jadawel.contrib.integrations.tasks  # noqa: F403, F401
        from jadawel.contrib.automation.nodes.receivers import (
            connect_to_node_pre_delete_signal,
        )

        connect_to_node_pre_delete_signal()

        from jadawel.contrib.automation.search_types import AutomationSearchType
        from jadawel.core.search.registries import workspace_search_registry

        workspace_search_registry.register(AutomationSearchType())
