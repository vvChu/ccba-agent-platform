"""Registry query, clause/table extraction, sharded compilation, and PPTX CLI handlers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def handle_query(args: argparse.Namespace) -> int:
    """Handle query subcommand."""
    from ccba_legal.engine import LegalKnowledgeEngine

    corpus = getattr(args, "corpus", None)
    engine = LegalKnowledgeEngine(registry_path=args.registry, corpus_dir=corpus)
    include_expired = getattr(args, "include_expired", False)
    results = engine.search(args.search_query, top_k=args.top_k, include_expired=include_expired)
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0

    print("=================================================================")
    print("          CCBA LEGAL INTEL - KNOWLEDGE REGISTRY QUERY            ")
    print("=================================================================")
    print(f"🔍 Query   : '{args.search_query}' (Top {args.top_k})")
    print(f"📁 Registry: {engine.registry_path}")
    print(f"⚙️ Include Expired: {'YES' if include_expired else 'NO (Default: Current Only)'}")
    print("-----------------------------------------------------------------")
    if not results:
        print("ℹ️ Không tìm thấy văn bản phù hợp với từ khóa.")
        return 0

    for idx, doc in enumerate(results, start=1):
        short_name = doc.get("short_name", "VBPL")
        doc_num = doc.get("document_number", doc.get("id", ""))
        status = str(doc.get("status", "unknown")).upper()
        badge = "🟢 CURRENT" if status in {"ACTIVE", "CURRENT"} else f"🔴 {status}"
        print(f"\n{idx}. [{badge}] {short_name} - {doc_num}")
        if title := doc.get("title", ""):
            print(f"   Tiêu đề: {title}")
        if doc.get("lifecycle_warning"):
            print(f"   {doc['lifecycle_warning']}")
        if rep := doc.get("suggested_replacement"):
            print(
                f"   👉 Thay thế bởi: [{rep.get('short_name') or 'VBPL'} - {rep.get('document_number', '')}]"
            )
    print("\n=================================================================")
    return 0


def handle_get_clause(args: argparse.Namespace) -> int:
    """Handle get-clause subcommand."""
    from ccba_legal.engine import LegalKnowledgeEngine

    engine = LegalKnowledgeEngine(
        registry_path=args.registry, corpus_dir=getattr(args, "corpus", None)
    )
    try:
        res = engine.get_clause(args.doc, args.clause)
    except ValueError as e:
        print(f"❌ Security Error: {e}", file=sys.stderr)
        return 1
    if not res:
        print(
            f"❌ Điều khoản '{args.clause}' không tìm thấy trong văn bản '{args.doc}'.",
            file=sys.stderr,
        )
        return 1
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    print("=================================================================")
    print("         CCBA LEGAL INTEL - TIER-AWARE CLAUSE EXTRACTOR          ")
    print("=================================================================")
    print(f"📄 Văn bản   : {res['doc_id']}")
    print(f"🔖 Điều/Khoản: {res['clause_id']}")
    if res.get("title") and res["title"] != res["clause_id"]:
        print(f"📌 Tiêu đề   : {res['title']}")
    print("-----------------------------------------------------------------\n")
    print(res["content"])
    print("\n=================================================================")
    return 0


def handle_get_table(args: argparse.Namespace) -> int:
    """Handle get-table subcommand."""
    from ccba_legal.engine import LegalKnowledgeEngine

    engine = LegalKnowledgeEngine(
        registry_path=args.registry, corpus_dir=getattr(args, "corpus", None)
    )
    try:
        res = engine.get_table(args.doc, args.table, format=args.format)
    except ValueError as e:
        print(f"❌ Security Error: {e}", file=sys.stderr)
        return 1
    if res is None:
        print(
            f"❌ Bảng số liệu '{args.table}' không tìm thấy trong văn bản '{args.doc}'.",
            file=sys.stderr,
        )
        return 1
    if args.json:
        print(
            json.dumps(
                {"doc_id": args.doc, "table_id": args.table, "format": args.format, "content": res},
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0
    print(res)
    return 0


def _resolve_compile_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    """Resolve default docs directory and target registry YAML path for compile-registry."""
    docs_dir = args.docs_dir
    if not docs_dir:
        cand1, cand2 = Path("legal_docs"), Path(".md/legal_docs")
        docs_dir = cand1 if cand1.is_dir() else (cand2 if cand2.is_dir() else cand1)
    output_path = args.output
    if not output_path:
        cand_out1, cand_out2 = Path(".md/data/legal_registry.yaml"), Path("legal_registry.yaml")
        output_path = cand_out1 if cand_out1.parent.is_dir() else cand_out2
    return Path(docs_dir), Path(output_path)


def handle_compile_registry(args: argparse.Namespace) -> int:
    """Handle compile-registry subcommand."""
    from ccba_legal.compiler import compile_sharded_registry

    docs_dir, output_path = _resolve_compile_paths(args)
    print("=================================================================")
    print("         CCBA LEGAL INTELLIGENCE (SHARDED REGISTRY COMPILER)      ")
    print("=================================================================")
    print(f"📂 Docs Directory: {docs_dir}")
    print(f"📄 Target Registry: {output_path}")
    print(f"🔍 Mode: {'Check Synchronization (--check)' if args.check else 'Compile & Write'}")

    compiled, is_in_sync, issues = compile_sharded_registry(
        docs_dir=docs_dir,
        output_file=output_path,
        base_registry_path=args.base,
        check_only=args.check,
    )
    cats = ("laws", "decrees", "circulars", "decisions", "resolutions", "standards")
    doc_count = sum(len(compiled[k]) for k in cats if k in compiled)
    print(f"\n✅ Total compiled legal documents: {doc_count}")
    for cat in cats:
        if count := len(compiled.get(cat, [])):
            print(f"   - {cat}: {count}")

    if args.check:
        if is_in_sync:
            print(
                "\n🛡️ [CHECK PASS] legal_registry.yaml is 100% in sync with sharded metadata.yaml bundles."
            )
            return 0
        print("\n❌ [CHECK FAILED] Discrepancies detected between registry and sharded bundles:")
        for iss in issues:
            print(f"   - {iss}")
        return 1
    print(f"\n🎉 Successfully compiled registry to: {output_path}")
    return 0


def handle_pptx(args: argparse.Namespace) -> int:
    """Handle pptx subcommand: Convert markdown into CCBA branded PPTX presentation (ADR-0044)."""
    try:
        from ccba_ooxml.pptx.deck_builder import build_presentation_from_markdown
        from ccba_ooxml.pptx.templates import CCBAPresentationTheme
    except ImportError as e:
        print(f"❌ Error: ccba_ooxml package is required for PPTX generation: {e}", file=sys.stderr)
        return 1

    input_path: Path = args.input_markdown
    if not input_path.exists() or not input_path.is_file():
        print(
            f"❌ Error: Input markdown file does not exist or is not a file: {input_path}",
            file=sys.stderr,
        )
        return 1

    output_path: Path = args.output if args.output else input_path.with_suffix(".pptx")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    theme = CCBAPresentationTheme.default()
    try:
        res_path = build_presentation_from_markdown(
            markdown_text_or_path=input_path, output_path=output_path, theme=theme
        )
        print(f"🎉 Successfully generated CCBA presentation: {res_path}")
        return 0
    except Exception as e:
        print(f"❌ Error generating presentation: {e}", file=sys.stderr)
        return 1
