"""``arabase.generative_ai.usage``: token counts survive genai-prices' extras."""

from pydantic_ai.usage import RequestUsage

# A real OpenRouter usage block (DeepSeek), as the OpenAI client dumps it.
OPENROUTER_USAGE = {
    "completion_tokens": 33,
    "prompt_tokens": 32,
    "total_tokens": 65,
    "completion_tokens_details": {
        "audio_tokens": 0,
        "reasoning_tokens": 30,
        "image_tokens": 0,
    },
    "prompt_tokens_details": {
        "audio_tokens": 0,
        "cached_tokens": 0,
        "cache_write_tokens": 0,
        "video_tokens": 0,
    },
    "cost": 1.704e-05,
    "is_byok": False,
    "cost_details": {"upstream_inference_cost": 1.704e-05},
}


def extract():
    return RequestUsage.extract(
        {"model": "deepseek/deepseek-v4.1-flash", "usage": OPENROUTER_USAGE},
        provider="openrouter",
        provider_url="https://openrouter.ai/api/v1",
        provider_fallback="openai",
        api_flavor="chat",
        details={"reasoning_tokens": 30},
    )


def test_a_reasoning_models_tokens_are_counted():
    # Installed by ArabaseConfig.ready().
    usage = extract()

    assert (usage.input_tokens, usage.output_tokens) == (32, 33)
    assert usage.details["reasoning_tokens"] == 30


def test_the_wrapper_is_still_needed():
    """Fails once pydantic-ai accepts every field genai-prices returns; then
    delete ``arabase/generative_ai/usage.py`` and its call in ``apps.py``."""

    original = RequestUsage.extract.__func__.__wrapped__
    usage = original(
        RequestUsage,
        {"model": "deepseek/deepseek-v4.1-flash", "usage": OPENROUTER_USAGE},
        provider="openrouter",
        provider_url="https://openrouter.ai/api/v1",
        provider_fallback="openai",
        api_flavor="chat",
    )

    assert usage.input_tokens == 0 and usage.output_tokens == 0
