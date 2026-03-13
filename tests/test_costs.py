from resumecraftr.cli.utils.costs import (
    PricingInfo,
    OPENAI_PRICING,
    ANTHROPIC_PRICING,
    get_model_pricing,
    _approx_tokens,
)


def test_openai_pricing_has_expected_entries():
    assert "gpt-4o-mini" in OPENAI_PRICING
    info = OPENAI_PRICING["gpt-4o-mini"]
    assert isinstance(info, PricingInfo)
    assert info.prompt > 0
    assert info.completion > 0


def test_anthropic_pricing_has_expected_entries():
    assert "claude-sonnet-4-6" in ANTHROPIC_PRICING
    info = ANTHROPIC_PRICING["claude-sonnet-4-6"]
    assert isinstance(info, PricingInfo)
    assert info.prompt > 0
    assert info.completion > 0


def test_get_model_pricing_for_openai_and_anthropic():
    openai_conf = {"provider": "openai", "model": "gpt-4o-mini"}
    anthropic_conf = {"provider": "anthropic", "model": "claude-sonnet-4-6"}

    openai_price = get_model_pricing(openai_conf)
    anthropic_price = get_model_pricing(anthropic_conf)

    assert isinstance(openai_price, PricingInfo)
    assert isinstance(anthropic_price, PricingInfo)
    assert openai_price.prompt > 0
    assert anthropic_price.prompt > 0


def test_approx_tokens_rounds_reasonably():
    assert _approx_tokens(0) == 1
    assert _approx_tokens(4) == 1
    assert _approx_tokens(8) == 2
    assert _approx_tokens(1000) == 250

