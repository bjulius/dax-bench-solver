# OpenRouter Models Skill

Discover, filter, and select LLM models from OpenRouter for benchmarking and DAX generation tasks.

## Implementation

**Python module**: `dax-bench/fetch_models.py` (already implemented)

## Purpose

Provide easy access to OpenRouter's model catalog with intelligent filtering for:
- Finding free models for cost-effective testing
- Identifying best-value models for production
- Comparing pricing across providers
- Selecting models by capability tier

## When to Invoke This Skill

Use this skill when:
- User asks "what models are available?"
- User asks to "compare models" or "find cheap models"
- Preparing benchmark runs that need model selection
- User mentions "OpenRouter" or "LLM models"

## Prerequisites

- **OpenRouter API Key**: Set as environment variable `OPENROUTER_API_KEY`
- **Internet access**: For API calls

## Model Tiers

| Tier | Description | Cost Range | Examples |
|------|-------------|------------|----------|
| **free** | $0 cost, rate-limited | $0 | llama-3.3-70b:free, gemini-flash:free |
| **budget** | Very cheap, good for iteration | <$0.50/1M | Ministral 3B, Haiku |
| **value** | Good quality/cost balance | $0.50-$3/1M | Sonnet, GPT-4o-mini |
| **premium** | High quality, higher cost | $3-$15/1M | Opus, GPT-4o |
| **frontier** | Best available, premium pricing | >$15/1M | Opus 4.5, o1 |
| **reasoning** | Extended thinking models | Varies | DeepSeek R1, o1, o3 |

## Commands

### List Available Models
```bash
python openrouter_models.py list [--tier <tier>] [--provider <provider>]
```

### Search Models
```bash
python openrouter_models.py search <query>
```

### Get Model Details
```bash
python openrouter_models.py info <model_id>
```

### Refresh Cache
```bash
python openrouter_models.py refresh
```

### Compare Models
```bash
python openrouter_models.py compare <model1> <model2>
```

## API Integration

### Fetch Models Endpoint
```
GET https://openrouter.ai/api/v1/models
Headers:
  Authorization: Bearer {OPENROUTER_API_KEY}
```

### Response Structure
```json
{
  "data": [
    {
      "id": "anthropic/claude-opus-4-5-20251101",
      "name": "Claude Opus 4.5",
      "pricing": {
        "prompt": "0.000015",    // per token
        "completion": "0.000075"  // per token
      },
      "context_length": 200000,
      "top_provider": {
        "max_completion_tokens": 32000
      }
    }
  ]
}
```

## Caching

Models are cached locally to avoid repeated API calls:
- Cache location: `dax-bench/cache/openrouter_models.json`
- Cache TTL: 24 hours
- Force refresh: `--refresh` flag

## Output Formats

### Table (Default)
```
| Model ID | Name | Input $/1M | Output $/1M | Context |
|----------|------|------------|-------------|---------|
| anthropic/claude-opus-4-5 | Opus 4.5 | $15.00 | $75.00 | 200K |
| anthropic/claude-sonnet-4 | Sonnet 4 | $3.00 | $15.00 | 200K |
```

### JSON
```bash
python openrouter_models.py list --json
```

### Recommendations
```bash
python openrouter_models.py recommend --use-case dax-generation --budget 0.01
```

## Integration with Other Skills

### Called by: dax-bench-solver
```python
from openrouter_models import get_model_info, find_models

# Get specific model
model = get_model_info("anthropic/claude-opus-4-5")

# Find models by criteria
cheap_models = find_models(max_input_cost=0.5)
free_models = find_models(tier="free")
```

### Example: Model Comparison Table
```python
from openrouter_models import compare_models

comparison = compare_models([
    "anthropic/claude-opus-4-5",
    "anthropic/claude-sonnet-4",
    "anthropic/claude-haiku-4-5",
    "mistralai/mistral-small-3.1"
])
print(comparison.to_markdown())
```

## Recommended Models for DAX Bench

### Best Accuracy
- `anthropic/claude-opus-4-5-20251101` - Highest quality, $15/$75 per 1M tokens

### Best Value
- `anthropic/claude-3.5-haiku` - Great quality, very cheap
- `google/gemini-2.5-flash` - Fast, cheap, 1M context

### Free Options
- `meta-llama/llama-3.3-70b-instruct:free` - Best free model
- `google/gemini-2.0-flash-exp:free` - Good free alternative

### Cheapest
- `mistralai/ministral-3b` - $0.04/$0.04 per 1M tokens
