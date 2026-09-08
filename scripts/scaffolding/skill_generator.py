#!/usr/bin/env python
"""skill_generator.py - Autonomous Skill Scaffolder for CCBA Platform.

Parses script CLI interfaces (argparse / click / AST) to generate standardized
CCBA Skills (SKILL.md, cli_spec.yaml, references/*.md per ADR-0057).

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

import yaml

# Ensure project root and ccba-harness package are in sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_HARNESS_SRC = _ROOT / "packages" / "ccba-harness" / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from ccba_harness.gpi import (
    ArchitectureTier,
    DecisionRequest,
    GPIMetrics,
    evaluate_two_stage_decision,
)

# Mock click if not installed to avoid import crashes
try:
    import click

    HAS_CLICK = True
except ImportError:
    HAS_CLICK = False
    click = None  # type: ignore[assignment]


# ==========================================
# 1. PARSING KỸ THUẬT: DYNAMIC INSPECTION
# ==========================================


def get_argparse_schema(parser: Any) -> dict[str, Any]:
    """Trích xuất JSON Schema từ đối tượng ArgumentParser của argparse."""
    properties: dict[str, Any] = {}
    required: list[str] = []

    # Duyệt qua các action định nghĩa trong parser
    for action in parser._actions:
        # Bỏ qua action trợ giúp mặc định
        action_class_name = action.__class__.__name__
        if action_class_name == "_HelpAction" or "Help" in action_class_name:
            continue

        # Xác định key của tham số trong schema
        param_name = action.dest
        if action.option_strings:
            longest_opt = max(action.option_strings, key=len)
            param_name = longest_opt.lstrip("-").replace("-", "_")

        # Xác định kiểu dữ liệu
        json_type = "string"
        if action.type is int:
            json_type = "integer"
        elif action.type is float:
            json_type = "number"
        elif action.type is bool:
            json_type = "boolean"

        param_schema: dict[str, Any] = {
            "type": json_type,
            "description": action.help or f"Tham số {param_name}",
        }

        # Bổ sung các giá trị enum nếu có choices
        if action.choices:
            param_schema["enum"] = list(action.choices)

        # Bổ sung giá trị mặc định nếu có
        if action.default is not None and str(action.default) != "==SUPPRESS==":
            param_schema["default"] = action.default

        properties[param_name] = param_schema

        # Positional arguments (không có option_strings) thường là bắt buộc
        if action.required or not action.option_strings:
            required.append(param_name)

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required

    return schema


def get_click_schema(command: Any) -> dict[str, Any]:
    """Trích xuất JSON Schema từ đối tượng click.Command."""
    properties: dict[str, Any] = {}
    required: list[str] = []

    for param in command.params:
        param_name = param.name

        # Xác định kiểu dữ liệu trong Click
        json_type = "string"
        click_type_name = param.type.name.lower() if hasattr(param.type, "name") else ""

        if "int" in click_type_name:
            json_type = "integer"
        elif "float" in click_type_name or "number" in click_type_name:
            json_type = "number"
        elif "bool" in click_type_name or "boolean" in click_type_name:
            json_type = "boolean"

        param_schema: dict[str, Any] = {
            "type": json_type,
            "description": getattr(param, "help", None) or f"Tham số {param_name}",
        }

        # Bổ sung enum nếu click type là Choice
        if hasattr(param.type, "choices") and param.type.choices:
            param_schema["enum"] = list(param.type.choices)

        if param.default is not None:
            param_schema["default"] = param.default

        properties[param_name] = param_schema

        if param.required:
            required.append(param_name)

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required

    return schema


def inspect_via_dynamic_import(script_path: Path) -> tuple[str, dict[str, Any], str]:
    """Import runtime script Python và inspect để lấy parser.

    Trả về: (command_base_string, commands_dict, module_docstring)
    """
    module_name = script_path.stem
    spec = importlib.util.spec_from_file_location(module_name, str(script_path))
    if not spec or not spec.loader:
        raise ImportError(f"Không thể tạo module spec cho {script_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    docstring = inspect.getdoc(module) or ""

    # 1. Trường hợp sử dụng click
    click_commands: list[tuple[str, Any]] = []
    if HAS_CLICK:
        for name, obj in inspect.getmembers(module):
            if isinstance(obj, click.Command):
                click_commands.append((name, obj))

    if click_commands:
        group_obj = next(
            (obj for name, obj in click_commands if isinstance(obj, click.Group)), None
        )
        if group_obj:
            commands_map: dict[str, Any] = {}
            for sub_name, sub_cmd in group_obj.commands.items():
                commands_map[sub_name] = {
                    "command_base": f"python scripts/{script_path.name} {sub_name}",
                    "input_schema": get_click_schema(sub_cmd),
                }
            return f"python scripts/{script_path.name}", commands_map, docstring
        else:
            cmd_name, cmd_obj = click_commands[0]
            commands_map = {
                "default": {
                    "command_base": f"python scripts/{script_path.name}",
                    "input_schema": get_click_schema(cmd_obj),
                }
            }
            return f"python scripts/{script_path.name}", commands_map, docstring

    # 2. Trường hợp sử dụng argparse (tìm hàm get_parser())
    if hasattr(module, "get_parser"):
        get_parser_fn = module.get_parser
        parser = get_parser_fn()
        subparsers_action = next(
            (
                action
                for action in parser._actions
                if action.__class__.__name__ == "_SubParsersAction"
            ),
            None,
        )

        if subparsers_action:
            commands_map = {}
            for sub_name, sub_parser in subparsers_action.choices.items():
                commands_map[sub_name] = {
                    "command_base": f"python scripts/{script_path.name} {sub_name}",
                    "input_schema": get_argparse_schema(sub_parser),
                }
            return f"python scripts/{script_path.name}", commands_map, docstring
        else:
            commands_map = {
                "default": {
                    "command_base": f"python scripts/{script_path.name}",
                    "input_schema": get_argparse_schema(parser),
                }
            }
            return f"python scripts/{script_path.name}", commands_map, docstring

    raise ValueError(
        "Script không cung cấp click decorators hoặc hàm get_parser() để thực hiện dynamic inspection."
    )


# ==========================================
# 2. PARSING KỸ THUẬT: FALLBACK STATIC AST
# ==========================================


class ASTCLIParser(ast.NodeVisitor):
    """AST Visitor để phân tích cú pháp tĩnh các arguments của argparse/click."""

    def __init__(self) -> None:
        self.properties: dict[str, Any] = {}
        self.required: list[str] = []
        self.subcommands: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument":
            self.parse_add_argument(node)
        self.generic_visit(node)

    def parse_add_argument(self, node: ast.Call) -> None:
        opts: list[str] = []
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                opts.append(arg.value)

        if not opts:
            return

        longest_opt = max(opts, key=len)
        param_name = longest_opt.lstrip("-").replace("-", "_")

        param_schema: dict[str, Any] = {"type": "string", "description": f"Tham số {param_name}"}
        is_required = not longest_opt.startswith("-")

        for kw in node.keywords:
            if kw.arg == "help" and isinstance(kw.value, ast.Constant):
                param_schema["description"] = kw.value.value
            elif kw.arg == "default" and isinstance(kw.value, ast.Constant):
                param_schema["default"] = kw.value.value
            elif kw.arg == "required" and isinstance(kw.value, ast.Constant):
                is_required = bool(kw.value.value)
            elif kw.arg == "choices" and isinstance(kw.value, ast.List):
                enum_vals = []
                for elt in kw.value.elts:
                    if isinstance(elt, ast.Constant):
                        enum_vals.append(elt.value)
                if enum_vals:
                    param_schema["enum"] = enum_vals
            elif kw.arg == "type" and isinstance(kw.value, ast.Name):
                type_map = {"int": "integer", "float": "number", "bool": "boolean"}
                param_schema["type"] = type_map.get(kw.value.id, "string")

        self.properties[param_name] = param_schema
        if is_required:
            self.required.append(param_name)


def inspect_via_static_ast(script_path: Path) -> tuple[str, dict[str, Any], str]:
    """Fallback phân tích cú pháp tĩnh file Python bằng AST."""
    with open(script_path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(script_path))

    docstring = ast.get_docstring(tree) or ""
    visitor = ASTCLIParser()
    visitor.visit(tree)

    commands_map = {
        "default": {
            "command_base": f"python scripts/{script_path.name}",
            "input_schema": {
                "type": "object",
                "properties": visitor.properties,
                "required": visitor.required,
            },
        }
    }
    return f"python scripts/{script_path.name}", commands_map, docstring


# ==========================================
# 3. SINH FILE CẤU HÌNH VÀ WORKFLOW
# ==========================================


def write_cli_spec(output_path: Path, commands: dict[str, Any]) -> None:
    """Ghi cấu trúc CLI spec ra tệp yaml."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {"commands": commands}
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)
    print(f"[Info] Đã ghi tệp đặc tả kỹ thuật: {output_path.resolve()}")


