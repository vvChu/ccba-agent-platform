"""Module-level static AST expression evaluator for obfuscated command detection."""

from __future__ import annotations

import ast
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

_BINOP_MAP: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
    ast.Add: lambda left, right: left + right,
    ast.Sub: lambda left, right: left - right,
    ast.Mult: lambda left, right: left * right,
    ast.Div: lambda left, right: left / right,
    ast.FloorDiv: lambda left, right: left // right,
    ast.Mod: lambda left, right: left % right,
    ast.Pow: lambda left, right: left**right,
    ast.LShift: lambda left, right: left << right,
    ast.RShift: lambda left, right: left >> right,
    ast.BitOr: lambda left, right: left | right,
    ast.BitAnd: lambda left, right: left & right,
    ast.BitXor: lambda left, right: left ^ right,
}

_DUNDER_BINOP_ATTRS: frozenset[str] = frozenset(
    {
        "__or__",
        "__and__",
        "__xor__",
        "__lshift__",
        "__rshift__",
        "__add__",
        "__sub__",
        "__mul__",
        "__truediv__",
        "__floordiv__",
        "__mod__",
        "__pow__",
    }
)


@dataclass
class _AstEvalContext:
    """Shared mutable scope and environment mocks for AST partial evaluation."""

    target_env: dict[str, str] | None = None
    sys_argv_mock: list[str] | None = None
    local_vars: dict[str, Any] = field(default_factory=dict)
    max_depth: int = 100


def _eval_name_node(n: ast.Name, ctx: _AstEvalContext) -> Any:
    """Resolve local variables, safe builtin refs, loaded sys.modules, or dynamic import."""
    if n.id in ctx.local_vars:
        return ctx.local_vars[n.id]
    if n.id == "os":
        return os
    if n.id == "sys":
        return sys
    if n.id == "getattr":
        return getattr
    if n.id in sys.modules:
        return sys.modules[n.id]
    try:
        return __import__(n.id)
    except Exception:
        return None


def _eval_assign_node(n: ast.Assign, ctx: _AstEvalContext, depth: int) -> Any:
    """Evaluate assignment RHS and bind any Name targets into shared `ctx.local_vars`."""
    val = _eval_ast_node(n.value, ctx, depth + 1)
    for target in n.targets:
        if isinstance(target, ast.Name):
            ctx.local_vars[target.id] = val
    return val


def _eval_subscript_node(n: ast.Subscript, ctx: _AstEvalContext, depth: int) -> Any:
    """Evaluate slice or index subscript expressions safely."""
    val = _eval_ast_node(n.value, ctx, depth + 1)
    sl = n.slice
    if isinstance(sl, ast.Slice):
        lower = _eval_ast_node(sl.lower, ctx, depth + 1) if sl.lower is not None else None
        upper = _eval_ast_node(sl.upper, ctx, depth + 1) if sl.upper is not None else None
        step = _eval_ast_node(sl.step, ctx, depth + 1) if sl.step is not None else None
        if val is not None:
            try:
                return val[slice(lower, upper, step)]
            except Exception:
                return None
        return None
    idx = _eval_ast_node(sl, ctx, depth + 1)
    if val is not None and idx is not None:
        try:
            return val[idx]
        except Exception:
            return None
    return None


def _eval_attribute_node(n: ast.Attribute, ctx: _AstEvalContext, depth: int) -> Any:
    """Evaluate attribute lookups, intercepting `os.environ` and `sys.argv`."""
    val = _eval_ast_node(n.value, ctx, depth + 1)
    if val is os and n.attr == "environ":
        return ctx.target_env
    if val is sys and n.attr == "argv":
        return ctx.sys_argv_mock
    if val is not None:
        try:
            return getattr(val, n.attr)
        except Exception:
            return None
    return None


def _eval_binop_or_unary_node(n: ast.BinOp | ast.UnaryOp, ctx: _AstEvalContext, depth: int) -> Any:
    """Evaluate binary and unary arithmetic/string/bitwise AST operations."""
    if isinstance(n, ast.UnaryOp):
        operand_val = _eval_ast_node(n.operand, ctx, depth + 1)
        if operand_val is None:
            return None
        if isinstance(n.op, ast.USub):
            try:
                return -operand_val
            except Exception:
                return None
        if isinstance(n.op, ast.UAdd):
            return operand_val
        return None

    left_val = _eval_ast_node(n.left, ctx, depth + 1)
    right_val = _eval_ast_node(n.right, ctx, depth + 1)
    op_fn = _BINOP_MAP.get(type(n.op))
    if left_val is not None and right_val is not None and op_fn is not None:
        try:
            return op_fn(left_val, right_val)
        except Exception:
            return None
    return None


