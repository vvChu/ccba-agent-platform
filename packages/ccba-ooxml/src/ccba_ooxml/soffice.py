"""LibreOffice (soffice) runner and environment helper.

Provides helper functions for running LibreOffice (soffice) in headless mode
with cross-platform socket shim handling.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def get_soffice_env() -> dict[str, str]:
    """Get environment dictionary for running soffice subprocess safely."""
    env = os.environ.copy()
    env["SAL_USE_VCLPLUGIN"] = "svp"

    if _needs_shim():
        shim = _ensure_shim()
        env["LD_PRELOAD"] = str(shim)

    return env


def find_soffice_bin() -> str | None:
    """Find the path to soffice executable on the system."""
    soffice_bin = shutil.which("soffice")
    if soffice_bin:
        return soffice_bin

    # Windows common fallbacks
    fallbacks = [
        Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
        Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
    ]
    for fb in fallbacks:
        if fb.exists():
            return str(fb)
    return None


def run_soffice(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[Any]:
    """Run soffice command line with configured environment.

    Args:
        args: List of command-line arguments to pass to soffice.
        **kwargs: Additional keyword arguments passed to subprocess.run.

    Returns:
        subprocess.CompletedProcess instance.

    Raises:
        FileNotFoundError: If soffice executable is not found.
    """
    soffice_bin = find_soffice_bin()
    if not soffice_bin:
        raise FileNotFoundError(
            "LibreOffice (soffice) not found on PATH or default installation folders. "
            "Please install LibreOffice from https://www.libreoffice.org/ to enable conversion features."
        )
    env = get_soffice_env()
    # Merge custom env if passed in kwargs
    if "env" in kwargs:
        merged_env = env.copy()
        merged_env.update(kwargs.pop("env"))
        env = merged_env
    return subprocess.run([soffice_bin, *args], env=env, **kwargs)


_SHIM_SO = Path(tempfile.gettempdir()) / "lo_socket_shim.so"


def _needs_shim() -> bool:
    """Check if AF_UNIX socket creation is blocked (e.g. sandboxed environment)."""
    if os.name == "nt":
        return False
    af_unix = getattr(socket, "AF_UNIX", None)
    if af_unix is None:
        return False
    try:
        s = socket.socket(af_unix, socket.SOCK_STREAM)
        s.close()
        return False
    except OSError:
        return True


def _ensure_shim() -> Path:
    """Compile and return LD_PRELOAD socket shim for blocked environments."""
    if _SHIM_SO.exists():
        return _SHIM_SO

    src = Path(tempfile.gettempdir()) / "lo_socket_shim.c"
    src.write_text(_SHIM_SOURCE, encoding="utf-8")
    try:
        subprocess.run(
            ["gcc", "-shared", "-fPIC", "-o", str(_SHIM_SO), str(src), "-ldl"],
            check=True,
            capture_output=True,
        )
    finally:
        if src.exists():
            src.unlink()
    return _SHIM_SO


_SHIM_SOURCE = r"""
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <unistd.h>

static int (*real_socket)(int, int, int);
static int (*real_socketpair)(int, int, int, int[2]);
static int (*real_listen)(int, int);
static int (*real_accept)(int, struct sockaddr *, socklen_t *);
static int (*real_close)(int);
static int (*real_read)(int, void *, size_t);

static int is_shimmed[1024];
static int peer_of[1024];
static int wake_r[1024];
static int wake_w[1024];
static int listener_fd = -1;

__attribute__((constructor))
static void init(void) {
    real_socket     = dlsym(RTLD_NEXT, "socket");
    real_socketpair = dlsym(RTLD_NEXT, "socketpair");
    real_listen     = dlsym(RTLD_NEXT, "listen");
    real_accept     = dlsym(RTLD_NEXT, "accept");
    real_close      = dlsym(RTLD_NEXT, "close");
    real_read       = dlsym(RTLD_NEXT, "read");
    for (int i = 0; i < 1024; i++) {
        peer_of[i] = -1;
        wake_r[i]  = -1;
        wake_w[i]  = -1;
    }
}

