from django.urls import path

from jadawel_billing.api.checkout import (
    AccountView,
    CheckoutOptionsView,
    OrdersView,
    VerifyOrderView,
)
from jadawel_billing.api.grants import (
    AdminAccountAuditView,
    AdminGrantPreviewView,
    AdminGrantView,
    AdminRevokeGrantView,
    AdminSuspensionView,
)
from jadawel_billing.api.payments import (
    AdminOrdersView,
    AdminProviderEventsView,
    AdminProviderHealthView,
    AdminReconcileOrderView,
)
from jadawel_billing.api.subscriptions import (
    AdminExternalPaymentView,
    AdminRefundView,
    CancellationView,
    PaymentMethodDeleteView,
    PaymentMethodsView,
    SeatIncreaseView,
    SubscriptionChangeView,
)
from jadawel_billing.api.views import (
    AdminAccountsView,
    AdminPlansView,
    AdminPlanView,
    AdminPricesView,
    AdminPriceView,
)
from jadawel_billing.api.webhooks import MoyasarWebhookView

app_name = "jadawel_billing"
urlpatterns = [
    path("moyasar/webhook/", MoyasarWebhookView.as_view(), name="moyasar_webhook"),
    path("checkout/", CheckoutOptionsView.as_view(), name="checkout_options"),
    path("orders/", OrdersView.as_view(), name="orders"),
    path(
        "orders/<uuid:order_id>/verify/", VerifyOrderView.as_view(), name="verify_order"
    ),
    path("accounts/<uuid:account_id>/", AccountView.as_view(), name="account"),
    path(
        "accounts/<uuid:account_id>/payment-methods/",
        PaymentMethodsView.as_view(),
        name="payment_methods",
    ),
    path(
        "accounts/<uuid:account_id>/payment-methods/<int:method_id>/",
        PaymentMethodDeleteView.as_view(),
        name="payment_method_delete",
    ),
    path(
        "accounts/<uuid:account_id>/subscription/cancellation/",
        CancellationView.as_view(),
        name="subscription_cancellation",
    ),
    path(
        "accounts/<uuid:account_id>/subscription/change/",
        SubscriptionChangeView.as_view(),
        name="subscription_change",
    ),
    path(
        "accounts/<uuid:account_id>/subscription/seat-increase/",
        SeatIncreaseView.as_view(),
        name="subscription_seat_increase",
    ),
    path(
        "admin/accounts/<uuid:account_id>/grant/",
        AdminGrantView.as_view(),
        name="admin_grant",
    ),
    path(
        "admin/accounts/<uuid:account_id>/grant/preview/",
        AdminGrantPreviewView.as_view(),
        name="admin_grant_preview",
    ),
    path(
        "admin/accounts/<uuid:account_id>/grant/revoke/",
        AdminRevokeGrantView.as_view(),
        name="admin_revoke_grant",
    ),
    path(
        "admin/accounts/<uuid:account_id>/suspension/",
        AdminSuspensionView.as_view(),
        name="admin_suspension",
    ),
    path(
        "admin/accounts/<uuid:account_id>/audit/",
        AdminAccountAuditView.as_view(),
        name="admin_account_audit",
    ),
    path("admin/accounts/", AdminAccountsView.as_view(), name="admin_accounts"),
    path("admin/plans/", AdminPlansView.as_view(), name="admin_plans"),
    path("admin/plans/<int:pk>/", AdminPlanView.as_view(), name="admin_plan"),
    path(
        "admin/plans/<int:plan_id>/prices/",
        AdminPricesView.as_view(),
        name="admin_prices",
    ),
    path("admin/prices/<int:pk>/", AdminPriceView.as_view(), name="admin_price"),
    path("admin/orders/", AdminOrdersView.as_view(), name="admin_orders"),
    path(
        "admin/provider-events/",
        AdminProviderEventsView.as_view(),
        name="admin_provider_events",
    ),
    path(
        "admin/provider-health/",
        AdminProviderHealthView.as_view(),
        name="admin_provider_health",
    ),
    path(
        "admin/orders/<uuid:order_id>/reconcile/",
        AdminReconcileOrderView.as_view(),
        name="admin_reconcile_order",
    ),
    path(
        "admin/orders/<uuid:order_id>/refund/",
        AdminRefundView.as_view(),
        name="admin_refund",
    ),
    path(
        "admin/external-payments/",
        AdminExternalPaymentView.as_view(),
        name="admin_external_payment",
    ),
]
