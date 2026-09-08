def test_billing_api_has_a_stable_namespace():
    from django.urls import reverse

    assert reverse("api:jadawel_billing:checkout_options") == "/api/billing/checkout/"