def _eval_attr_call(n: ast.Call, attr_node: ast.Attribute, ctx: _AstEvalContext, depth: int) -> Any:
    """Evaluate safe attribute method calls (`decode`, `encode`, `join`, dunder ops)."""
    val = _eval_ast_node(attr_node.value, ctx, depth + 1)
    attr = attr_node.attr
    try:
        if attr == "decode" and isinstance(val, bytes):
            return val.decode("utf-8", errors="ignore")
        if attr == "encode" and isinstance(val, str):
            return val.encode("utf-8")
        if attr == "join" and isinstance(val, (str, bytes)) and len(n.args) == 1:
            arg_val = _eval_ast_node(n.args[0], ctx, depth + 1)
            if isinstance(arg_val, (list, tuple)):
                return val.join(arg_val)
        if attr in _DUNDER_BINOP_ATTRS and len(n.args) == 1:
            arg_val = _eval_ast_node(n.args[0], ctx, depth + 1)
            method = getattr(val, attr, None) if arg_val is not None else None
            if method is not None:
                return method(arg_val)
    except Exception:
        return None
    return None


def _eval_simple_builtin_call(
    func_name: str, args: list[ast.expr], ctx: _AstEvalContext, depth: int
) -> Any:
    """Evaluate safe constructor/conversion builtin calls (`bytes`, `int`, `list`, `chr`, `ord`)."""
    evaled = [_eval_ast_node(a, ctx, depth + 1) for a in args]
    try:
        if func_name == "bytes":
            if not args:
                return b""
            if len(args) == 1 and evaled[0] is not None:
                return bytes(evaled[0])
            if len(args) == 2 and evaled[0] is not None and evaled[1] is not None:
                return bytes(evaled[0], evaled[1])
        elif func_name == "int":
            if not args:
                return 0
            if len(args) == 1 and evaled[0] is not None:
                return int(evaled[0])
            if len(args) == 2 and evaled[0] is not None and evaled[1] is not None:
                return int(evaled[0], evaled[1])
        elif func_name == "list":
            return [] if not args else (list(evaled[0]) if evaled[0] is not None else None)
        elif func_name == "chr" and len(args) == 1 and isinstance(evaled[0], int):
            return chr(evaled[0])
        elif (
            func_name == "ord"
            and len(args) == 1
            and isinstance(evaled[0], str)
            and len(evaled[0]) == 1
        ):
            return ord(evaled[0])
    except Exception:
        return None
    return None


def _eval_map_lambda_call(
    func_node: ast.Lambda, iter_val: Any, ctx: _AstEvalContext, depth: int
) -> Any:
    """Evaluate `map(lambda x: ..., iterable)` using `ctx.local_vars` with cleanup."""
    if len(func_node.args.args) != 1:
        return None
    arg_name = func_node.args.args[0].arg
    results: list[Any] = []
    old_val = ctx.local_vars.get(arg_name)
    try:
        for count, item in enumerate(iter_val, start=1):
            if count > 1000:
                break
            ctx.local_vars[arg_name] = item
            res = _eval_ast_node(func_node.body, ctx, depth + 1)
            if res is None:
                break
            results.append(res)
        if all(isinstance(x, int) and 0 <= x <= 255 for x in results):
            return bytes(results)
        return results
    finally:
        if old_val is not None:
            ctx.local_vars[arg_name] = old_val
        else:
            ctx.local_vars.pop(arg_name, None)


def _eval_map_call(n: ast.Call, ctx: _AstEvalContext, depth: int) -> Any:
    """Evaluate 2-argument `map(...)` over lambdas or `chr`/`ord` builtins."""
    func_node, iter_node = n.args[0], n.args[1]
    iter_val = _eval_ast_node(iter_node, ctx, depth + 1)
    if iter_val is None:
        return None
    if isinstance(func_node, ast.Lambda):
        return _eval_map_lambda_call(func_node, iter_val, ctx, depth)
    if isinstance(func_node, ast.Name):
        try:
            if func_node.id == "chr":
                return "".join(chr(x) for idx, x in enumerate(iter_val) if idx < 1000)
            if func_node.id == "ord":
                return [ord(x) for idx, x in enumerate(iter_val) if idx < 1000]
        except Exception:
            return None
    return None


def _eval_call_node(n: ast.Call, ctx: _AstEvalContext, depth: int) -> Any:
    """Evaluate safe `ast.Call` patterns (`getattr`, attribute calls, builtins, `map`)."""
    func_val = _eval_ast_node(n.func, ctx, depth + 1)
    if func_val is getattr and len(n.args) == 2:
        obj = _eval_ast_node(n.args[0], ctx, depth + 1)
        attr = _eval_ast_node(n.args[1], ctx, depth + 1)
        if obj is not None and attr is not None:
            try:
                return getattr(obj, attr)
            except Exception:
                pass
    if isinstance(n.func, ast.Attribute):
        return _eval_attr_call(n, n.func, ctx, depth)
    if isinstance(n.func, ast.Name):
        if n.func.id == "map" and len(n.args) == 2:
            return _eval_map_call(n, ctx, depth)
        return _eval_simple_builtin_call(n.func.id, n.args, ctx, depth)
    return None