def write_skill_markdown(
    output_path: Path,
    skill_name: str,
    docstring: str,
    bundle: str = "_software",
    gpi_metrics: GPIMetrics | None = None,
) -> None:
    """Ghi tệp tin SKILL.md mẫu nghiệp vụ ban đầu (chỉ ghi nếu chưa có)."""
    if output_path.exists():
        print(
            f"[Info] File SKILL.md đã tồn tại. Bỏ qua ghi đè để bảo vệ nội dung viết tay: {output_path.resolve()}"
        )
        return

    desc = (
        docstring.strip().split("\n")[0]
        if docstring
        else f"Tự động tương tác với công cụ {skill_name}."
    )

    clean_trigger = skill_name.removeprefix("ccba-").removeprefix("bigbim-")
    triggers_yaml = (
        f"- {clean_trigger}\n- {skill_name}" if clean_trigger != skill_name else f"- {skill_name}"
    )

    gpi_block = ""
    if gpi_metrics is not None:
        gpi_block = f"\ngpi: {{s: {gpi_metrics.s}, k: {gpi_metrics.k}, a: {gpi_metrics.a}, p: {gpi_metrics.p}}}"

    content = f"""---
name: {skill_name}
description: {desc}
bundle: {bundle}
user-invocable: true
disable-model-invocation: true
command: /{skill_name}
triggers:
{triggers_yaml}{gpi_block}
---

# Kỹ năng {skill_name}

{docstring.strip() if docstring else "Mô tả nghiệp vụ chi tiết của kỹ năng."}

## Quy trình Vận hành của Agent

---

### Bước 1: Khởi động và Xác thực (Initialization & Environment Verification)
*   Kiểm tra sự tồn tại của script và nạp tham chiếu kỹ thuật tại file `cli_spec.yaml` cùng cấp.
*   Xác minh các tham số và tùy chọn cấu hình môi trường thực thi trước khi gọi công cụ.
*   **Tiêu chí hoàn thành:** Tệp script tồn tại và schema tham số được nạp thành công.

---

### Bước 2: Bảo mật & Chốt chặn Maskara Gate (Security & Redaction Protocol)
*   **BẮT BUỘC:** Nếu đầu vào có chứa tệp tin cục bộ, Agent phải chạy quét bảo mật qua `scripts/maskara.py` trước khi thực thi.
*   Không được truyền khóa bí mật (API keys), mật khẩu hoặc thông tin nội bộ không được kiểm duyệt.
*   **Tiêu chí hoàn thành:** Không còn khóa bí mật hoặc thông tin nhạy cảm rò rỉ.

---

### Bước 3: Thực thi dòng lệnh (CLI Invocation & Error Interception)
*   Đọc các tham số của người dùng, map tương ứng vào JSON Schema trong `cli_spec.yaml`.
*   Gọi lệnh qua terminal và bắt lỗi (`stdout`/`stderr`), ghi nhận chi tiết mã trả về.
*   **Tiêu chí hoàn thành:** Lệnh thực thi thành công với mã trả về 0.

---

### Bước 4: Hậu xử lý & Báo cáo QC (Post-processing & Attribution)
*   Định dạng đầu ra sạch sẽ, cấu trúc dữ liệu rõ ràng dễ tra cứu.
*   Chèn dòng Attribution và Disclaimer của CCBA vào cuối tài liệu.
*   **Tiêu chí hoàn thành:** Kết quả đầu ra được xác thực và trình bày rõ ràng.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[Info] Đã tạo file tri thức nghiệp vụ mẫu: {output_path.resolve()}")


def write_reference_markdown(
    output_path: Path,
    sub_name: str,
    parent_skill: str,
    docstring: str,
    gpi_metrics: GPIMetrics,
    gpi_score: float,
    script_path: Path,
) -> None:
    """Ghi tệp Progressive Reference (Tier 2A) trong references/ của Master Skill."""
    if output_path.exists():
        print(f"[Info] File reference đã tồn tại. Bỏ qua ghi đè: {output_path.resolve()}")
        return

    try:
        src_display = script_path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except (ValueError, RuntimeError):
        src_display = script_path.as_posix() if isinstance(script_path, Path) else str(script_path)

    content = f"""# Progressive Reference: {sub_name}

