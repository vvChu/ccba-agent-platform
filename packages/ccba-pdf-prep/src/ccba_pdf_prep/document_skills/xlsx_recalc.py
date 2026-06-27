import os
import sys
import subprocess
import platform
from pathlib import Path
from openpyxl import load_workbook


def setup_libreoffice_macro():
    """Setup LibreOffice macro for recalculation if not already configured"""
    if platform.system() == 'Darwin':
        macro_dir = os.path.expanduser('~/Library/Application Support/LibreOffice/4/user/basic/Standard')
    elif platform.system() == 'Windows':
        macro_dir = os.path.expandvars('%APPDATA%/LibreOffice/4/user/basic/Standard')
    else:
        macro_dir = os.path.expanduser('~/.config/libreoffice/4/user/basic/Standard')
    
    macro_file = os.path.join(macro_dir, 'Module1.xba')
    
    if os.path.exists(macro_file):
        try:
            with open(macro_file, 'r', encoding='utf-8') as f:
                if 'RecalculateAndSave' in f.read():
                    return True
        except Exception:
            pass
            
    try:
        os.makedirs(macro_dir, exist_ok=True)
    except Exception:
        return False
    
    macro_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">
    Sub RecalculateAndSave()
      ThisComponent.calculateAll()
      ThisComponent.store()
      ThisComponent.close(True)
    End Sub
</script:module>'''
    
    try:
        with open(macro_file, 'w', encoding='utf-8') as f:
            f.write(macro_content)
        return True
    except Exception:
        return False


def recalc_xlsx(filename: str, timeout: int = 30) -> dict:
    """
    Recalculate formulas in Excel file using LibreOffice or fall back to openpyxl.
    """
    file_path = Path(filename)
    if not file_path.exists():
        return {'error': f'File {filename} does not exist'}
        
    abs_path = str(file_path.absolute())
    
    # Try LibreOffice first
    if setup_libreoffice_macro():
        soffice_cmd = "soffice"
        if platform.system() == "Windows":
            # Common paths for LibreOffice on Windows
            win_paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
            ]
            for p in win_paths:
                if os.path.exists(p):
                    soffice_cmd = p
                    break
                    
        try:
            cmd = [
                soffice_cmd, '--headless', '--norestore',
                'vnd.sun.star.script:Standard.Module1.RecalculateAndSave?language=Basic&location=application',
                abs_path
            ]
            res = subprocess.run(cmd, capture_output=True, timeout=timeout)
            if res.returncode == 0:
                return {'success': True, 'method': 'LibreOffice'}
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
            
    # Fallback to openpyxl
    try:
        wb = load_workbook(filename, data_only=False)
        wb.save(filename)
        return {'success': True, 'method': 'openpyxl (Save-back only)'}
    except Exception as e:
        return {'error': f'Failed recalculation: {e}'}
