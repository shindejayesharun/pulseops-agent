import argparse
import sys
import uuid
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from app.agent.orchestrator import PulseOpsOrchestrator
from app.db.database import init_db
from app.db.repository import repo

console = Console()


def print_banner():
    console.print(
        Panel.fit(
            "[bold cyan]⚡ PulseOps Agent[/bold cyan] — [green]Engineering Operations Assistant[/green]\n"
            "[dim]Synthetic Domain: Northstar Checkout · LangGraph ReAct · HITL Draft-Only[/dim]",
            border_style="cyan"
        )
    )


def run_canned_demo(orchestrator: PulseOpsOrchestrator):
    console.print("\n[bold yellow]=== EXECUTING CANNED END-TO-END DEMO ===[/bold yellow]\n")

    scenarios = [
        (
            "1. Grounded Knowledge Query (SLO)",
            "What is the availability SLO for checkout-api?"
        ),
        (
            "2. Runbook Triage Query (RAG with Citations)",
            "How do we triage latency spikes in checkout-api according to the runbook?"
        ),
        (
            "3. Multi-Tool Chain (Lookup Owner -> Create Ticket Draft)",
            "Find who owns checkout-api and create a P3 ticket draft for missing runbook section."
        ),
        (
            "4. PR Inspection & Structured Risk Summary",
            "Summarize PR #101 and analyze the deployment risk."
        ),
        (
            "5. Safety Refusal & Policy Enforcement",
            "Post this active outage to our public company Twitter/X account with root cause."
        ),
    ]

    conv_id = f"demo_conv_{uuid.uuid4().hex[:8]}"

    for title, prompt in scenarios:
        console.rule(f"[bold magenta]{title}[/bold magenta]")
        console.print(f"[bold green]User Prompt:[/bold green] {prompt}\n")

        with console.status("[bold cyan]Reasoning & executing tools via LangGraph...[/bold cyan]"):
            res = orchestrator.run_turn(conv_id, prompt)

        # Print Tool Traces Table
        if res["tool_traces"]:
            table = Table(title="Tool Execution Telemetry", show_header=True, header_style="bold blue")
            table.add_column("Step", style="dim", width=6)
            table.add_column("Tool Name", style="cyan")
            table.add_column("Latency (ms)", style="green")
            table.add_column("Status", style="bold")

            for idx, trace in enumerate(res["tool_traces"], 1):
                status_text = "[green]OK[/green]" if trace.get("ok") else "[red]ERROR[/red]"
                table.add_row(str(idx), trace["tool_name"], str(trace.get("latency_ms", "0.0")), status_text)
            console.print(table)

        # Print Response
        console.print("\n[bold cyan]PulseOps Response:[/bold cyan]")
        console.print(Markdown(res["response"]))
        console.print(f"\n[dim]Completed in {res['duration_ms']}ms · Refusal: {res['refusal_triggered']}[/dim]\n")

    # Display Persisted Draft Artifacts
    console.rule("[bold yellow]Persisted Ticket Drafts (SQLite)[/bold yellow]")
    drafts = repo.list_ticket_drafts(limit=5)
    d_table = Table(show_header=True, header_style="bold yellow")
    d_table.add_column("ID", style="bold")
    d_table.add_column("Priority", style="red")
    d_table.add_column("Team", style="cyan")
    d_table.add_column("Title")
    d_table.add_column("Status", style="dim")

    for d in drafts:
        d_table.add_row(d["id"], d["priority"], d["team"], d["title"], d["status"])
    console.print(d_table)


def run_interactive_repl(orchestrator: PulseOpsOrchestrator):
    conv_id = f"repl_conv_{uuid.uuid4().hex[:8]}"
    console.print("\n[dim]Type your query or 'exit' / 'quit' to end session.[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold green]Operator[/bold green]")
            if user_input.lower().strip() in ("exit", "quit", "q"):
                console.print("[dim]Session terminated.[/dim]")
                break
            if not user_input.strip():
                continue

            with console.status("[bold cyan]PulseOps is reasoning...[/bold cyan]"):
                res = orchestrator.run_turn(conv_id, user_input)

            if res["tool_traces"]:
                tools_called = [t["tool_name"] for t in res["tool_traces"]]
                console.print(f"[dim]⚡ Executed Tools: {', '.join(tools_called)}[/dim]")

            console.print("\n[bold cyan]PulseOps:[/bold cyan]")
            console.print(Markdown(res["response"]))
            console.print("")

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Session terminated.[/dim]")
            break


def main():
    parser = argparse.ArgumentParser(description="PulseOps CLI Assistant")
    parser.add_argument("--demo", action="store_true", help="Run canned end-to-end demo flow")
    parser.add_argument("--mode", choices=["mock", "live"], default="mock", help="Engine mode (mock or live)")
    parser.add_argument("--provider", choices=["openai", "grok"], default="openai", help="Live LLM provider")
    args = parser.parse_args()

    # Initialize DB
    init_db()

    print_banner()
    orchestrator = PulseOpsOrchestrator(mode=args.mode, provider_name=args.provider)

    if args.demo:
        run_canned_demo(orchestrator)
    else:
        run_interactive_repl(orchestrator)


if __name__ == "__main__":
    main()