> Thuộc Master Skill [`{parent_skill}`](../SKILL.md).

{docstring.strip() if docstring else f"Tài liệu hướng dẫn nghiệp vụ tham chiếu tăng tiến cho {sub_name}."}

## 1. Thông Tin Định Tuyến Kiến Trúc (ADR-0057)

- **Phân loại:** Tier 2A (Progressive Reference)
- **Chỉ số GPI:** {gpi_score:.2f} (S={gpi_metrics.s}, K={gpi_metrics.k}, A={gpi_metrics.a}, P={gpi_metrics.p})
- **Tệp nguồn:** `{src_display}`

## 2. Hướng Dẫn Vận Hành Cho Agent

Agent chỉ nạp tài liệu này theo nguyên tắc **Progressive Disclosure** (khi thực sự cần năng lực chuyên biệt):
`view_file` tới `.agents/skills/{parent_skill}/references/{sub_name}.md`.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[Info] Đã tạo file Progressive Reference: {output_path.resolve()}")


# ==========================================
# 4. HÀM ĐIỀU PHỐI ĐẦU RA (API CHÍNH)
# ==========================================


def create_skill_from_script(
    script_path_str: str | Path,
    skill_name: str | None = None,
    skills_base_dir: Path | None = None,
    workflows_base_dir: Path | None = None,
    bundle: str = "_software",
    is_deterministic: bool = False,
    is_orchestrated: bool = False,
    s: float | None = None,
    k: float | None = None,
    a: float | None = None,
    p: float | None = None,
    parent: str | None = None,
) -> int:
    """Tạo mới cấu trúc Skill hoặc Progressive Reference từ tệp Python script."""
    script_p = Path(script_path_str)
    if not script_p.exists():
        print(f"ERROR: Tệp tin script '{script_path_str}' không tồn tại.", file=sys.stderr)
        return 1

    raw_name = skill_name or script_p.stem.replace("_helper", "").replace("_", "-")
    if (
        not raw_name.startswith("ccba-")
        and not raw_name.startswith("bigbim-")
        and raw_name != "platform-loader"
    ):
        name = f"ccba-{raw_name}"
    else:
        name = raw_name

    base_skills = skills_base_dir or (Path(".agents") / "skills")

    # Cổng 0: Determinism Gate
    if is_deterministic:
        request = DecisionRequest(name=name, is_deterministic=True, parent_skill=parent)
        decision = evaluate_two_stage_decision(request)
        print("\n[ERROR] Cổng 0 (Determinism Gate) từ chối tạo Skill phẳng:", file=sys.stderr)
        print(f"👉 {decision.rationale}", file=sys.stderr)
        print(
            "👉 Hướng dẫn: Đưa logic vào 'packages/*/src/' thay vì tạo Skill phẳng độc lập.\n",
            file=sys.stderr,
        )
        return 1

    # Cổng 1: Orchestration Gate
    if is_orchestrated:
        request = DecisionRequest(name=name, is_orchestrated=True, parent_skill=parent)
        decision = evaluate_two_stage_decision(request)
        print("\n[ERROR] Cổng 1 (Orchestration Gate) từ chối tạo Skill phẳng:", file=sys.stderr)
        print(f"👉 {decision.rationale}", file=sys.stderr)
        print(
            "👉 Hướng dẫn: Tạo workflow trong '.agents/workflows/' thay vì tạo Skill phẳng độc lập.\n",
            file=sys.stderr,
        )
        return 1

    # Stage 2: Đánh giá GPI
    has_any_gpi = any(x is not None for x in (s, k, a, p))
    has_all_gpi = all(x is not None for x in (s, k, a, p))

    if parent is not None and not has_all_gpi:
        print(
            "ERROR: Khi chỉ định Master Skill sở hữu qua '--parent', bắt buộc phải cung cấp đầy đủ cả 4 chỉ số GPI: --s, --k, --a, --p.",
            file=sys.stderr,
        )
        return 1

    if has_any_gpi and not has_all_gpi:
        print(
            "ERROR: Khi đánh giá GPI, bắt buộc phải cung cấp đầy đủ cả 4 chỉ số: --s, --k, --a, --p.",
            file=sys.stderr,
        )
        return 1

    gpi_metrics: GPIMetrics | None = None
    if has_all_gpi:
        assert s is not None and k is not None and a is not None and p is not None
        try:
            gpi_metrics = GPIMetrics(s=float(s), k=float(k), a=float(a), p=float(p))
        except (TypeError, ValueError) as err:
            print(f"ERROR: Tham số GPI không hợp lệ: {err}", file=sys.stderr)
            return 1

        request = DecisionRequest(
            name=name,
            is_deterministic=False,
            is_orchestrated=False,
            gpi_metrics=gpi_metrics,
            parent_skill=parent,
        )
        decision = evaluate_two_stage_decision(request)

        # Nếu GPI < 12.0 (Tier 2A - Progressive Reference)
        if decision.tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE:
            if not parent:
                print(
                    f"\n[ERROR] Chỉ số GPI ({decision.gpi_score:.2f}) < 12.0: Phân loại Tier 2A (Progressive Reference).\n"
                    f"Từ chối tạo Skill độc lập tại .agents/skills/{name}/.\n"
                    f"Vui lòng chỉ định Master Skill sở hữu thông qua tham số '--parent <master-skill>' để tạo 'references/<name>.md'.\n",
                    file=sys.stderr,
                )
                return 1

            parent_dir = base_skills / parent
            if not parent_dir.is_dir():
                parent_dir = base_skills / f"ccba-{parent}"
            if not parent_dir.is_dir():
                parent_dir = Path(parent)

            if not parent_dir.is_dir():
                print(
                    f"\n[ERROR] Master Skill '{parent}' không tồn tại hoặc không phải là thư mục trong '{base_skills}'.\n"
                    f"Không thể tạo 'references/<name>.md'. Vui lòng kiểm tra lại.\n",
                    file=sys.stderr,
                )
                return 1

            try:
                _, _, docstring = inspect_via_dynamic_import(script_p)
            except Exception:
                try:
                    _, _, docstring = inspect_via_static_ast(script_p)
                except Exception as ex:
                    print(f"ERROR: Phân tích script thất bại: {ex}", file=sys.stderr)
                    return 3

            ref_dir = parent_dir / "references"
            ref_dir.mkdir(parents=True, exist_ok=True)
            clean_sub_name = (
                name.removeprefix("ccba-")
                .removeprefix("bigbim-")
                .removesuffix(".md")
                .replace("_", "-")
                .lower()
            )
            ref_file = ref_dir / f"{clean_sub_name}.md"

            write_reference_markdown(
                output_path=ref_file,
                sub_name=clean_sub_name,
                parent_skill=parent_dir.name,
                docstring=docstring,
                gpi_metrics=gpi_metrics,
                gpi_score=decision.gpi_score or 0.0,
                script_path=script_p,
            )

            print(f"\nSUCCESS: Đã tạo Progressive Reference (Tier 2A) tại '{ref_file.resolve()}'")
            print(f"👉 Thuộc Master Skill: {parent_dir.name}")
            print(f"👉 Chỉ số GPI: {decision.gpi_score:.2f} < 12.0\n")
            return 0

    # Nếu GPI >= 12.0 (hoặc không truyền metrics để giữ tương thích ngược) -> Tier 2B Standalone Kernel Skill
    skill_dir = base_skills / name
    skill_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Info] Bắt đầu phân tích script '{script_p.name}'...")
    try:
        _, commands, docstring = inspect_via_dynamic_import(script_p)
        print("[Info] Phân tích động (Dynamic Inspection) thành công.")
    except Exception as e:
        print(
            f"[Warn] Phân tích động thất bại ({e}). Thử chuyển sang phân tích tĩnh (Static AST)...",
            file=sys.stderr,
        )
        try:
            _, commands, docstring = inspect_via_static_ast(script_p)
            print("[Info] Fallback phân tích tĩnh (Static AST) thành công.")
        except Exception as ex:
            print(
                f"ERROR: Cả hai phương pháp phân tích đều thất bại. Chi tiết: {ex}", file=sys.stderr
            )
            return 3

    write_cli_spec(skill_dir / "cli_spec.yaml", commands)
    write_skill_markdown(
        skill_dir / "SKILL.md", name, docstring, bundle=bundle, gpi_metrics=gpi_metrics
    )

    print(f"\nSUCCESS: Tạo Skill '{name}' thành công!")
    print(f"👉 Thư mục skill: {skill_dir.resolve()}")
    print(f"👉 Lệnh Slash Command: /{name}\n")
    return 0


