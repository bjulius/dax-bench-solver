"""
Results Analyzer for DAX Bench
Generates reports from benchmark run data.

Usage:
    # From Python
    from results_analyzer import ResultsAnalyzer
    analyzer = ResultsAnalyzer()
    analyzer.load_all_results()
    print(analyzer.generate_comparison_report())

    # From CLI
    python results_analyzer.py [--format markdown|json]
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from datetime import datetime


@dataclass
class TaskResult:
    """Individual task result from a benchmark run."""
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
    error: Optional[str] = None
    final_dax: Optional[str] = None


@dataclass
class ModelSummary:
    """Summary statistics for a single model."""
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
        """Percentage of tasks solved."""
        return self.tasks_solved / self.tasks_total if self.tasks_total > 0 else 0

    @property
    def first_try_rate(self) -> float:
        """Percentage of tasks solved on first try."""
        return self.first_try / self.tasks_total if self.tasks_total > 0 else 0

    @property
    def avg_iterations(self) -> float:
        """Average iterations per task."""
        return self.total_iterations / self.tasks_total if self.tasks_total > 0 else 0

    @property
    def cost_per_task(self) -> float:
        """Average cost per task."""
        return self.total_cost / self.tasks_total if self.tasks_total > 0 else 0

    @property
    def time_per_task(self) -> float:
        """Average time per task in seconds."""
        return self.total_time / self.tasks_total if self.tasks_total > 0 else 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary including computed properties."""
        return {
            "model": self.model,
            "tasks_total": self.tasks_total,
            "tasks_solved": self.tasks_solved,
            "success_rate": self.success_rate,
            "first_try": self.first_try,
            "first_try_rate": self.first_try_rate,
            "avg_iterations": self.avg_iterations,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost": self.total_cost,
            "cost_per_task": self.cost_per_task,
            "total_time": self.total_time,
            "time_per_task": self.time_per_task,
        }


