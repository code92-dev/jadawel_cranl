"""Keeps pydantic-ai's token counts when genai-prices reports more than it knows.

pydantic-ai 1.106 turns a provider's usage block into ``RequestUsage`` through
``RequestUsage.extract``, which asks genai-prices to read it and passes every
field back as a keyword. genai-prices 0.1.6 added ``output_reasoning_tokens``,
which ``RequestUsage`` has no field for, so the constructor raises, ``extract``
swallows the error, and the request is recorded as zero tokens. That happens for
every model that reports reasoning tokens — DeepSeek through OpenRouter, for
one — and it left Sanad's token budget (``arabase.sanad.budget``) counting
nothing.

``install`` wraps ``extract`` so the fields ``RequestUsage`` has are kept and
the rest go to ``details``. Remove it once pydantic-ai accepts them:
``test_generative_ai_usage.py`` fails when the wrapper is no longer needed.
"""

from functools import wraps

_REASONING_KEY = "reasoning_tokens"


def install() -> None:
    from genai_prices.data_snapshot import get_snapshot
    from pydantic_ai.usage import RequestUsage

    original = RequestUsage.extract.__func__
    if getattr(original, "_arabase_tolerant", False):
        return

    fields = set(RequestUsage.__dataclass_fields__) - {"details"}

    @wraps(original)
    def extract(cls, data, *, provider, provider_url, provider_fallback, **kwargs):
        usage = original(
            cls,
            data,
            provider=provider,
            provider_url=provider_url,
            provider_fallback=provider_fallback,
            **kwargs,
        )
        if usage.input_tokens or usage.output_tokens:
            return usage
        # The same lookup order as ``extract``, keeping what fits.
        api_flavor = kwargs.get("api_flavor", "default")
        details = dict(kwargs.get("details") or {})
        for provider_id, provider_api_url in (
            (None, provider_url),
            (provider, None),
            (provider_fallback, None),
        ):
            try:
                found = get_snapshot().find_provider(
                    None, provider_id, provider_api_url
                )
                _model, extracted = found.extract_usage(data, api_flavor=api_flavor)
            except Exception:  # noqa: BLE001, S112 - as ``extract`` does
                continue
            known, extra = {}, {}
            for key, value in extracted.__dict__.items():
                if value is None:
                    continue
                (known if key in fields else extra)[key] = value
            if "output_reasoning_tokens" in extra:
                details.setdefault(_REASONING_KEY, extra["output_reasoning_tokens"])
            return cls(**known, details=details)
        return usage

    extract._arabase_tolerant = True
    RequestUsage.extract = classmethod(extract)