def sync_all_skills(skills_base_dir: Path | None = None) -> int:
    """Quét toàn bộ thư mục skills cục bộ và đồng bộ lại cli_spec.yaml nếu có file script tương ứng."""
    skills_dir = skills_base_dir or (Path(".agents") / "skills")
    if not skills_dir.exists():
        print("[Info] Chưa có thư mục skills nào để đồng bộ.")
        return 0

    success_count = 0
    fail_count = 0

    print("[Info] Bắt đầu quét và đồng bộ các Skills...")
    for folder in skills_dir.iterdir():
        if not folder.is_dir():
            continue

        cli_spec_file = folder / "cli_spec.yaml"
        if not cli_spec_file.exists():
            continue

        name_snake = folder.name.replace("-", "_")
        name_no_prefix = folder.name.replace("ccba-", "").replace("bigbim-", "").replace("-", "_")
        candidates = [
            folder / "scripts" / f"{name_snake}.py",
            folder / "scripts" / f"{name_no_prefix}.py",
            Path("scripts") / f"{name_snake}.py",
            Path("scripts") / f"{name_no_prefix}.py",
            Path("scripts") / f"{name_snake}_helper.py",
            Path("scripts") / f"{name_no_prefix}_helper.py",
            Path("scripts") / "scaffolding" / f"{name_snake}.py",
            Path("scripts") / "scaffolding" / f"{name_no_prefix}.py",
            Path("scripts") / "governance" / f"{name_snake}.py",
            Path("scripts") / "governance" / f"{name_no_prefix}.py",
            Path("scripts") / "legal" / f"{name_snake}.py",
            Path("scripts") / "legal" / f"{name_no_prefix}.py",
            Path("scripts") / "security" / f"{name_snake}.py",
            Path("scripts") / "security" / f"{name_no_prefix}.py",
        ]

        target_script = next((c for c in candidates if c.exists()), None)
        if not target_script:
            continue

        print(f"\n[Info] Đồng bộ hóa Skill '{folder.name}' từ script '{target_script.name}'...")
        try:
            _, commands, _ = inspect_via_dynamic_import(target_script)
            write_cli_spec(cli_spec_file, commands)
            success_count += 1
        except Exception as e:
            try:
                _, commands, _ = inspect_via_static_ast(target_script)
                write_cli_spec(cli_spec_file, commands)
                success_count += 1
            except Exception as ex:
                print(f"[Error] Không thể đồng bộ '{folder.name}': {e} | {ex}", file=sys.stderr)
                fail_count += 1

    print(f"\nSUCCESS: Đồng bộ hoàn tất! (Thành công: {success_count}, Thất bại: {fail_count})\n")
    return 0 if fail_count == 0 else 3