def _eval_comp_node(n: ast.ListComp | ast.GeneratorExp, ctx: _AstEvalContext, depth: int) -> Any:
    """Evaluate single-generator list comprehensions and generator expressions."""
    if len(n.generators) != 1 or not isinstance(n.generators[0].target, ast.Name):
        return None
    gen = n.generators[0]
    iter_val = _eval_ast_node(gen.iter, ctx, depth + 1)
    if iter_val is None or not isinstance(gen.target, ast.Name):
        return None
    target_name = gen.target.id
    results: list[Any] = []
    old_val = ctx.local_vars.get(target_name)
    try:
        for count, item in enumerate(iter_val, start=1):
            if count > 1000:
                break
            ctx.local_vars[target_name] = item
            if any(
                (fv := _eval_ast_node(flt, ctx, depth + 1)) is not None and not fv
                for flt in gen.ifs
            ):
                continue
            res = _eval_ast_node(n.elt, ctx, depth + 1)
            if res is not None:
                results.append(res)
        return results
    finally:
        if old_val is not None:
            ctx.local_vars[target_name] = old_val
        else:
            ctx.local_vars.pop(target_name, None)


def _eval_joined_str_node(n: ast.JoinedStr, ctx: _AstEvalContext, depth: int) -> str | None:
    """Evaluate f-string (`JoinedStr`) nodes when all interpolated parts resolve."""
    parts: list[str] = []
    for val_node in n.values:
        part = _eval_ast_node(val_node, ctx, depth + 1)
        if part is None:
            return None
        parts.append(str(part))
    return "".join(parts)


def _eval_ast_node(n: ast.AST | None, ctx: _AstEvalContext, depth: int = 0) -> Any:
    """Dispatch single AST node evaluation using a shared `_AstEvalContext`."""
    if n is None or depth > ctx.max_depth:
        return None
    if isinstance(n, ast.Constant):
        return n.value
    if isinstance(n, ast.Name):
        return _eval_name_node(n, ctx)
    if isinstance(n, ast.Assign):
        return _eval_assign_node(n, ctx, depth)
    if isinstance(n, ast.Subscript):
        return _eval_subscript_node(n, ctx, depth)
    if isinstance(n, ast.Attribute):
        return _eval_attribute_node(n, ctx, depth)
    if isinstance(n, (ast.BinOp, ast.UnaryOp)):
        return _eval_binop_or_unary_node(n, ctx, depth)
    if isinstance(n, ast.Call):
        return _eval_call_node(n, ctx, depth)
    if isinstance(n, ast.List):
        elts = [_eval_ast_node(elt, ctx, depth + 1) for elt in n.elts]
        return elts if all(v is not None for v in elts) else None
    if isinstance(n, ast.Tuple):
        elts = [_eval_ast_node(elt, ctx, depth + 1) for elt in n.elts]
        return tuple(elts) if all(v is not None for v in elts) else None
    if isinstance(n, (ast.ListComp, ast.GeneratorExp)):
        return _eval_comp_node(n, ctx, depth)
    if isinstance(n, ast.JoinedStr):
        return _eval_joined_str_node(n, ctx, depth)
    if isinstance(n, ast.FormattedValue):
        return _eval_ast_node(n.value, ctx, depth + 1)
    return None


def _record_ast_val(val: Any, strs: list[str], bytes_list: list[bytes]) -> None:
    """Append evaluated AST str/bytes/byte-sequence values to collection buffers."""
    if isinstance(val, str):
        strs.append(val)
    elif isinstance(val, bytes):
        bytes_list.append(val)
    elif isinstance(val, int) and 0 <= val <= 255:
        bytes_list.append(bytes([val]))
    elif isinstance(val, (list, tuple)):
        if all(isinstance(x, int) and 0 <= x <= 255 for x in val):
            bytes_list.append(bytes(val))
        for x in val:
            if isinstance(x, str):
                strs.append(x)
            elif isinstance(x, bytes):
                bytes_list.append(x)


def _visit_ast_node(
    n: ast.AST,
    ctx: _AstEvalContext,
    strs: list[str],
    bytes_list: list[bytes],
    depth: int = 0,
) -> None:
    """Walk AST tree recursively up to `ctx.max_depth` collecting resolved values."""
    if depth > ctx.max_depth:
        return
    val = _eval_ast_node(n, ctx, depth)
    if val is not None:
        _record_ast_val(val, strs, bytes_list)
    for child in ast.iter_child_nodes(n):
        _visit_ast_node(child, ctx, strs, bytes_list, depth + 1)


def _scan_ast_nodes(
    node: ast.AST,
    target_env: dict[str, str] | None = None,
    sys_argv_mock: list[str] | None = None,
) -> tuple[list[str], list[bytes]]:
    """Partially evaluate Python AST subtrees to surface obfuscated strings and bytes."""
    strs: list[str] = []
    bytes_list: list[bytes] = []
    ctx = _AstEvalContext(target_env=target_env, sys_argv_mock=sys_argv_mock)
    _visit_ast_node(node, ctx, strs, bytes_list)
    return strs, bytes_list
