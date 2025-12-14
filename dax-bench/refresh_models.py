#!/usr/bin/env python3
"""
Refresh models.json with current OpenRouter model IDs.

This script fetches the latest models from OpenRouter's API and updates
the local models.json file with correct model IDs while preserving
existing daxBench scores and tier classifications.

Usage:
    python refresh_models.py              # Refresh models.json
    python refresh_models.py --list       # List all available models
    python refresh_models.py --search gemini  # Search for models
"""

import os
import sys
import json
import requests
from pathlib import Path

# Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"
MODELS_JSON_PATH = Path(__file__).parent.parent / ".claude" / "skills" / "dax-bench-solver" / "models.json"

# Model name patterns to search for (maps friendly name -> exact model IDs to try)
# These are checked in order - first match wins
PREFERRED_MODELS = {
    "Claude Opus 4.5": ["anthropic/claude-opus-4.5", "anthropic/claude-opus-4"],
    "Claude Sonnet 4": ["anthropic/claude-sonnet-4", "anthropic/claude-sonnet-4.5"],
    "Claude Sonnet 3.5": ["anthropic/claude-3.5-sonnet"],
    "GPT-4o": ["openai/gpt-4o", "openai/gpt-4o-2024"],
    "GPT-4 Turbo": ["openai/gpt-4-turbo"],
    "Gemini 2.5 Flash": ["google/gemini-2.5-flash", "google/gemini-2.5-flash-preview"],
    "Gemini 2.5 Pro": ["google/gemini-2.5-pro", "google/gemini-2.5-pro-preview"],
    "Gemini 2.0 Flash": ["google/gemini-2.0-flash", "google/gemini-2.0-flash-exp"],
    "DeepSeek V3": ["deepseek/deepseek-chat", "deepseek/deepseek-v3"],
    "DeepSeek Coder": ["deepseek/deepseek-coder"],
    "Qwen Coder": ["qwen/qwen-2.5-coder-32b-instruct", "qwen/qwen3-coder"],
    "Llama 3.3 70B": ["meta-llama/llama-3.3-70b-instruct"],
    "Mistral Large": ["mistralai/mistral-large"],
    "Devstral": ["mistralai/devstral-small", "mistralai/devstral"],
    "Grok 2": ["x-ai/grok-2", "x-ai/grok-2-1212"],
}


def get_api_key():
    """Get OpenRouter API key from environment."""
    for var in ["OPENROUTER_DAXBENCH_API_KEY", "OPENROUTER_API_KEY"]:
        key = os.environ.get(var)
        if key:
            return key
    return None


