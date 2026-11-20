"""Subprocess and multi-threading runtime wrappers preserving re-entrancy hook contracts."""

from __future__ import annotations

import os
import threading
from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._guard import HarnessGuard

from ._proc_guard_checks import (
    _check_subprocess_call,
    _is_copied_python_executable,
    _is_python_cmd_name,
)
from ._proc_shell_parser import (
    _extract_exec_path,
    _extract_subprocess_parts,
    _normalize_cmd_args,
    _split_command_to_words,
)
from ._state import (
    _HOOK_TOKEN,
    HarnessState,
    _check_in_hook,
    _get_active_guards,
    _Originals,
)


def _inject_child_env(env_dict: Any, guards: list[HarnessGuard]) -> dict[str, str]:
    """Inject PYTHONPATH, HARNESS_ACTIVE, and HARNESS_APPROVED_PATHS into child Python env."""
    new_env = dict(os.environ) if env_dict is None else dict(env_dict)
    temp_dirs = [g._temp_dir for g in guards if hasattr(g, "_temp_dir") and g._temp_dir]
    if not temp_dirs:
        return new_env

    existing_pythonpath = new_env.get("PYTHONPATH", "")
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path_dirs = list(temp_dirs) + [package_root]
    if existing_pythonpath:
        path_dirs.append(existing_pythonpath)
    new_env["PYTHONPATH"] = os.pathsep.join(path_dirs)
    new_env["HARNESS_ACTIVE"] = "1"
    all_approved = [path for g in guards if g.approved_paths for path in g.approved_paths]
    new_env["HARNESS_APPROVED_PATHS"] = os.pathsep.join(all_approved)
    return new_env


def _detect_python_target(name: str, args_tuple: tuple[Any, ...], kwargs: dict[str, Any]) -> bool:
    """Return True if a Popen/os subprocess call targets a Python interpreter binary."""
    exec_path = _extract_exec_path(name, args_tuple, kwargs)
    cmd_args_extracted, _ = _extract_subprocess_parts(name, args_tuple, kwargs)
    target_cmd = ""
    if exec_path is not None:
        target_cmd = str(exec_path)
    elif cmd_args_extracted:
        normalized = _normalize_cmd_args(cmd_args_extracted)
        if normalized:
            target_cmd = normalized[0]
            if isinstance(cmd_args_extracted, (str, bytes)):
                words = _split_command_to_words(target_cmd)
                if words:
                    target_cmd = words[0]

    if target_cmd and (_is_python_cmd_name(target_cmd) or _is_copied_python_executable(target_cmd)):
        return True
    if cmd_args_extracted:
        normalized = _normalize_cmd_args(cmd_args_extracted)
        return any(
            _is_python_cmd_name(arg) or _is_copied_python_executable(arg) for arg in normalized
        )
    return False


def _materialize_cmd_iterator(args_list: list[Any], kwargs: dict[str, Any]) -> None:
    """Materialize an iterator command argument in-place so validation and Popen see identical items."""
    cmd_args = None
    in_kwargs = False
    if args_list:
        cmd_args = args_list[0]
    elif "args" in kwargs:
        cmd_args = kwargs["args"]
        in_kwargs = True
    if (
        cmd_args is not None
        and not isinstance(cmd_args, (str, bytes))
        and hasattr(cmd_args, "__next__")
    ):
        materialized = list(cmd_args)
        if in_kwargs:
            kwargs["args"] = materialized
        elif args_list:
            args_list[0] = materialized


def _wrapped_popen(*args: Any, **kwargs: Any) -> Any:
    """Intercept `subprocess.Popen`, validate command/env, inject child hooks, and restore in_hook."""
    args_list = list(args)
    _materialize_cmd_iterator(args_list, kwargs)
    _check_subprocess_call("Popen", tuple(args_list), kwargs)

    guards = _get_active_guards()
    if guards and _detect_python_target("Popen", tuple(args_list), kwargs):
        if "env" in kwargs:
            kwargs["env"] = _inject_child_env(kwargs["env"], guards)
        elif len(args_list) > 10:
            args_list[10] = _inject_child_env(args_list[10], guards)
        else:
            kwargs["env"] = _inject_child_env(None, guards)

    old_in_hook = getattr(HarnessState.local, "in_hook", None)
    HarnessState.local.__dict__["in_hook"] = _HOOK_TOKEN
    try:
        return _Originals.popen(*args_list, **kwargs)
    finally:
        HarnessState.local.__dict__["in_hook"] = old_in_hook


