# Results Analyzer Skill

Analyze DAX Bench benchmark results and generate comprehensive reports.

## Purpose

Process benchmark run data to:
- Calculate success rates and performance metrics
- Compare models across different dimensions
- Identify patterns in failures
- Generate markdown and HTML reports
- Track improvement over time

## When to Invoke This Skill

Use this skill when:
- A benchmark run completes and needs analysis
- User asks to "compare models" or "show results"
- Generating summary reports for stakeholders
- Identifying which tasks models struggle with

## Input Sources

### 1. Individual Run Files
```
dax-bench/runs/YYYY-MM-DD_HHMM_task-XXX_model_v4.json
```

### 2. Summary Results
```
dax-bench/runs/YYYY-MM-DD_HHMM_RESULTS_model_v4.json
```

### 3. API Response Files (pre-validation)
```
dax-bench/runs/YYYY-MM-DD_HHMM_api_responses_v4.json
```

## Report Types

### 1. Model Comparison Report

Compare multiple models side-by-side:

```markdown
# DAX Bench Model Comparison

| Metric | Opus 4.5 | Sonnet 4.5 | Haiku 4.5 | Mistral |
|--------|----------|------------|-----------|---------|
| Success Rate | 80.0% | 83.3% | 83.3% | 83.3% |
| First-Try | 76.7% | 80.0% | 80.0% | 80.0% |
| Avg Iterations | 1.2 | 1.1 | 1.1 | 1.1 |
| Cost/Task | $0.0012 | $0.0003 | $0.0001 | $0.0001 |
```

### 2. Task Analysis Report

Analyze which tasks are problematic:

```markdown
# Task Difficulty Analysis

## Always Failed (All Models)
- task-007: YTD Calculation - Time intelligence needs date table marking
- task-016: Budget Variance - Budget table missing

## Model-Specific Failures
- task-014: Year-over-Year - Opus failed (missing 'Date' quotes)
```

### 3. Error Pattern Report

Categorize errors by type:

```markdown
# Error Pattern Analysis

| Error Type | Count | Affected Tasks |
|------------|-------|----------------|
| Quoting Error | 3 | task-014, task-022, task-028 |
| Schema Reference | 5 | task-007, task-009, task-016... |
| Context Error | 2 | task-018, task-025 |
```

## Python Implementation

Save to `dax-bench/results_analyzer.py`:

