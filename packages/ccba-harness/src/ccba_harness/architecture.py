"""ccba_harness.architecture - Architectural Decision & Rationale Lookup (ADR-0009).

Queries ADRs, Traceability Matrices, Git history, and Peer Exchange records to explain
the technical rationale ('WHY was it built this way?') behind codebase architectures.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ADRMatch(BaseModel):
    """Represents a matched Architecture Decision Record."""

    model_config = ConfigDict(extra="forbid")

    adr_id: str
    title: str
    status: str
    decision_summary: str
    file_path: str
    relevance_score: int


class WhyExplanation(BaseModel):
    """Aggregate answer explaining the architectural rationale for a query."""

    model_config = ConfigDict(extra="forbid")

    query: str
    adr_matches: list[ADRMatch] = Field(default_factory=list)
    peer_exchange_matches: list[dict[str, Any]] = Field(default_factory=list)
    git_commits: list[dict[str, Any]] = Field(default_factory=list)
    synthesis: str


def parse_adr_file(file_path: Path, root_dir: Path) -> dict[str, Any]:
    """Extracts metadata, status, context, and decision from an ADR markdown file.

    Args:
        file_path: Path to the ADR markdown file.
        root_dir: Base repository root directory for relative path computation.

    Returns:
        Dictionary containing extracted metadata or empty dict if invalid.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        title = file_path.stem
        first_line = content.strip().splitlines()[0] if content.strip() else ""
        if first_line.startswith("# "):
            title = first_line.replace("# ", "").strip()

        status_match = re.search(r"(?i)\*\*Trạng thái\*\*:\s*([^\n\r]+)", content) or re.search(
            r"(?i)\*\*Status\*\*:\s*([^\n\r]+)", content
        )
        status = status_match.group(1).strip() if status_match else "UNKNOWN"

        dec_match = re.search(r"(?i)##\s*(?:Quyết định|Decision)([\s\S]*?)(?=##|\Z)", content)
        decision = (
            dec_match.group(1).strip()[:300] if dec_match else "No explicit decision section found."
        )

        rel_path = str(
            file_path.relative_to(root_dir) if file_path.is_relative_to(root_dir) else file_path
        )
        return {
            "adr_id": file_path.stem[:4],
            "title": title,
            "status": status,
            "decision": decision.replace("\n", " ").strip(),
            "content": content,
            "path": rel_path,
        }
    except Exception:
        return {}


def search_adrs(query: str, adr_dirs: list[Path], root_dir: Path) -> list[ADRMatch]:
    """Searches ADR directories for matching rationale using deterministic scoring.

    Args:
        query: Query string describing the architecture decision in question.
        adr_dirs: List of directories containing ADR markdown files.
        root_dir: Base repository root for path resolution.

    Returns:
        List of ADRMatch items sorted deterministically by score.
    """
    keywords = [w.lower() for w in re.split(r"\W+", query) if len(w) >= 3]
    matches: list[ADRMatch] = []

    for adr_dir in adr_dirs:
        if not adr_dir.exists():
            continue
        for adr_file in sorted(adr_dir.glob("*.md"), key=lambda p: p.name):
            if adr_file.name in ("README.md", "TEMPLATE.md", "TRACEABILITY_MATRIX.md"):
                continue
            data = parse_adr_file(adr_file, root_dir)
            if not data:
                continue

            content_lower = data.get("content", "").lower()
            score = sum(content_lower.count(kw) for kw in keywords)
            if score > 0 or any(kw in data["title"].lower() for kw in keywords):
                bonus = 10 if any(kw in data["title"].lower() for kw in keywords) else 0
                matches.append(
                    ADRMatch(
                        adr_id=data["adr_id"],
                        title=data["title"],
                        status=data["status"],
                        decision_summary=data["decision"][:250],
                        file_path=data["path"],
                        relevance_score=score + bonus,
                    )
                )

    matches.sort(key=lambda m: (-round(m.relevance_score, 4), m.adr_id, m.title))
    return matches[:5]


