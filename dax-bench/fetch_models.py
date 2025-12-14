#!/usr/bin/env python3
"""
OpenRouter Model Fetcher & Cache
Fetches all available models from OpenRouter API and caches them with categorization.
Supports queries like: best free model, cheapest flash model, etc.
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Configuration
API_KEY = os.environ.get("OPENROUTER_DAXBENCH_API_KEY", os.environ.get("OPENROUTER_API_KEY", ""))
MODELS_API = "https://openrouter.ai/api/v1/models"
CACHE_FILE = Path(__file__).parent / "models_cache.json"
CACHE_MAX_AGE_HOURS = 24


def fetch_models_from_api() -> List[Dict[str, Any]]:
    """Fetch all models from OpenRouter API"""
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}

    response = requests.get(MODELS_API, headers=headers, timeout=30)
    if response.status_code != 200:
        raise Exception(f"API error {response.status_code}: {response.text}")

    data = response.json()
    return data.get("data", [])


def categorize_model(model: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and categorize model information"""
    model_id = model.get("id", "")
    name = model.get("name", "")
    pricing = model.get("pricing", {})

    # Parse pricing (costs are per token as strings)
    prompt_cost = float(pricing.get("prompt", "0") or "0")
    completion_cost = float(pricing.get("completion", "0") or "0")

    # Calculate cost per 1M tokens
    input_cost_per_1m = prompt_cost * 1_000_000
    output_cost_per_1m = completion_cost * 1_000_000

    # Determine if free
    is_free = ":free" in model_id or (prompt_cost == 0 and completion_cost == 0)

    # Determine tier based on pricing and model characteristics
    tier = determine_tier(model_id, name, input_cost_per_1m, output_cost_per_1m, is_free)

    # Extract provider
    provider = model_id.split("/")[0] if "/" in model_id else "unknown"

    # Determine capabilities
    arch = model.get("architecture", {})
    modalities = arch.get("input_modalities", [])
    has_vision = "image" in modalities
    has_tools = "tools" in model.get("supported_parameters", [])

    return {
        "id": model_id,
        "name": name,
        "provider": provider,
        "description": model.get("description", "")[:200],
        "context_length": model.get("context_length", 0),
        "max_output": model.get("top_provider", {}).get("max_completion_tokens", 0),
        "input_cost_per_1m": round(input_cost_per_1m, 4),
        "output_cost_per_1m": round(output_cost_per_1m, 4),
        "is_free": is_free,
        "tier": tier,
        "has_vision": has_vision,
        "has_tools": has_tools,
        "modality": arch.get("modality", "text->text"),
    }


def determine_tier(model_id: str, name: str, input_cost: float, output_cost: float, is_free: bool) -> str:
    """Determine model tier based on characteristics"""
    model_lower = model_id.lower() + name.lower()

    if is_free:
        return "free"

    # Flash/efficient models
    if any(x in model_lower for x in ["flash", "mini", "lite", "nano", "small", "haiku", "instant"]):
        return "flash"

    # Frontier models (expensive, top-tier)
    if any(x in model_lower for x in ["opus", "gpt-4o", "gpt-5", "pro", "ultra", "large"]):
        if input_cost >= 1.0:  # $1+ per 1M input tokens
            return "frontier"

    # Strong models (good performance, moderate cost)
    if any(x in model_lower for x in ["sonnet", "claude-3", "gpt-4", "gemini-2", "deepseek", "qwen"]):
        return "strong"

    # Reasoning models
    if any(x in model_lower for x in ["-r1", "thinking", "reason", "o1", "o3"]):
        return "reasoning"

    # Default based on cost
    if input_cost >= 5.0:
        return "frontier"
    elif input_cost >= 0.5:
        return "strong"
    elif input_cost > 0:
        return "efficient"

    return "unknown"


