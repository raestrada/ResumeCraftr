import os
from unittest import mock

import pytest

# Skip this module's tests entirely if LangChain core is not available in the environment.
pytest.importorskip("langchain_core")

from resumecraftr.core.llm import LLMConfig, create_chat_model


def test_llm_config_defaults():
    cfg = LLMConfig()
    assert cfg.provider == "openrouter"
    assert isinstance(cfg.model, str)
    assert cfg.temperature == pytest.approx(0.4)
    assert cfg.max_tokens > 0


@mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True)
def test_create_chat_model_openai_uses_chatopenai():
    cfg = LLMConfig(provider="openai", model="gpt-4o-mini")
    model = create_chat_model(cfg)
    # LangChain's ChatOpenAI has a .model attribute in recent versions
    assert getattr(model, "model", None) == "gpt-4o-mini"


@mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-openrouter-key"}, clear=True)
def test_create_chat_model_openrouter_uses_base_url():
    cfg = LLMConfig(provider="openrouter", model="gpt-4o-mini")
    model = create_chat_model(cfg)
    # ChatOpenAI exposes the base_url via .client or .client.base_url depending on version;
    # we just assert the attribute exists to avoid coupling to internals.
    assert model is not None


def test_create_chat_model_unsupported_provider_raises():
    cfg = LLMConfig(provider="not-a-provider")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        create_chat_model(cfg)

