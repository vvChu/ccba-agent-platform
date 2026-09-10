"""CLI Entrypoint for ccba-qc command-line tool."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from ccba_qc_core.discovery import DiscoveryEngine
from ccba_qc_core.pccc import PcccMapReduceEngine
from ccba_qc_core.pipeline import QCBatchOrchestrator
from ccba_qc_core.quadview import QuadViewAuditEngine

app = typer.Typer(
    name="ccba-qc",
    help="CCBA AI Quality Control CLI — Discovery, Quad-View Alignment, Semantic, and Batch Audits.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def discover(
    input_path: Path = typer.Option(..., "--input", "-i", help="PDF file or folder of drawings"),
    output_path: Path = typer.Option(
        Path("backbone.json"), "--output", "-o", help="Output JSON path"
    ),
    project_name: str = typer.Option("CCBA Project", "--project", "-p", help="Project name"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Scan subdirectories"),
    no_ai: bool = typer.Option(False, "--no-ai", help="Skip AI metadata extraction"),
    ai_model: str = typer.Option("gemini-3.7-flash", "--model", "-m", help="AI Model to use"),
    titleblocks_dir: Path = typer.Option(
        Path("titleblocks"), "--titleblocks-dir", help="Dir for extracted titleblocks"
    ),
) -> None:
    """Khai phá cấu trúc tài liệu PDF và trích xuất danh mục bản vẽ (Backbone)."""
    if input_path.is_file():
        pdfs = [input_path]
    else:
        pattern = "**/*.pdf" if recursive else "*.pdf"
        pdfs = sorted(input_path.glob(pattern))

    if not pdfs:
        console.print(f"[red]Không tìm thấy tệp PDF nào tại: {input_path}[/red]")
        raise typer.Exit(code=1)

    console.print(
        f"[cyan]Khởi động Discovery trên {len(pdfs)} tệp PDF (Dự án: {project_name})...[/cyan]"
    )
    engine = DiscoveryEngine(
        project_name=project_name, output_dir=titleblocks_dir, ai_model=ai_model
    )
    backbone = asyncio.run(engine.discover(pdfs, run_ai=not no_ai))
    engine.export(backbone, output_path)
    console.print(
        f"[green]Thành công: {backbone.total_sheets} bản vẽ từ {backbone.total_files} file -> {output_path}[/green]"
    )


@app.command()
def audit(
    arch: Path = typer.Option(..., "--arch", help="Bản vẽ Kiến trúc (image hoặc PDF)"),
    kc: Path = typer.Option(..., "--kc", help="Bản vẽ Kết cấu (image hoặc PDF)"),
    mep: Path = typer.Option(..., "--mep", help="Bản vẽ Cơ điện (image hoặc PDF)"),
    pccc: Path = typer.Option(..., "--pccc", help="Bản vẽ PCCC (image hoặc PDF)"),
    level: str = typer.Option("L1", "--level", "-l", help="Tên tầng hoặc khu vực"),
    output_dir: Path = typer.Option(Path("audit_output"), "--output-dir", "-o", help="Thư mục đầu ra"),
    ai_model: str = typer.Option("gemini-2.5-flash", "--model", "-m", help="AI Vision Model"),
) -> None:
    """Thực hiện đối soát Quad-View đa bộ môn cho một tầng."""
    engine = QuadViewAuditEngine(output_dir=output_dir, ai_model=ai_model)
    images = [arch, kc, mep, pccc]

    console.print(f"[cyan]Đang đối soát Quad-View cho tầng: {level}...[/cyan]")
    result = asyncio.run(engine.run_audit(images, level))
    console.print(
        f"[green]Kết quả tầng {level}: {result.finding_count} lỗi "
        f"({result.high_severity_count} HIGH)[/green]"
    )
    console.print(f"[yellow]Tóm tắt:[/yellow] {result.summary}")


@app.command()
def batch(
    project_dir: Path = typer.Option(..., "--project-dir", "-p", help="Thư mục gốc dự án"),
    matrix_csv: Path = typer.Option(..., "--matrix", "-m", help="File CSV Ma trận Phối hợp"),
    out_dir: Path = typer.Option(..., "--out-dir", "-o", help="Thư mục xuất báo cáo"),
    ai_model: str = typer.Option("gemini-3.7-flash-high", "--model", help="AI Vision Model"),
) -> None:
    """Chạy quy trình thẩm tra toàn bộ ma trận phối hợp theo lô (Batch)."""
    orchestrator = QCBatchOrchestrator(project_dir, matrix_csv, out_dir)
    console.print(f"[cyan]Bắt đầu chạy Batch QC Orchestrator cho dự án {project_dir.name}...[/cyan]")
    asyncio.run(orchestrator.run_batch(ai_model=ai_model))
    console.print("[green]Hoàn thành thẩm tra theo lô.[/green]")


@app.command()
def pccc(
    tm: Path = typer.Option(..., "--tm", help="File Thuyết minh PCCC (Markdown)"),
    arch: Path = typer.Option(..., "--arch", help="File Kiến trúc PCCC (Markdown)"),
    mep: Path = typer.Option(..., "--mep", help="File MEP PCCC (Markdown)"),
    gopy: Path = typer.Option(None, "--gopy", help="File góp ý PC07 (nếu có)"),
    model: str = typer.Option("qwen-local-primary", "--model", "-m", help="Tên model LLM"),
    out: Path = typer.Option(Path("PCCC_MapReduce_Report.md"), "--out", "-o", help="File báo cáo đầu ra"),
) -> None:
    """Thực hiện thẩm tra chuyên trách PCCC QCVN 06:2022 qua Map-Reduce."""
    thuyet_minh = tm.read_text(encoding="utf-8") if tm.exists() else ""
    arch_pccc = arch.read_text(encoding="utf-8") if arch.exists() else ""
    mep_pccc = mep.read_text(encoding="utf-8") if mep.exists() else ""
    gop_y = gopy.read_text(encoding="utf-8") if (gopy and gopy.exists()) else ""

    engine = PcccMapReduceEngine(ai_model=model)
    console.print(f"[cyan]Bắt đầu quy trình PCCC Map-Reduce sử dụng model {model}...[/cyan]")
    res = asyncio.run(
        engine.execute_full_audit(thuyet_minh, arch_pccc, mep_pccc, gop_y, output_file=out)
    )
    console.print(
        f"[green]Hoàn thành PCCC Audit. Điểm chất lượng: {res.get('overall_quality_score', 'N/A')} "
        f"| Trạng thái QCVN: {res.get('qcvn_compliance_status', 'N/A')}[/green]"
    )


if __name__ == "__main__":
    app()