def fetch_and_cache_models(force_refresh: bool = False) -> Dict[str, Any]:
    """Fetch models and cache them, or load from cache if fresh"""

    # Check cache
    if not force_refresh and CACHE_FILE.exists():
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)

        cached_time = datetime.fromisoformat(cache.get("fetched_at", "2000-01-01"))
        age_hours = (datetime.now() - cached_time).total_seconds() / 3600

        if age_hours < CACHE_MAX_AGE_HOURS:
            print(f"Using cached models (age: {age_hours:.1f}h)")
            return cache

    print("Fetching models from OpenRouter API...")
    raw_models = fetch_models_from_api()

    # Process and categorize
    models = [categorize_model(m) for m in raw_models]

    # Build cache with indexes
    cache = {
        "fetched_at": datetime.now().isoformat(),
        "total_count": len(models),
        "models": models,
        "by_tier": {},
        "by_provider": {},
        "free_models": [],
        "stats": {}
    }

    # Build indexes
    for m in models:
        tier = m["tier"]
        provider = m["provider"]

        if tier not in cache["by_tier"]:
            cache["by_tier"][tier] = []
        cache["by_tier"][tier].append(m["id"])

        if provider not in cache["by_provider"]:
            cache["by_provider"][provider] = []
        cache["by_provider"][provider].append(m["id"])

        if m["is_free"]:
            cache["free_models"].append(m["id"])

    # Calculate stats
    cache["stats"] = {
        "total": len(models),
        "free": len(cache["free_models"]),
        "by_tier": {k: len(v) for k, v in cache["by_tier"].items()},
        "by_provider": {k: len(v) for k, v in cache["by_provider"].items()},
    }

    # Save cache
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

    print(f"Cached {len(models)} models to {CACHE_FILE}")
    return cache


def get_models(cache: Dict = None) -> List[Dict]:
    """Get all models from cache"""
    if cache is None:
        cache = fetch_and_cache_models()
    return cache.get("models", [])


def find_best_free(cache: Dict = None, prefer_large_context: bool = True) -> List[Dict]:
    """Find the best free models, ranked by capability indicators"""
    models = get_models(cache)
    free = [m for m in models if m["is_free"]]

    # Score by: context length, has_tools, has_vision, provider reputation
    def score(m):
        s = 0
        # Context length (normalized to 0-100 scale)
        s += min(m["context_length"] / 10000, 100) if prefer_large_context else 0
        # Tools support is valuable
        s += 20 if m["has_tools"] else 0
        # Vision support
        s += 10 if m["has_vision"] else 0
        # Provider reputation bonus
        if any(p in m["provider"] for p in ["google", "meta", "mistral", "qwen"]):
            s += 15
        # Penalty for very small models
        if any(x in m["id"].lower() for x in ["3b", "4b", "7b", "8b"]):
            s -= 20
        # Bonus for larger models
        if any(x in m["id"].lower() for x in ["70b", "72b", "235b", "405b"]):
            s += 30
        return s

    free.sort(key=score, reverse=True)
    return free[:10]


def find_cheapest_flash(cache: Dict = None) -> List[Dict]:
    """Find the cheapest flash/efficient tier models"""
    models = get_models(cache)
    flash = [m for m in models if m["tier"] == "flash" and not m["is_free"]]
    flash.sort(key=lambda m: m["input_cost_per_1m"] + m["output_cost_per_1m"])
    return flash[:10]


def find_best_value(cache: Dict = None, max_input_cost: float = 1.0) -> List[Dict]:
    """Find best value models under a cost threshold"""
    models = get_models(cache)
    affordable = [m for m in models if 0 < m["input_cost_per_1m"] <= max_input_cost]

    # Score by capability indicators vs cost
    def value_score(m):
        cost = m["input_cost_per_1m"] + m["output_cost_per_1m"]
        if cost == 0:
            return 0
        capability = (
            min(m["context_length"] / 1000, 200) +
            (30 if m["has_tools"] else 0) +
            (20 if m["has_vision"] else 0)
        )
        return capability / cost

    affordable.sort(key=value_score, reverse=True)
    return affordable[:10]


def find_by_provider(provider: str, cache: Dict = None) -> List[Dict]:
    """Find all models from a specific provider"""
    models = get_models(cache)
    return [m for m in models if provider.lower() in m["provider"].lower()]


def find_frontier(cache: Dict = None) -> List[Dict]:
    """Find frontier-tier models"""
    models = get_models(cache)
    frontier = [m for m in models if m["tier"] == "frontier"]
    frontier.sort(key=lambda m: m["input_cost_per_1m"], reverse=True)
    return frontier[:10]