def _prepare_os_subprocess_call(name: str, args_list: list[Any], kwargs: dict[str, Any]) -> None:
    """Run guard checks and child env injection for `os.system`/`os.spawn*`/`os.exec*`."""
    _check_subprocess_call(name, tuple(args_list), kwargs)
    guards = _get_active_guards()
    if not guards or not _detect_python_target(name, tuple(args_list), kwargs):
        return
    if name.endswith(("e", "e_")) or "env" in kwargs:
        if "env" in kwargs:
            kwargs["env"] = _inject_child_env(kwargs["env"], guards)
        elif args_list:
            args_list[-1] = _inject_child_env(args_list[-1], guards)


def _make_os_wrapper(name: str, original_func: Callable[..., Any]) -> Callable[..., Any]:
    """Build a wrapped OS process-launch function clearing `in_hook = None` in `finally`."""

    @wraps(original_func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if _check_in_hook():
            return original_func(*args, **kwargs)
        args_list = list(args)
        HarnessState.local.__dict__["in_hook"] = _HOOK_TOKEN
        try:
            _prepare_os_subprocess_call(name, args_list, kwargs)
            return original_func(*args_list, **kwargs)
        finally:
            HarnessState.local.__dict__["in_hook"] = None

    return wrapper


def _release_subthread_guards(parent_guards: list[HarnessGuard]) -> None:
    """Decrement subthread refcount and restore global hooks if no guards/threads remain."""
    if not parent_guards:
        return
    with HarnessState.lock:
        HarnessState.active_subthreads_count -= 1
        if (
            HarnessState.active_subthreads_count == 0
            and HarnessState.active_count == 0
            and HarnessState.global_hooks_active
        ):
            from ._engine import HarnessEngine

            HarnessEngine._restore_global_hooks_internal()


def _wrapped_thread_start(self: threading.Thread, *args: Any, **kwargs: Any) -> Any:
    """Propagate active HarnessGuard list into spawned `threading.Thread` workers."""
    parent_guards = list(_get_active_guards())
    if parent_guards:
        with HarnessState.lock:
            HarnessState.active_subthreads_count += 1
    original_run = self.run

    def wrapped_run(*run_args: Any, **run_kwargs: Any) -> Any:
        HarnessState.local.active_guards = list(parent_guards)
        try:
            return original_run(*run_args, **run_kwargs)
        finally:
            _release_subthread_guards(parent_guards)

    self.run = wrapped_run  # type: ignore[method-assign]
    return _Originals.thread_start(self, *args, **kwargs)


def _wrapped_thread_start_new_thread(
    function: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any] | None = None
) -> int:
    """Propagate active HarnessGuard list into `_thread.start_new_thread` workers."""
    parent_guards = list(_get_active_guards())
    if parent_guards:
        with HarnessState.lock:
            HarnessState.active_subthreads_count += 1

    def thread_target_wrapper(*target_args: Any, **target_kwargs: Any) -> Any:
        HarnessState.local.active_guards = list(parent_guards)
        try:
            return function(*target_args, **target_kwargs)
        finally:
            _release_subthread_guards(parent_guards)

    return _Originals.thread_start_new_thread(thread_target_wrapper, args, kwargs or {})


def _wrapped_thread_start_new(
    function: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any] | None = None
) -> int:
    """Propagate active HarnessGuard list into `_thread.start_new` workers."""
    parent_guards = list(_get_active_guards())
    if parent_guards:
        with HarnessState.lock:
            HarnessState.active_subthreads_count += 1

    def thread_target_wrapper(*target_args: Any, **target_kwargs: Any) -> Any:
        HarnessState.local.active_guards = list(parent_guards)
        try:
            return function(*target_args, **target_kwargs)
        finally:
            _release_subthread_guards(parent_guards)

    target_fn = (
        _Originals.thread_start_new
        if _Originals.thread_start_new is not None
        else _Originals.thread_start_new_thread
    )
    return target_fn(thread_target_wrapper, args, kwargs or {})
