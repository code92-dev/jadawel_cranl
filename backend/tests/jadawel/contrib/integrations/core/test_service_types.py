from jadawel.contrib.integrations.core.service_types import (
    CoreHTTPRequestServiceType,
    CorePeriodicServiceType,
    CoreResponseServiceType,
    CoreRouterServiceType,
    CoreServiceType,
    CoreSMTPEmailServiceType,
)
from jadawel.core.services.registries import DispatchTypes, service_type_registry


def test_core_service_type_dispatch_types():
    core_dispatch_types = {
        service_type.type: service_type.dispatch_types
        for service_type in service_type_registry.get_all()
        if isinstance(service_type, CoreServiceType)
    }
    assert core_dispatch_types == {
        CoreHTTPRequestServiceType.type: [DispatchTypes.ACTION],
        CoreSMTPEmailServiceType.type: [DispatchTypes.ACTION],
        CoreRouterServiceType.type: [DispatchTypes.ACTION],
        CorePeriodicServiceType.type: [DispatchTypes.EVENT],
        CoreResponseServiceType.type: [DispatchTypes.ACTION],
    }