def find_reasoning(cache: Dict = None) -> List[Dict]:
    """Find reasoning-specialized models"""
    models = get_models(cache)
    reasoning = [m for m in models if m["tier"] == "reasoning" or
                 any(x in m["id"].lower() for x in ["r1", "thinking", "reason", "o1", "o3"])]
    return reasoning[:10]


def search_models(query: str, cache: Dict = None) -> List[Dict]:
    """Search models by name or ID"""
    models = get_models(cache)
    query = query.lower()
    return [m for m in models if query in m["id"].lower() or query in m["name"].lower()]


def print_models(models: List[Dict], title: str = "Models"):
    """Pretty print a list of models"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

    if not models:
        print("No models found.")
        return

    print(f"{'Model ID':<45} {'Tier':<10} {'Input$/1M':<10} {'Context':<10}")
    print("-" * 75)

    for m in models:
        cost_str = "FREE" if m["is_free"] else f"${m['input_cost_per_1m']:.4f}"
        ctx_str = f"{m['context_length']//1000}K" if m['context_length'] else "?"
        print(f"{m['id']:<45} {m['tier']:<10} {cost_str:<10} {ctx_str:<10}")


def main():
    import argparse
    import sys

    # Fix Windows encoding for UTF-8 output
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description="OpenRouter Model Discovery Tool")
    parser.add_argument("command", nargs="?", default="stats",
                       choices=["stats", "refresh", "free", "flash", "frontier",
                               "value", "reasoning", "search", "provider", "all"],
                       help="Command to run")
    parser.add_argument("--query", "-q", help="Search query or provider name")
    parser.add_argument("--max-cost", type=float, default=1.0, help="Max cost for value search")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Refresh if requested
    cache = fetch_and_cache_models(force_refresh=(args.command == "refresh"))

    if args.command == "stats":
        print("\n[STATS] OpenRouter Model Statistics")
        print(f"   Total models: {cache['stats']['total']}")
        print(f"   Free models: {cache['stats']['free']}")
        print(f"\n   By Tier:")
        for tier, count in sorted(cache['stats']['by_tier'].items(), key=lambda x: -x[1]):
            print(f"      {tier}: {count}")
        print(f"\n   Top Providers:")
        for provider, count in sorted(cache['stats']['by_provider'].items(), key=lambda x: -x[1])[:10]:
            print(f"      {provider}: {count}")

    elif args.command == "free":
        models = find_best_free(cache)
        if args.json:
            print(json.dumps(models, indent=2))
        else:
            print_models(models, "[FREE] Best Free Models")

    elif args.command == "flash":
        models = find_cheapest_flash(cache)
        if args.json:
            print(json.dumps(models, indent=2))
        else:
            print_models(models, "[FLASH] Cheapest Flash Models")

    elif args.command == "frontier":
        models = find_frontier(cache)
        if args.json:
            print(json.dumps(models, indent=2))
        else:
            print_models(models, "[FRONTIER] Top Frontier Models")

    elif args.command == "value":
        models = find_best_value(cache, args.max_cost)
        if args.json:
            print(json.dumps(models, indent=2))
        else:
            print_models(models, f"[VALUE] Best Value (max ${args.max_cost}/1M input)")

    elif args.command == "reasoning":
        models = find_reasoning(cache)
        if args.json:
            print(json.dumps(models, indent=2))
        else:
            print_models(models, "[REASONING] Reasoning Models")

    elif args.command == "search":
        if not args.query:
            print("Error: --query required for search")
            return
        models = search_models(args.query, cache)
        if args.json:
            print(json.dumps(models, indent=2))
        else:
            print_models(models, f"[SEARCH] Results for '{args.query}'")

    elif args.command == "provider":
        if not args.query:
            print("Error: --query required for provider search")
            return
        models = find_by_provider(args.query, cache)
        if args.json:
            print(json.dumps(models, indent=2))
        else:
            print_models(models, f"[PROVIDER] Models from '{args.query}'")

    elif args.command == "all":
        models = get_models(cache)
        if args.json:
            print(json.dumps(models, indent=2))
        else:
            print_models(models[:50], "All Models (first 50)")


if __name__ == "__main__":
    main()
