"""Excel spreadsheet formula recalculation utilities for OOXML files.

Supports headless recalculation via LibreOffice Basic Macro with automatic
fallback to openpyxl for save-back.
"""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Any

LIBREOFFICE_MACRO_SNIPPET = """    Sub RecalculateAndSave()
      ThisComponent.calculateAll()
      ThisComponent.store()
      ThisComponent.close(True)
    End Sub"""

LIBREOFFICE_MODULE_TEMPLATE = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">
{LIBREOFFICE_MACRO_SNIPPET}
</script:module>"""


def setup_libreoffice_macro() -> bool:
    """Setup LibreOffice macro for recalculation without destroying existing macros.

    Uses safe injection: if Module1.xba exists, injects RecalculateAndSave
    before the closing </script:module> tag rather than overwriting.

    Returns:
        bool: True if macro is ready, False otherwise.
    """
    system = platform.system()
    if system == "Darwin":
        macro_dir = os.path.expanduser(
            "~/Library/Application Support/LibreOffice/4/user/basic/Standard"
        )
    elif system == "Windows":
        app_data = os.getenv("APPDATA")
        if app_data:
            macro_dir = os.path.join(app_data, "LibreOffice", "4", "user", "basic", "Standard")
        else:
            macro_dir = str(Path.home() / "AppData" / "Roaming" / "LibreOffice" / "4" / "user" / "basic" / "Standard")
    else:
        macro_dir = os.path.expanduser("~/.config/libreoffice/4/user/basic/Standard")

    macro_file = os.path.join(macro_dir, "Module1.xba")

    if os.path.exists(macro_file):
        try:
            with open(macro_file, encoding="utf-8") as f:
                content = f.read()
            if "RecalculateAndSave" in content:
                return True

            # Safe injection: insert snippet before </script:module>
            if "</script:module>" in content:
                injected = content.replace(
                    "</script:module>",
                    f"\n{LIBREOFFICE_MACRO_SNIPPET}\n</script:module>",
                )
                with open(macro_file, "w", encoding="utf-8") as f:
                    f.write(injected)
                return True
        except Exception as e:
            print(f"[ccba_ooxml.calc] Warning reading/injecting macro: {e}")
            return False

    try:
        os.makedirs(macro_dir, exist_ok=True)
        with open(macro_file, "w", encoding="utf-8") as f:
            f.write(LIBREOFFICE_MODULE_TEMPLATE)
        return True
    except Exception as e:
        print(f"[ccba_ooxml.calc] Warning creating macro directory/file: {e}")
        return False


def recalc_xlsx(filename: str | Path, timeout: int = 30) -> dict[str, Any]:
    """Recalculate formulas in Excel file using LibreOffice or fall back to openpyxl.

    Args:
        filename: Path to the .xlsx spreadsheet file.
        timeout: Maximum seconds to wait for LibreOffice subprocess.

    Returns:
        Dictionary containing status and method used, or error message.
    """
    file_path = Path(filename)
    if not file_path.exists():
        return {"error": f"File {filename} does not exist"}

    abs_path = str(file_path.resolve())

    # Try LibreOffice first
    libreoffice_setup_ok = False
    try:
        libreoffice_setup_ok = setup_libreoffice_macro()
    except Exception as e:
        print(f"[ccba_ooxml.calc] Warning: Failed to set up LibreOffice macro: {e}")

    if libreoffice_setup_ok:
        soffice_cmd = "soffice"
        if platform.system() == "Windows":
            win_paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ]
            for p in win_paths:
                if os.path.exists(p):
                    soffice_cmd = p
                    break

        try:
            cmd = [
                soffice_cmd,
                "--headless",
                "--norestore",
                "vnd.sun.star.script:Standard.Module1.RecalculateAndSave?language=Basic&location=application",
                abs_path,
            ]
            res = subprocess.run(cmd, capture_output=True, timeout=timeout)
            if res.returncode == 0:
                return {"success": True, "method": "LibreOffice"}
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    # Fallback to openpyxl (Lazy Import to prevent crash if openpyxl not installed)
    try:
        from openpyxl import load_workbook

        wb = load_workbook(filename, data_only=False)
        wb.save(filename)
        return {"success": True, "method": "openpyxl (Save-back only)"}
    except ImportError:
        return {
            "error": "Failed recalculation: Neither LibreOffice nor openpyxl is available."
        }
    except Exception as e:
        return {"error": f"Failed recalculation: {e}"}