def fetch_openrouter_models(api_key=None):
    """Fetch all available models from OpenRouter."""
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.get(OPENROUTER_API_URL, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.RequestException as e:
        print(f"Error fetching models: {e}")
        return []


def search_models(models, query):
    """Search models by name or ID."""
    query = query.lower()
    results = []
    for model in models:
        model_id = model.get("id", "").lower()
        model_name = model.get("name", "").lower()
        if query in model_id or query in model_name:
            results.append(model)
    return results


def find_best_match(models, patterns):
    """Find the best matching model for given search patterns.

    First tries exact ID matches, then falls back to substring matching.
    """
    # Build lookup dict for fast exact matching
    model_by_id = {m.get("id", ""): m for m in models}

    # Try exact matches first
    for pattern in patterns:
        if pattern in model_by_id:
            return model_by_id[pattern]

    # Fall back to substring matching
    for pattern in patterns:
        for model in models:
            model_id = model.get("id", "").lower()
            if pattern.lower() in model_id:
                return model
    return None


def format_model_entry(model, tier="unknown", dax_rank=None, dax_score=None, note=None):
    """Format a model entry for models.json."""
    pricing = model.get("pricing", {})

    # Parse pricing (OpenRouter returns as strings like "0.00015")
    try:
        input_cost = float(pricing.get("prompt", "0")) * 1_000_000
        output_cost = float(pricing.get("completion", "0")) * 1_000_000
    except (ValueError, TypeError):
        input_cost = 0
        output_cost = 0

    entry = {
        "id": model.get("id"),
        "name": model.get("name", model.get("id")),
        "tier": tier,
        "provider": model.get("id", "").split("/")[0].title(),
        "inputCostPer1M": round(input_cost, 4),
        "outputCostPer1M": round(output_cost, 4),
        "contextWindow": model.get("context_length", 0),
        "daxBenchRank": dax_rank,
        "daxBenchScore": dax_score,
    }

    if note:
        entry["note"] = note

    return entry


def update_models_json(models):
    """Update models.json with current model IDs."""
    # Load existing models.json to preserve daxBench scores
    existing_data = {}
    existing_models = {}

    if MODELS_JSON_PATH.exists():
        with open(MODELS_JSON_PATH, "r") as f:
            existing_data = json.load(f)
            for m in existing_data.get("models", []):
                # Key by name for matching
                existing_models[m.get("name", "")] = m

    # Build new model list
    new_models = []

    # Tier assignments (can be customized)
    tier_assignments = {
        "Claude Opus 4.5": "frontier",
        "Claude Sonnet 4": "strong",
        "Claude Sonnet 3.5": "strong",
        "GPT-4o": "frontier",
        "GPT-4 Turbo": "frontier",
        "Gemini 2.5 Pro": "frontier",
        "Gemini 2.5 Flash": "efficient",
        "Gemini 2.0 Flash": "efficient",
        "DeepSeek V3": "strong",
        "DeepSeek Coder": "efficient",
        "Qwen Coder": "efficient",
        "Llama 3.3 70B": "efficient",
        "Mistral Large": "strong",
        "Devstral": "small",
        "Grok 2": "efficient",
    }

    for friendly_name, patterns in PREFERRED_MODELS.items():
        match = find_best_match(models, patterns)
        if match:
            # Get existing daxBench data if available
            existing = existing_models.get(friendly_name, {})

            entry = format_model_entry(
                match,
                tier=tier_assignments.get(friendly_name, "unknown"),
                dax_rank=existing.get("daxBenchRank"),
                dax_score=existing.get("daxBenchScore"),
                note=existing.get("note"),
            )
            # Use friendly name
            entry["name"] = friendly_name
            new_models.append(entry)
            print(f"  [OK] {friendly_name}: {match.get('id')}")
        else:
            print(f"  [--] {friendly_name}: NOT FOUND")

    # Preserve settings and tiers from existing file
    new_data = {
        "models": new_models,
        "settings": existing_data.get("settings", {
            "maxIterations": 10,
            "timeoutPerAttemptMs": 60000,
            "openRouterBaseUrl": "https://openrouter.ai/api/v1",
            "apiKeyEnvVars": ["OPENROUTER_DAXBENCH_API_KEY", "OPENROUTER_API_KEY"],
        }),
        "tiers": existing_data.get("tiers", {
            "frontier": "Largest, most capable models - highest accuracy, highest cost",
            "strong": "Excellent performance, more cost-effective than frontier",
            "efficient": "Good performance at low cost, may need more iterations",
            "small": "Smallest/cheapest, tests the limits of iteration approach",
        }),
        "_lastUpdated": __import__("datetime").datetime.now().isoformat(),
    }

    # Write updated file
    MODELS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODELS_JSON_PATH, "w") as f:
        json.dump(new_data, f, indent=2)

    return new_models


def list_all_models(models):
    """Print all available models."""
    print(f"\n{'='*80}")
    print(f"Available OpenRouter Models ({len(models)} total)")
    print(f"{'='*80}\n")

    # Group by provider
    by_provider = {}
    for model in models:
        provider = model.get("id", "").split("/")[0]
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append(model)

    for provider in sorted(by_provider.keys()):
        print(f"\n{provider.upper()}")
        print("-" * 40)
        for model in sorted(by_provider[provider], key=lambda x: x.get("id", "")):
            model_id = model.get("id", "")
            name = model.get("name", "")
            ctx = model.get("context_length", 0)
            print(f"  {model_id}")
            if name and name != model_id:
                print(f"    Name: {name}")
            print(f"    Context: {ctx:,}")


def main():
    args = sys.argv[1:]

    print("Fetching models from OpenRouter...")
    api_key = get_api_key()
    models = fetch_openrouter_models(api_key)

    if not models:
        print("No models found. Check your API key or network connection.")
        return 1

    print(f"Found {len(models)} models.\n")

    if "--list" in args:
        list_all_models(models)
        return 0

    if "--search" in args:
        idx = args.index("--search")
        if idx + 1 < len(args):
            query = args[idx + 1]
            results = search_models(models, query)
            print(f"\nSearch results for '{query}':")
            print("-" * 40)
            for model in results:
                print(f"  {model.get('id')}")
                pricing = model.get("pricing", {})
                print(f"    Input: ${float(pricing.get('prompt', 0)) * 1e6:.4f}/1M")
                print(f"    Output: ${float(pricing.get('completion', 0)) * 1e6:.4f}/1M")
                print(f"    Context: {model.get('context_length', 0):,}")
        return 0

    # Default: update models.json
    print("Updating models.json with current model IDs...")
    print("-" * 40)
    updated = update_models_json(models)
    print("-" * 40)
    print(f"\n[OK] Updated {len(updated)} models in {MODELS_JSON_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