int socket(int domain, int type, int protocol) {
    if (domain == AF_UNIX) {
        int fd = real_socket(domain, type, protocol);
        if (fd >= 0) return fd;
        int sv[2];
        if (real_socketpair(domain, type, protocol, sv) == 0) {
            if (sv[0] >= 0 && sv[0] < 1024) {
                is_shimmed[sv[0]] = 1;
                peer_of[sv[0]]    = sv[1];
                int wp[2];
                if (pipe(wp) == 0) {
                    wake_r[sv[0]] = wp[0];
                    wake_w[sv[0]] = wp[1];
                }
            }
            return sv[0];
        }
        errno = EPERM;
        return -1;
    }
    return real_socket(domain, type, protocol);
}

int listen(int sockfd, int backlog) {
    if (sockfd >= 0 && sockfd < 1024 && is_shimmed[sockfd]) {
        listener_fd = sockfd;
        return 0;
    }
    return real_listen(sockfd, backlog);
}

int accept(int sockfd, struct sockaddr *addr, socklen_t *addrlen) {
    if (sockfd >= 0 && sockfd < 1024 && is_shimmed[sockfd]) {
        if (wake_r[sockfd] >= 0) {
            char buf;
            real_read(wake_r[sockfd], &buf, 1);
        }
        errno = ECONNABORTED;
        return -1;
    }
    return real_accept(sockfd, addr, addrlen);
}

int close(int fd) {
    if (fd >= 0 && fd < 1024 && is_shimmed[fd]) {
        int was_listener = (fd == listener_fd);
        is_shimmed[fd] = 0;

        if (wake_w[fd] >= 0) {
            char c = 0;
            write(wake_w[fd], &c, 1);
            real_close(wake_w[fd]);
            wake_w[fd] = -1;
        }
        if (wake_r[fd] >= 0) { real_close(wake_r[fd]); wake_r[fd]  = -1; }
        if (peer_of[fd] >= 0) { real_close(peer_of[fd]); peer_of[fd] = -1; }

        if (was_listener)
            _exit(0);
    }
    return real_close(fd);
}
"""


def validate_document(doc_path: str | Path) -> bool:
    """Validate document by converting to HTML with soffice.

    Args:
        doc_path: Path to .docx, .pptx, or .xlsx file.

    Returns:
        bool: True if validation succeeds or soffice is not found (graceful fallback).
    """
    import sys

    doc_path = Path(doc_path)
    if not doc_path.exists() or not doc_path.is_file():
        print(f"Validation error: '{doc_path}' is not a valid file.", file=sys.stderr)
        return False

    # Determine the correct filter based on file extension
    match doc_path.suffix.lower():
        case ".docx":
            filter_name = "html:HTML"
        case ".pptx":
            filter_name = "html:impress_html_Export"
        case ".xlsx":
            filter_name = "html:HTML (StarCalc)"
        case _:
            print(
                f"Validation error: Unsupported file type '{doc_path.suffix}'. Supported: .docx, .pptx, .xlsx",
                file=sys.stderr,
            )
            return False

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            result = run_soffice(
                [
                    "--headless",
                    "--convert-to",
                    filter_name,
                    "--outdir",
                    temp_dir,
                    str(doc_path),
                ],
                capture_output=True,
                timeout=10,
                text=True,
            )
            if not (Path(temp_dir) / f"{doc_path.stem}.html").exists():
                error_msg = result.stderr.strip() or "Document validation failed"
                print(f"Validation error: {error_msg}", file=sys.stderr)
                return False
            return True
        except FileNotFoundError:
            print("Warning: soffice not found. Skipping validation.", file=sys.stderr)
            return True
        except subprocess.TimeoutExpired:
            print("Validation error: Timeout during conversion", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Validation error: {e}", file=sys.stderr)
            return False


__all__ = ["find_soffice_bin", "get_soffice_env", "run_soffice", "validate_document"]