class ResultsAnalyzer:
    """
    Analyze DAX Bench results and generate reports.

    Supports loading results from:
    - Individual task JSON files
    - Summary RESULTS JSON files
    - API response files (for pre-validation data)
    """

    def __init__(self, runs_dir: Optional[Path] = None):
        """
        Initialize analyzer with runs directory.

        Args:
            runs_dir: Path to runs directory (defaults to dax-bench/runs)
        """
        self.runs_dir = runs_dir or Path(__file__).parent / "runs"
        self.results: List[TaskResult] = []
        self.model_summaries: Dict[str, ModelSummary] = {}

    def load_results_file(self, filepath: Path) -> List[Dict]:
        """Load a single results JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Handle both array and single object
            if isinstance(data, list):
                return data
            return [data]

    def load_all_results(self, pattern: str = "*_RESULTS_*.json") -> int:
        """
        Load all result files matching pattern.

        Args:
            pattern: Glob pattern for result files

        Returns:
            Number of results loaded
        """
        self.results = []

        for filepath in sorted(self.runs_dir.glob(pattern)):
            try:
                data = self.load_results_file(filepath)
                for item in data:
                    result = TaskResult(
                        task_id=item.get("task_id", ""),
                        title=item.get("title", ""),
                        complexity=item.get("complexity", ""),
                        category=item.get("category", ""),
                        model=item.get("model", ""),
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
            except Exception as e:
                print(f"Warning: Could not load {filepath}: {e}", file=sys.stderr)

        return len(self.results)

    def load_validated_results(self, filepath: Path) -> int:
        """
        Load validated results from a specific file.

        Args:
            filepath: Path to validated results JSON

        Returns:
            Number of results loaded
        """
        self.results = []
        data = self.load_results_file(filepath)

        for item in data:
            result = TaskResult(
                task_id=item.get("task_id", ""),
                title=item.get("title", ""),
                complexity=item.get("complexity", ""),
                category=item.get("category", ""),
                model=item.get("model", ""),
                solved=item.get("valid", item.get("solved", False)),
                first_try=item.get("first_try", item.get("valid", False)),
                iterations=item.get("iteration_count", 1),
                input_tokens=item.get("input_tokens", 0),
                output_tokens=item.get("output_tokens", 0),
                cost=item.get("cost", 0),
                time=item.get("time", 0),
                error=item.get("error"),
                final_dax=item.get("dax")
            )
            self.results.append(result)

        return len(self.results)

    def compute_model_summaries(self) -> Dict[str, ModelSummary]:
        """
        Compute summary statistics per model.

        Returns:
            Dict mapping model name to ModelSummary
        """
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

    def get_model_names_short(self) -> Dict[str, str]:
        """Get shortened model names for display."""
        short_names = {}
        for model in self.model_summaries.keys():
            # Extract last part after /
            short = model.split("/")[-1]
            # Truncate if too long
            if len(short) > 20:
                short = short[:17] + "..."
            short_names[model] = short
        return short_names

    def generate_comparison_report(self) -> str:
        """
        Generate model comparison markdown report.

        Returns:
            Markdown formatted comparison table
        """
        if not self.model_summaries:
            self.compute_model_summaries()

        models = sorted(self.model_summaries.keys())
        short_names = self.get_model_names_short()

        lines = [
            "# DAX Bench Model Comparison",
            "",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
            "",
            "## Summary",
            ""
        ]

        # Build header
        header_parts = ["Metric"] + [short_names[m] for m in models]
        header = "| " + " | ".join(header_parts) + " |"
        sep = "|" + "|".join(["-" * (len(p) + 2) for p in header_parts]) + "|"
        lines.extend([header, sep])

        # Metrics to display
        metrics = [
            ("Success Rate", lambda s: f"{s.success_rate*100:.1f}%"),
            ("First-Try", lambda s: f"{s.first_try_rate*100:.1f}%"),
            ("Avg Iterations", lambda s: f"{s.avg_iterations:.2f}"),
            ("Tasks Solved", lambda s: f"{s.tasks_solved}/{s.tasks_total}"),
            ("Input Tokens", lambda s: f"{s.total_input_tokens:,}"),
            ("Output Tokens", lambda s: f"{s.total_output_tokens:,}"),
            ("Cost/Task", lambda s: f"${s.cost_per_task:.6f}"),
            ("Total Cost", lambda s: f"${s.total_cost:.4f}"),
            ("Time/Task", lambda s: f"{s.time_per_task:.2f}s"),
            ("Total Time", lambda s: f"{s.total_time:.1f}s"),
        ]

        for name, fn in metrics:
            row_parts = [f"**{name}**"] + [fn(self.model_summaries[m]) for m in models]
            lines.append("| " + " | ".join(row_parts) + " |")

        return "\n".join(lines)

    def find_common_failures(self) -> List[str]:
        """
        Find tasks that failed for all models.

        Returns:
            List of task IDs that all models failed
        """
        task_results = defaultdict(dict)
        for r in self.results:
            task_results[r.task_id][r.model] = r.solved

        common_failures = []
        for task_id, by_model in task_results.items():
            if len(by_model) > 0 and all(not solved for solved in by_model.values()):
                common_failures.append(task_id)

        return sorted(common_failures)

    def find_model_specific_failures(self) -> Dict[str, List[str]]:
        """
        Find tasks that failed for only some models.

        Returns:
            Dict mapping model to list of tasks it uniquely failed
        """
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

    def get_error_for_task(self, task_id: str) -> Optional[str]:
        """Get error message for a failed task."""
        for r in self.results:
            if r.task_id == task_id and not r.solved and r.error:
                return r.error
        return None

    def get_task_title(self, task_id: str) -> str:
        """Get title for a task."""
        for r in self.results:
            if r.task_id == task_id:
                return r.title
        return ""

    def generate_failure_report(self) -> str:
        """
        Generate failure analysis report.

        Returns:
            Markdown formatted failure analysis
        """
        lines = [
            "# Task Failure Analysis",
            "",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
            ""
        ]

        # Common failures
        common = self.find_common_failures()
        if common:
            lines.extend([
                "## Common Failures (All Models)",
                "These tasks failed for every model tested:",
                ""
            ])
            for task_id in common:
                title = self.get_task_title(task_id)
                error = self.get_error_for_task(task_id)
                lines.append(f"- **{task_id}**: {title}")
                if error:
                    # Truncate long errors
                    error_short = error[:100] + "..." if len(error) > 100 else error
                    lines.append(f"  - Error: `{error_short}`")
            lines.append("")

        # Model-specific failures
        specific = self.find_model_specific_failures()
        if specific:
            lines.extend([
                "## Model-Specific Failures",
                "Tasks that some models solved but others failed:",
                ""
            ])
            short_names = self.get_model_names_short()
            for model in sorted(specific.keys()):
                tasks = specific[model]
                lines.append(f"### {short_names[model]}")
                for task_id in sorted(tasks):
                    title = self.get_task_title(task_id)
                    lines.append(f"- {task_id}: {title}")
                lines.append("")

        if not common and not specific:
            lines.append("*All models passed all tasks!*")

        return "\n".join(lines)

    def generate_by_complexity_report(self) -> str:
        """Generate breakdown by complexity level."""
        if not self.model_summaries:
            self.compute_model_summaries()

        lines = [
            "# Results by Complexity",
            "",
        ]

        for level in ["basic", "intermediate", "advanced"]:
            level_results = [r for r in self.results if r.complexity == level]
            if not level_results:
                continue

            lines.append(f"## {level.capitalize()}")
            lines.append("")

            # Group by model
            by_model = defaultdict(list)
            for r in level_results:
                by_model[r.model].append(r)

            lines.append("| Model | Solved | First-Try |")
            lines.append("|-------|--------|-----------|")

            short_names = self.get_model_names_short()
            for model in sorted(by_model.keys()):
                results = by_model[model]
                solved = sum(1 for r in results if r.solved)
                first = sum(1 for r in results if r.first_try)
                lines.append(f"| {short_names[model]} | {solved}/{len(results)} | {first}/{len(results)} |")

            lines.append("")

        return "\n".join(lines)

    def generate_full_report(self) -> str:
        """Generate comprehensive report combining all sections."""
        sections = [
            self.generate_comparison_report(),
            "",
            "---",
            "",
            self.generate_by_complexity_report(),
            "",
            "---",
            "",
            self.generate_failure_report(),
        ]
        return "\n".join(sections)

    def to_json(self) -> str:
        """Export summaries as JSON."""
        if not self.model_summaries:
            self.compute_model_summaries()

        data = {
            "generated": datetime.now().isoformat(),
            "models": {m: s.to_dict() for m, s in self.model_summaries.items()},
            "common_failures": self.find_common_failures(),
            "model_specific_failures": self.find_model_specific_failures(),
        }
        return json.dumps(data, indent=2)

    def save_report(self, content: str, filename: str) -> Path:
        """
        Save report to file.

        Args:
            content: Report content
            filename: Output filename

        Returns:
            Path to saved file
        """
        filepath = self.runs_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath


# CLI
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze DAX Bench results")
    parser.add_argument("--format", "-f", choices=["markdown", "json"],
                       default="markdown", help="Output format")
    parser.add_argument("--input", "-i", type=str,
                       help="Specific input file to analyze")
    parser.add_argument("--output", "-o", type=str,
                       help="Output file (default: stdout)")

    args = parser.parse_args()

    analyzer = ResultsAnalyzer()

    if args.input:
        analyzer.load_validated_results(Path(args.input))
    else:
        count = analyzer.load_all_results()
        if count == 0:
            print("No results found in runs directory.", file=sys.stderr)
            sys.exit(1)
        print(f"Loaded {count} results", file=sys.stderr)

    analyzer.compute_model_summaries()

    if args.format == "json":
        output = analyzer.to_json()
    else:
        output = analyzer.generate_full_report()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Report saved to {args.output}", file=sys.stderr)
    else:
        print(output)