def search_peer_exchange(query: str, peer_dirs: list[Path]) -> list[dict[str, Any]]:
    """Searches peer exchange files for peer review discussions and verdicts.

    Args:
        query: Query string.
        peer_dirs: List of directories containing peer exchange markdown files.

    Returns:
        List of hit summaries.
    """
    keywords = [w.lower() for w in re.split(r"\W+", query) if len(w) >= 3]
    results: list[dict[str, Any]] = []

    for peer_dir in peer_dirs:
        if not peer_dir.exists():
            continue
        for md_file in sorted(peer_dir.glob("*.md"), key=lambda p: p.name):
            try:
                text = md_file.read_text(encoding="utf-8")
                hits = [kw for kw in keywords if kw in text.lower()]
                if hits:
                    snippet = text[:200].replace("\n", " ").strip() + "..."
                    results.append(
                        {"file": md_file.name, "matched_keywords": hits, "snippet": snippet}
                    )
            except Exception:
                continue

    return results[:4]


def search_git_commit_rationale(query: str, root_dir: Path, limit: int = 4) -> list[dict[str, Any]]:
    """Queries git commit logs for architectural changes matching keywords.

    Args:
        query: Search query string.
        root_dir: Git repository root directory.
        limit: Maximum number of commits to retrieve.

    Returns:
        List of commit summary dicts.
    """
    clean_query = " ".join([w for w in re.split(r"\W+", query) if len(w) >= 3][:3])
    if not clean_query:
        return []

    try:
        cmd = ["git", "log", f"--grep={clean_query}", f"-n{limit}", "--oneline"]
        proc = subprocess.run(cmd, cwd=root_dir, capture_output=True, text=True, check=False)
        commits: list[dict[str, Any]] = []
        for line in proc.stdout.strip().splitlines():
            if line:
                parts = line.split(" ", 1)
                commits.append({"hash": parts[0], "message": parts[1] if len(parts) > 1 else ""})
        return commits
    except Exception:
        return []


def explain_architecture_why(
    query: str,
    root_dir: Path | None = None,
    adr_dirs: list[Path] | None = None,
    peer_dirs: list[Path] | None = None,
) -> WhyExplanation:
    """Aggregates ADRs, peer records, and commit history into a unified architecture explanation.

    Args:
        query: Architectural question or topic.
        root_dir: Base repository root directory (default: current working directory).
        adr_dirs: Optional custom list of directories containing ADRs.
        peer_dirs: Optional custom list of directories containing peer exchanges.

    Returns:
        WhyExplanation synthesis.
    """
    root = root_dir.resolve() if root_dir else Path.cwd().resolve()
    dirs_to_search = adr_dirs if adr_dirs is not None else [root / "docs" / "adr"]
    peers_to_search = peer_dirs if peer_dirs is not None else [root / ".md" / "peer_exchange"]

    adr_matches = search_adrs(query, dirs_to_search, root)
    peer_matches = search_peer_exchange(query, peers_to_search)
    git_commits = search_git_commit_rationale(query, root)

    if adr_matches:
        top_adr = adr_matches[0]
        synthesis = f"Quyết định được quy định tại ADR-{top_adr.adr_id} ('{top_adr.title}'): {top_adr.decision_summary}"
    elif git_commits:
        synthesis = f"Tìm thấy {len(git_commits)} commit lịch sử liên quan đến '{query}': {git_commits[0].get('message', '')}"
    else:
        synthesis = f"Chưa tìm thấy bản ghi ADR hoặc cam kết lịch sử phù hợp trực tiếp với truy vấn '{query}'."

    return WhyExplanation(
        query=query,
        adr_matches=adr_matches,
        peer_exchange_matches=peer_matches,
        git_commits=git_commits,
        synthesis=synthesis,
    )
