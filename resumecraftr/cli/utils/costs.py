from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.prompt import Confirm

from resumecraftr.cli.ui import console

PRICING_CACHE_PATH = Path("cv-workspace/.pricing_cache.json")
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # 1 week
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


@dataclass
class PricingInfo:
    prompt: float  # cost per token USD
    completion: float  # cost per token USD


def _load_pricing_cache() -> dict:
    if PRICING_CACHE_PATH.exists():
        try:
            with PRICING_CACHE_PATH.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}
    return {}


def _save_pricing_cache(cache: dict) -> None:
    PRICING_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PRICING_CACHE_PATH.open("w", encoding="utf-8") as fh:
        json.dump(cache, fh, indent=2, ensure_ascii=False)


def _openrouter_models_from_api() -> dict:
    headers = {"Accept": "application/json"}
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(OPENROUTER_MODELS_URL, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    models = {}
    for entry in data.get("data", []):
        pricing = entry.get("pricing") or {}
        prompt = float(pricing.get("prompt") or 0)
        completion = float(pricing.get("completion") or 0)
        for key in filter(None, [entry.get("id"), entry.get("name"), entry.get("canonical_slug")]):
            models[key] = {"prompt": prompt, "completion": completion}
    return models


def _get_openrouter_models() -> dict:
    cache = _load_pricing_cache()
    provider_cache = cache.get("openrouter", {})
    models = provider_cache.get("models") or {}
    timestamp = provider_cache.get("timestamp", 0)
    now = time.time()
    if not models or now - timestamp > CACHE_TTL_SECONDS:
        try:
            models = _openrouter_models_from_api()
            cache["openrouter"] = {"models": models, "timestamp": now}
            _save_pricing_cache(cache)
        except Exception:
            pass
    return models or provider_cache.get("models", {})


def _lookup_model(models: dict, model: str) -> Optional[PricingInfo]:
    if not models or not model:
        return None
    targets = {model, model.lower(), model.replace(":", "/"), model.replace(":", "-"), model.replace("/", "-")}
    for key, value in models.items():
        compare = {key, key.lower()}
        if targets & compare:
            return PricingInfo(prompt=float(value.get("prompt", 0)), completion=float(value.get("completion", 0)))
    return None


def _get_openrouter_pricing(model: str) -> Optional[PricingInfo]:
    models = _get_openrouter_models()
    return _lookup_model(models, model)


OPENAI_PRICING = {
    "gpt-4o-mini": PricingInfo(prompt=0.00000015, completion=0.0000006),  # $0.15 / $0.60 per MTok
    "gpt-4o": PricingInfo(prompt=0.0000005, completion=0.0000015),
    "gpt-4.1-mini": PricingInfo(prompt=0.0000003, completion=0.0000009),
    "gpt-4.1": PricingInfo(prompt=0.0000005, completion=0.0000015),
    "o1-mini": PricingInfo(prompt=0.000003, completion=0.000009),
    "o1-preview": PricingInfo(prompt=0.000015, completion=0.00006),
}


def _get_openai_pricing(model: str) -> Optional[PricingInfo]:
    models = _get_openrouter_models()
    pricing = _lookup_model(models, model)
    if pricing:
        return pricing
    if model in OPENAI_PRICING:
        return OPENAI_PRICING[model]
    key = model.split(":", 1)[0]
    return OPENAI_PRICING.get(key)


def get_model_pricing(llm_config: dict) -> Optional[PricingInfo]:
    provider = (llm_config or {}).get("provider", "").lower()
    model = llm_config.get("model")
    if not model:
        return None
    if provider == "openrouter":
        return _get_openrouter_pricing(model)
    if provider == "openai":
        return _get_openai_pricing(model)
    return None


def _approx_tokens(characters: int) -> int:
    return max(1, int(characters / 4))


def confirm_llm_budget(action: str, workspace_config: dict, prompt_characters: int, completion_ratio: float = 0.25) -> bool:
    if prompt_characters <= 0:
        return True
    if os.getenv("RESUMECRAFTR_ASSUME_YES") == "1":
        return True
    llm_config = workspace_config.get("llm") or {}
    model = llm_config.get("model", "unknown model")
    provider = llm_config.get("provider", "unknown provider")
    pricing = get_model_pricing(llm_config)
    prompt_tokens = _approx_tokens(prompt_characters)
    completion_tokens = max(1, int(prompt_tokens * completion_ratio))

    if pricing:
        cost_prompt = pricing.prompt * prompt_tokens
        cost_completion = pricing.completion * completion_tokens
        total_cost = cost_prompt + cost_completion
        console.print(
            f"[yellow]{action}[/yellow] will send approximately "
            f"{prompt_tokens:,} prompt tokens and {completion_tokens:,} completion tokens "
            f"to [bold]{model}[/bold] ({provider}). Estimated cost ≈ [bold]${total_cost:.4f}[/bold]."
        )
    else:
        console.print(
            f"[yellow]{action}[/yellow]: unable to fetch pricing for {provider}/{model}. "
            f"Estimated token usage ≈ {prompt_tokens:,} prompt / {completion_tokens:,} completion tokens."
        )

    return Confirm.ask("Proceed?", default=True)
