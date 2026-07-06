import typer

from app.agents.graph import build_graph

cli = typer.Typer(help="NHI Secret Agent CLI")


@cli.command()
def run(
    target_path: str = typer.Option(
        "data/sample_project",
        "--target-path",
        "-t",
        help="분석 대상 폴더 경로",
    ),
):
    """
    LangGraph 기반 NHI Secret Agent를 실행한다.
    """

    graph = build_graph()

    initial_state = {
        "target_path": target_path,
        "raw_findings": [],
        "context_results": [],
        "risk_results": [],
        "policy_evidence": [],
        "explanations": [],
        "review_results": [],
        "report_path": "",
        "errors": [],
    }

    final_state = graph.invoke(initial_state)

    typer.echo("\n=== NHI Secret Agent 실행 완료 ===")
    typer.echo(f"Target Path: {final_state['target_path']}")
    typer.echo(f"Raw Findings: {len(final_state['raw_findings'])}")
    typer.echo(f"Context Results: {len(final_state['context_results'])}")
    typer.echo(f"Risk Results: {len(final_state['risk_results'])}")
    typer.echo(f"Policy Evidence: {len(final_state['policy_evidence'])}")
    typer.echo(f"Explanations: {len(final_state['explanations'])}")
    typer.echo(f"Review Results: {len(final_state['review_results'])}")
    typer.echo(f"Report Path: {final_state['report_path']}")
    typer.echo(f"Errors: {len(final_state['errors'])}")

    if final_state["errors"]:
        typer.echo("\n에러 목록:")
        for error in final_state["errors"]:
            typer.echo(f"- {error}")


if __name__ == "__main__":
    cli()