def main(args_list: list[str] | None = None) -> int:
    """CLI entry point for skill scaffolder."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass
        if hasattr(sys.stderr, "reconfigure"):
            try:
                sys.stderr.reconfigure(encoding="utf-8")
            except Exception:
                pass

    parser = argparse.ArgumentParser(description="CCBA Autonomous Skill & Workflow Scaffolder")
    parser.add_argument("--script", help="Đường dẫn file Python script nguồn")
    parser.add_argument(
        "--name", "-n", default=None, help="Tên Skill muốn tạo (mặc định theo tên script)"
    )
    parser.add_argument(
        "--bundle",
        default="_software",
        choices=["_software", "_core", "_qc", "_consulting", "_bim"],
        help="Taxonomy bundle phân loại kỹ năng (mặc định: _software)",
    )
    parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Cổng 0: Tác vụ giải quyết 100%% bằng giải thuật xác định (chuyển sang package)",
    )
    parser.add_argument(
        "--orchestrated",
        action="store_true",
        help="Cổng 1: Tác vụ điều phối đa tác tử / HITL (chuyển sang workflow)",
    )
    parser.add_argument(
        "--s", type=float, default=None, help="Chỉ số GPI - Reasoning Steps (1.0 - 5.0)"
    )
    parser.add_argument(
        "--k",
        type=float,
        default=None,
        help="Chỉ số GPI - Interface / Schema Complexity (1.0 - 5.0)",
    )
    parser.add_argument(
        "--a",
        type=float,
        default=None,
        help="Chỉ số GPI - Autonomous Model Invocation (1.0 - 5.0)",
    )
    parser.add_argument(
        "--p",
        type=float,
        default=None,
        help="Chỉ số GPI - Parent Domain Coupling (1.0 - 5.0)",
    )
    parser.add_argument(
        "--parent",
        type=str,
        default=None,
        help="Tên Master Skill sở hữu nếu phân loại Tier 2A (Progressive Reference)",
    )
    parser.add_argument(
        "--sync-all", action="store_true", help="Đồng bộ lại tất cả cli_spec.yaml từ scripts"
    )

    args = parser.parse_args(args_list)

    if args.sync_all:
        return sync_all_skills()

    if not args.script:
        parser.print_help()
        return 1

    return create_skill_from_script(
        script_path_str=args.script,
        skill_name=args.name,
        bundle=args.bundle,
        is_deterministic=args.deterministic,
        is_orchestrated=args.orchestrated,
        s=args.s,
        k=args.k,
        a=args.a,
        p=args.p,
        parent=args.parent,
    )


if __name__ == "__main__":
    sys.exit(main())
