import argparse
import json
import sys
import time
import uuid
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from app.agent.orchestrator import PulseOpsOrchestrator
from app.db.database import init_db
from evals.graders import grade_case

console = Console()


def run_evaluation_suite(
    cases_file: Path,
    mode: str = "mock",
    provider: str = "openai",
    output_md: Path = None,
    output_json: Path = None,
):
    init_db()

    console.print(
        Panel.fit(
            f"[bold cyan]⚡ PulseOps Evaluation Harness[/bold cyan]\n"
            f"[dim]Engine Mode: {mode.upper()} · Provider: {provider} · Golden Set: {cases_file.name}[/dim]",
            border_style="cyan"
        )
    )

    if not cases_file.exists():
        console.print(f"[red]Error: Cases file not found at {cases_file}[/red]")
        sys.exit(1)

    cases = []
    with open(cases_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    orchestrator = PulseOpsOrchestrator(mode=mode, provider_name=provider)

    results_table = Table(title="Golden Evaluation Case Results", show_header=True, header_style="bold blue")
    results_table.add_column("Case ID", style="bold")
    results_table.add_column("Category", style="cyan")
    results_table.add_column("Tools Called", style="magenta")
    results_table.add_column("Latency (ms)", style="green")
    results_table.add_column("Result", style="bold")
    results_table.add_column("Notes", style="dim")

    passed_count = 0
    total_count = len(cases)
    latencies = []
    eval_records = []

    for c in cases:
        case_id = c["id"]
        category = c.get("type", "general")
        prompt = c["prompt"]

        # Run in fresh isolated conversation
        conv_id = f"eval_{case_id}_{uuid.uuid4().hex[:6]}"
        t0 = time.perf_counter()
        agent_res = orchestrator.run_turn(conv_id, prompt)
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        latencies.append(latency_ms)

        passed, failures = grade_case(c, agent_res)
        if passed:
            passed_count += 1
            status_render = "[green]PASS[/green]"
            notes = "All assertions satisfied"
        else:
            status_render = "[red]FAIL[/red]"
            notes = "; ".join(failures)

        tools_str = ", ".join(t["tool_name"] for t in agent_res["tool_traces"]) or "(none)"
        results_table.add_row(case_id, category, tools_str, str(latency_ms), status_render, notes)

        eval_records.append({
            "id": case_id,
            "category": category,
            "prompt": prompt,
            "passed": passed,
            "latency_ms": latency_ms,
            "tools_called": [t["tool_name"] for t in agent_res["tool_traces"]],
            "failures": failures,
            "response": agent_res["response"]
        })

    console.print(results_table)

    pass_rate = round((passed_count / total_count) * 100, 1) if total_count else 0
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0
    p95_latency = round(sorted(latencies)[int(len(latencies) * 0.95)], 2) if latencies else 0

    console.print("\n[bold]=== Benchmark Summary ===[/bold]")
    console.print(f"Total Cases:     {total_count}")
    console.print(f"Passed:          [green]{passed_count}[/green]")
    console.print(f"Failed:          [red]{total_count - passed_count}[/red]")
    console.print(f"Pass Rate:       [bold {'green' if pass_rate == 100 else 'yellow'}]{pass_rate}%[/bold {'green' if pass_rate == 100 else 'yellow'}]")
    console.print(f"Avg Latency:     {avg_latency} ms")
    console.print(f"p95 Latency:     {p95_latency} ms\n")

    # Export Markdown results
    if output_md:
        md_content = f"""# PulseOps Golden Evaluation Results
**Execution Mode**: `{mode.upper()}` | **Provider**: `{provider}`  
**Pass Rate**: **{pass_rate}% ({passed_count}/{total_count} passed)**  
**Latency**: Avg `{avg_latency}ms` | p95 `{p95_latency}ms`

| Case ID | Category | Tools Called | Latency | Status | Details |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
        for r in eval_records:
            t_str = ", ".join(r["tools_called"]) or "none"
            st = "PASS" if r["passed"] else "FAIL"
            dt = "Satisfied" if r["passed"] else "<br>".join(r["failures"])
            md_content += f"| `{r['id']}` | `{r['category']}` | `{t_str}` | {r['latency_ms']}ms | **{st}** | {dt} |\n"

        output_md.write_text(md_content, encoding="utf-8")
        console.print(f"[dim]Saved Markdown report to: {output_md}[/dim]")

    # Export JSON results
    if output_json:
        output_json.write_text(json.dumps({
            "mode": mode,
            "provider": provider,
            "total": total_count,
            "passed": passed_count,
            "pass_rate": pass_rate,
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency,
            "records": eval_records
        }, indent=2), encoding="utf-8")
        console.print(f"[dim]Saved JSON report to: {output_json}[/dim]")

    if passed_count < total_count:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="PulseOps Evaluation Runner")
    parser.add_argument("--mode", choices=["mock", "live"], default="mock", help="Engine execution mode")
    parser.add_argument("--provider", choices=["openai", "grok"], default="openai", help="Live LLM provider")
    parser.add_argument("--cases", type=Path, default=Path(__file__).resolve().parent / "cases.jsonl", help="Golden cases JSONL path")
    parser.add_argument("--out-md", type=Path, default=Path(__file__).resolve().parent / "results.sample.md", help="Markdown scorecard path")
    parser.add_argument("--out-json", type=Path, default=Path(__file__).resolve().parent / "results.sample.json", help="JSON results path")
    args = parser.parse_args()

    run_evaluation_suite(
        cases_file=args.cases,
        mode=args.mode,
        provider=args.provider,
        output_md=args.out_md,
        output_json=args.out_json,
    )


if __name__ == "__main__":
    main()