```python
"""
Results Analyzer for DAX Bench
Generates reports from benchmark run data.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class TaskResult:
    task_id: str
    title: str
    complexity: str
    category: str
    model: str
    solved: bool
    first_try: bool
    iterations: int
    input_tokens: int
    output_tokens: int
    cost: float
    time: float
    error: Optional[str]
    final_dax: Optional[str]


@dataclass
class ModelSummary:
    model: str
    tasks_total: int
    tasks_solved: int
    first_try: int
    total_iterations: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float
    total_time: float

    @property
    def success_rate(self) -> float:
        return self.tasks_solved / self.tasks_total if self.tasks_total > 0 else 0

    @property
    def first_try_rate(self) -> float:
        return self.first_try / self.tasks_total if self.tasks_total > 0 else 0

    @property
    def avg_iterations(self) -> float:
        return self.total_iterations / self.tasks_total if self.tasks_total > 0 else 0

    @property
    def cost_per_task(self) -> float:
        return self.total_cost / self.tasks_total if self.tasks_total > 0 else 0


class ResultsAnalyzer:
    """Analyze benchmark results and generate reports."""

    def __init__(self, runs_dir: Path = None):
        self.runs_dir = runs_dir or Path(__file__).parent / "runs"
        self.results: List[TaskResult] = []
        self.model_summaries: Dict[str, ModelSummary] = {}

    def load_results_file(self, filepath: Path) -> List[Dict]:
        """Load a single results JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_all_results(self, pattern: str = "*_RESULTS_*.json") -> None:
        """Load all result files matching pattern."""
        for filepath in self.runs_dir.glob(pattern):
            data = self.load_results_file(filepath)
            for item in data:
                result = TaskResult(
                    task_id=item["task_id"],
                    title=item.get("title", ""),
                    complexity=item.get("complexity", ""),
                    category=item.get("category", ""),
                    model=item["model"],
                    solved=item.get("solved", False),
                    first_try=item.get("first_try", False),
                    iterations=item.get("iteration_count", 0),
                    input_tokens=item.get("total_input_tokens", 0),
                    output_tokens=item.get("total_output_tokens", 0),
                    cost=item.get("total_cost", 0),
                    time=item.get("total_time", 0),
                    error=item.get("error"),
                    final_dax=item.get("final_dax")
                )
                self.results.append(result)

    def compute_model_summaries(self) -> Dict[str, ModelSummary]:
        """Compute summary statistics per model."""
        by_model = defaultdict(list)
        for r in self.results:
            by_model[r.model].append(r)

        self.model_summaries = {}
        for model, results in by_model.items():
            self.model_summaries[model] = ModelSummary(
                model=model,
                tasks_total=len(results),
                tasks_solved=sum(1 for r in results if r.solved),
                first_try=sum(1 for r in results if r.first_try),
                total_iterations=sum(r.iterations for r in results),
                total_input_tokens=sum(r.input_tokens for r in results),
                total_output_tokens=sum(r.output_tokens for r in results),
                total_cost=sum(r.cost for r in results),
                total_time=sum(r.time for r in results)
            )

        return self.model_summaries

    def generate_comparison_report(self) -> str:
        """Generate model comparison markdown report."""
        if not self.model_summaries:
            self.compute_model_summaries()

        models = sorted(self.model_summaries.keys())
        lines = ["# DAX Bench Model Comparison", ""]

        # Summary table
        lines.append("## Summary")
        header = "| Metric |" + " | ".join(m.split("/")[-1] for m in models) + " |"
        sep = "|--------|" + "|".join(["---------"] * len(models)) + "|"
        lines.extend([header, sep])

        metrics = [
            ("Success Rate", lambda s: f"{s.success_rate*100:.1f}%"),
            ("First-Try", lambda s: f"{s.first_try_rate*100:.1f}%"),
            ("Avg Iterations", lambda s: f"{s.avg_iterations:.2f}"),
            ("Cost/Task", lambda s: f"${s.cost_per_task:.6f}"),
            ("Time/Task", lambda s: f"{s.total_time/s.tasks_total:.2f}s"),
            ("Total Cost", lambda s: f"${s.total_cost:.4f}"),
        ]

        for name, fn in metrics:
            row = f"| **{name}** |"
            for m in models:
                row += f" {fn(self.model_summaries[m])} |"
            lines.append(row)

        return "\n".join(lines)

    def find_common_failures(self) -> List[str]:
        """Find tasks that failed for all models."""
        task_results = defaultdict(dict)
        for r in self.results:
            task_results[r.task_id][r.model] = r.solved

        common_failures = []
        for task_id, by_model in task_results.items():
            if all(not solved for solved in by_model.values()):
                common_failures.append(task_id)

        return sorted(common_failures)

    def find_model_specific_failures(self) -> Dict[str, List[str]]:
        """Find tasks that failed for only some models."""
        task_results = defaultdict(dict)
        for r in self.results:
            task_results[r.task_id][r.model] = r.solved

        model_failures = defaultdict(list)
        for task_id, by_model in task_results.items():
            failed_models = [m for m, solved in by_model.items() if not solved]
            passed_models = [m for m, solved in by_model.items() if solved]

            # Only include if some passed and some failed
            if failed_models and passed_models:
                for m in failed_models:
                    model_failures[m].append(task_id)

        return dict(model_failures)

    def generate_failure_report(self) -> str:
        """Generate failure analysis report."""
        lines = ["# Task Failure Analysis", ""]

        # Common failures
        common = self.find_common_failures()
        if common:
            lines.append("## Common Failures (All Models)")
            lines.append("These tasks failed for every model tested:")
            lines.append("")
            for task_id in common:
                # Find a result to get details
                for r in self.results:
                    if r.task_id == task_id:
                        lines.append(f"- **{task_id}**: {r.title}")
                        if r.error:
                            lines.append(f"  - Error: {r.error[:100]}...")
                        break
            lines.append("")

        # Model-specific failures
        specific = self.find_model_specific_failures()
        if specific:
            lines.append("## Model-Specific Failures")
            lines.append("Tasks that some models solved but others failed:")
            lines.append("")
            for model, tasks in sorted(specific.items()):
                model_short = model.split("/")[-1]
                lines.append(f"### {model_short}")
                for task_id in tasks:
                    lines.append(f"- {task_id}")
                lines.append("")

        return "\n".join(lines)

    def save_report(self, content: str, filename: str) -> Path:
        """Save report to file."""
        filepath = self.runs_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath


# CLI
if __name__ == "__main__":
    import sys

    analyzer = ResultsAnalyzer()
    analyzer.load_all_results()

    if not analyzer.results:
        print("No results found in runs directory.")
        sys.exit(1)

    analyzer.compute_model_summaries()

    print(analyzer.generate_comparison_report())
    print()
    print(analyzer.generate_failure_report())
```

## Integration with Other Skills

### Triggered after: dax-bench-solver

```python
# After benchmark completes
from results_analyzer import ResultsAnalyzer

analyzer = ResultsAnalyzer()
analyzer.load_all_results()
analyzer.compute_model_summaries()

# Generate reports
comparison = analyzer.generate_comparison_report()
failures = analyzer.generate_failure_report()

print(comparison)
print(failures)
```

## Output Examples

### Model Comparison

```
# DAX Bench Model Comparison

## Summary
| Metric | opus-4.5 | sonnet-4.5 | haiku-4.5 | mistral-small |
|--------|----------|------------|-----------|---------------|
| **Success Rate** | 80.0% | 83.3% | 83.3% | 83.3% |
| **First-Try** | 76.7% | 80.0% | 80.0% | 80.0% |
| **Avg Iterations** | 1.23 | 1.17 | 1.17 | 1.17 |
| **Cost/Task** | $0.001234 | $0.000312 | $0.000089 | $0.000045 |
| **Time/Task** | 2.34s | 1.56s | 0.89s | 0.76s |
| **Total Cost** | $0.0370 | $0.0094 | $0.0027 | $0.0014 |
```

### Failure Analysis

```
# Task Failure Analysis

## Common Failures (All Models)
These tasks failed for every model tested:

- **task-007**: Calculate YTD Revenue
  - Error: 'Date' is not a date table...
- **task-016**: Budget vs Actual Variance
  - Error: Column 'Budget' not found...

## Model-Specific Failures
Tasks that some models solved but others failed:

### opus-4.5
- task-014 (Year-over-Year calculation - quoting issue)
```
