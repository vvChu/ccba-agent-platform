"""AIVisionFormulaHarvester — Boc tach cong thuc toan hoc tu anh sang KaTeX (ADR 0031).

Ho tro hai nguon:
  - DOCX: anh nhung trong <v:imagedata> / <w:drawing> (word/media/imageX.png)
  - PDF : anh embedded duoc crop bang PyMuPDF / fitz

Pipeline xu ly:
  1. Heuristic phan loai Formula vs Diagram (height <= 60pt AND width <= 380pt AND context)
  2. SHA-256 cache gate (.md/cache/formula_vision/<sha256>.json)
  3. Goi AI Gateway (gemini-3.7-flash) voi max_tokens=1024 va few-shot prompt
  4. Validation + Retry (toi da 2 lan)
  5. Fallback placeholder neu Gateway offline hoac retry that bai
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import tempfile
import zipfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_FORMULA_CONTEXT_KEYWORDS = (
    "theo cong thuc",
    "theo c\u00f4ng th\u1ee9c",
    "Trong \u0111\u00f3:",
    "\u0111\u01b0\u1ee3c x\u00e1c \u0111\u1ecbnh",
    "\u0111\u01b0\u1ee3c t\u00ednh theo",
    "t\u00ednh theo c\u00f4ng th\u1ee9c",
    "x\u00e1c \u0111\u1ecbnh theo",
    "theo bi\u1ec3u th\u1ee9c",
)

_VISION_PROMPT = (
    "Chuy\u1ec3n \u0111\u1ed5i h\u00ecnh \u1ea3nh c\u00f4ng th\u1ee9c to\u00e1n h\u1ecdc k\u1ef9 thu\u1eadt n\u00e0y sang m\u00e3 LaTeX KaTeX ch\u00ednh x\u00e1c 100%.\n\n"
    "Quy t\u1eafc b\u1eaft bu\u1ed9c:\n"
    "- B\u1ea3o t\u1ed3n nguy\u00ean v\u1eb9n: k\u00fd t\u1ef1 Hy L\u1ea1p (\\u03c4\u2192\\\\tau, \\u03bc\u2192\\\\mu, \\u03b6\u2192\\\\zeta, \\u03b3\u2192\\\\gamma), "
    "ph\u00e2n s\u1ed1 (\\\\frac{}{}), c\u0103n b\u1eadc hai (\\\\sqrt{}), ch\u1ec9 s\u1ed1 d\u01b0\u1edbi (_{...}), s\u1ed1 m\u0169 (^{...}).\n"
    "- \u0110\u01a1n v\u1ecb \u0111o l\u01b0\u1eddng b\u1ecdc trong \\\\text{...} (v\u00ed d\u1ee5: \\\\text{m/s}, \\\\text{MPa}).\n"
    "- Ch\u1ec9 s\u1ed1 d\u01b0\u1edbi ti\u1ebfng Vi\u1ec7t b\u1ecdc trong \\\\text{...} (v\u00ed d\u1ee5: P_{\\\\text{D\\u0110}1}, P_{\\\\text{CB2}}).\n"
    "- Ch\u1ec9 tr\u1ea3 v\u1ec1 DUY NH\u1ea4T 1 d\u00f2ng b\u1eaft \u0111\u1ea7u b\u1eb1ng $$ v\u00e0 k\u1ebft th\u00fac b\u1eb1ng $$, KH\u00d4NG c\u00f3 b\u1ea5t k\u1ef3 v\u0103n b\u1ea3n n\u00e0o kh\u00e1c.\n\n"
    "V\u00ed d\u1ee5 \u0111\u1ea7u ra h\u1ee3p l\u1ec7:\n"
    "$$q_1 = 10 \\\\cdot K \\\\cdot \\\\sqrt{P}$$\n"
    "$$N = \\\\frac{V \\\\cdot a}{q \\\\cdot K \\\\cdot \\\\tau}$$"
)

_VISION_PROMPT_STRICT = (
    "Convert this math formula image to LaTeX. "
    "Return ONLY 1 line in the format $$FORMULA$$. "
    "No other text allowed before or after the $$ delimiters."
)


def is_formula_image(height_pt: float, width_pt: float, surrounding_text: str) -> bool:
    """Phan loai anh nhung: cong thuc toan hoc hay so do ky thuat.

    Args:
        height_pt: Chieu cao anh tinh bang point (pt).
        width_pt: Chieu rong anh tinh bang point (pt).
        surrounding_text: Van ban xung quanh doan chua anh.

    Returns:
        True neu anh la cong thuc toan hoc; False neu la so do/hinh ve ky thuat.
    """
    # Fix 1: Heuristic kep — kich thuoc nho VA khong phai hinh toan trang
    is_small = height_pt <= 60.0 and width_pt <= 380.0
    has_context = any(kw in surrounding_text for kw in _FORMULA_CONTEXT_KEYWORDS)
    return is_small and has_context


def _compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_cache(cache_dir: Path, sha256: str) -> str | None:
    cache_file = cache_dir / f"{sha256}.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8")).get("katex")
        except Exception:
            return None
    return None


def _write_cache(cache_dir: Path, sha256: str, katex: str) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{sha256}.json"
    cache_file.write_text(
        json.dumps({"sha256": sha256, "katex": katex}, ensure_ascii=False),
        encoding="utf-8",
    )


def _validate_katex(result: str) -> bool:
    """Kiem tra output co dung format $$...$$ khong."""
    s = result.strip()
    return (
        s.startswith("$$")
        and s.endswith("$$")
        and len(s) > 4
        and "\n\n" not in s
    )


def _clean_and_extract_katex(raw: str) -> str | None:
    """Trich xuat va lam sach cong thuc KaTeX $$...$$ tu chuoi AI raw."""
    if not raw:
        return None
    s = raw.strip()

    # 1. Tim block $$...$$ hoan chinh (bao gom ca truong hop AI kem loi thoai)
    m = re.search(r"\$\$(.+?)\$\$", s, re.DOTALL)
    if m:
        content = m.group(1).strip()
        if content and len(content) > 1 and "\n\n" not in content:
            return f"$${content}$$"

    # 2. Truong hop bat dau bang $$ nhung bi thieu $$ o cuoi do cat token
    if s.startswith("$$") and not s.endswith("$$"):
        content = s[2:].strip()
        content = re.sub(r"[`'\"]+$", "", content).strip()
        if content and len(content) > 1 and "\n\n" not in content:
            return f"$${content}$$"

    # 3. Truong hop dung inline $...$
    m_inline = re.search(r"(?<!\$)\$([^\$\n]+)\$(?!\$)", s)
    if m_inline:
        content = m_inline.group(1).strip()
        if content and len(content) > 1:
            return f"$${content}$$"

    # 4. Truong hop chuoi toan hoc thuan khong chua dau do
    if re.match(r"^[A-Za-z0-9_\\\{\}\(\)\+\-\*\/\=\,\.\s\^\_]+$", s) and ("=" in s or "\\" in s or "^" in s or "_" in s):
        if "\n\n" not in s and len(s) > 2:
            return f"$${s}$$"

    return None


def _call_vision_api(img_bytes: bytes, prompt: str) -> str:
    """Goi AI Gateway Vision API de nhan dien cong thuc toan hoc.

    Args:
        img_bytes: Binary cua anh cong thuc (PNG/JPEG).
        prompt: Prompt huong dan model.

    Returns:
        Chuoi tra ve tu model (chua validate).
    """
    from ccba_ai import ai, ModelArchetype

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(img_bytes)
        tmp_path = Path(tmp.name)

    try:
        b64_img = ai.encode_image(str(tmp_path), max_pixels=512, quality=95)
    finally:
        try:
            tmp_path.unlink()
        except Exception:
            pass

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}},
            ],
        }
    ]

    # Fix 2: max_tokens=1024 de tranh truncation
    return ai.chat_multi(
        messages,
        model=ModelArchetype.STANDARD,
        max_tokens=1024,
        temperature=0.0,
        timeout=60.0,
    )


def extract_latex_from_image(
    img_bytes: bytes,
    cache_dir: Path | None = None,
    skip_vision: bool = False,
) -> str:
    """Trich xuat cong thuc toan hoc tu anh sang ma LaTeX KaTeX chuan.

    Args:
        img_bytes: Binary cua anh cong thuc (PNG/JPEG).
        cache_dir: Thu muc cache SHA-256. Neu None, khong dung cache.
        skip_vision: Neu True, bo qua AI call va tra ve placeholder ngay.

    Returns:
        Chuoi KaTeX dang $$...$$, hoac placeholder neu that bai.
    """
    sha256 = _compute_sha256(img_bytes)

    # Buoc 1: Cache gate
    if cache_dir is not None:
        cached = _read_cache(cache_dir, sha256)
        if cached is not None:
            logger.debug("Formula cache hit: %s", sha256[:8])
            return cached

    # Buoc 2: Skip flag (offline / CI/CD)
    if skip_vision:
        return f"<!-- FORMULA_PLACEHOLDER: {sha256[:8]} -->"

    # Buoc 3: Goi AI Vision voi retry + regex post-processor
    prompts = [_VISION_PROMPT, _VISION_PROMPT_STRICT]
    for attempt, prompt in enumerate(prompts):
        try:
            raw = _call_vision_api(img_bytes, prompt)
            cleaned = _clean_and_extract_katex(raw)
            if cleaned and _validate_katex(cleaned):
                if cache_dir is not None:
                    _write_cache(cache_dir, sha256, cleaned)
                logger.info("Formula extracted (attempt %d): %s", attempt + 1, cleaned[:60])
                return cleaned
            logger.warning(
                "Vision attempt %d invalid format (sha256=%s): %s",
                attempt + 1, sha256[:8], raw.strip()[:80],
            )
        except Exception as exc:
            logger.warning("Vision attempt %d error (sha256=%s): %s", attempt + 1, sha256[:8], exc)

        if attempt < len(prompts) - 1:
            time.sleep(1.0)

    placeholder = f"<!-- FORMULA_IMAGE_PLACEHOLDER: {sha256[:8]} -->"
    logger.error("Formula extraction failed after %d attempts: %s", len(prompts), sha256[:8])
    return placeholder


def _parse_pt(style_str: str, dimension: str) -> float:
    m = re.search(rf"{dimension}:([\d.]+)pt", style_str)
    return float(m.group(1)) if m else 9999.0


def _get_surrounding_text(paragraphs: list[Any], center: int, window: int = 3) -> str:
    parts: list[str] = []
    for idx in range(max(0, center - window), min(len(paragraphs), center + window + 1)):
        txt = "".join(el.text or "" for el in paragraphs[idx].iter() if el.tag.endswith("}t"))
        parts.append(txt.strip())
    return " ".join(parts)


def harvest_docx_formula_images(
    docx_path: Path,
    cache_dir: Path | None = None,
    skip_vision: bool = False,
) -> dict[str, str]:
    """Thu hoach toan bo anh cong thuc tu tep DOCX va chuyen doi sang KaTeX.

    Args:
        docx_path: Duong dan den tep DOCX.
        cache_dir: Thu muc SHA-256 cache.
        skip_vision: Bo qua AI call, tra ve placeholder.

    Returns:
        Dict anh xa r:id -> KaTeX string.
    """
    import xml.etree.ElementTree as ET

    ns_v = "urn:schemas-microsoft-com:vml"
    ns_r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    ns_a = "http://schemas.openxmlformats.org/drawingml/2006/main"
    ns_wp = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"

    with zipfile.ZipFile(docx_path, "r") as z:
        rels_xml = z.read("word/_rels/document.xml.rels")
        rels_tree = ET.fromstring(rels_xml)
        r_map: dict[str, str] = {}
        for rel in rels_tree:
            rid = rel.attrib.get("Id")
            target = rel.attrib.get("Target", "")
            if rid and "media/" in target:
                r_map[rid] = "word/" + target.replace("../", "")

        media_files = set(f for f in z.namelist() if f.startswith("word/media/"))
        doc_xml = z.read("word/document.xml")
        doc_tree = ET.fromstring(doc_xml)
        paragraphs = doc_tree.findall(
            ".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"
        )

        rid_to_katex: dict[str, str] = {}

        for p_idx, para in enumerate(paragraphs):
            # 1. Check legacy VML shapes (v:shape)
            for shape in para.findall(f".//{{{ns_v}}}shape"):
                img_el = shape.find(f"{{{ns_v}}}imagedata")
                if img_el is None:
                    continue
                rid = img_el.attrib.get(f"{{{ns_r}}}id")
                if not rid or rid not in r_map:
                    continue

                style_str = shape.attrib.get("style", "")
                height_pt = _parse_pt(style_str, "height")
                width_pt = _parse_pt(style_str, "width")
                surrounding = _get_surrounding_text(paragraphs, p_idx, window=3)

                if not is_formula_image(height_pt, width_pt, surrounding):
                    rid_to_katex[rid] = f"<!-- DIAGRAM: {r_map[rid]} -->"
                    continue

                media_path = r_map[rid]
                if media_path not in media_files:
                    continue

                img_bytes = z.read(media_path)
                katex = extract_latex_from_image(img_bytes, cache_dir=cache_dir, skip_vision=skip_vision)
                rid_to_katex[rid] = katex

            # 2. Check modern DrawingML (w:drawing)
            for drawing in para.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing"):
                blip = drawing.find(f".//{{{ns_a}}}blip")
                if blip is None:
                    continue
                rid = blip.attrib.get(f"{{{ns_r}}}embed")
                if not rid or rid not in r_map or rid in rid_to_katex:
                    continue

                extent = drawing.find(f".//{{{ns_wp}}}extent")
                height_pt = 9999.0
                width_pt = 9999.0
                if extent is not None:
                    cx = float(extent.attrib.get("cx", 0))
                    cy = float(extent.attrib.get("cy", 0))
                    width_pt = cx / 12700.0
                    height_pt = cy / 12700.0

                surrounding = _get_surrounding_text(paragraphs, p_idx, window=3)

                if not is_formula_image(height_pt, width_pt, surrounding):
                    rid_to_katex[rid] = f"<!-- DIAGRAM: {r_map[rid]} -->"
                    continue

                media_path = r_map[rid]
                if media_path not in media_files:
                    continue

                img_bytes = z.read(media_path)
                katex = extract_latex_from_image(img_bytes, cache_dir=cache_dir, skip_vision=skip_vision)
                rid_to_katex[rid] = katex

    return rid_to_katex


def harvest_pdf_formula_images(
    pdf_path: Path,
    cache_dir: Path | None = None,
    skip_vision: bool = False,
) -> list[dict[str, Any]]:
    """Thu hoach anh cong thuc tu tep PDF bang PyMuPDF.

    Args:
        pdf_path: Duong dan den tep PDF.
        cache_dir: Thu muc SHA-256 cache.
        skip_vision: Bo qua AI call.

    Returns:
        List cac dict {page_num, xref, width_px, height_px, katex}.
    """
    try:
        import fitz
    except ImportError:
        logger.warning("PyMuPDF khong duoc cai dat. Bo qua PDF formula harvesting.")
        return []

    results: list[dict[str, Any]] = []
    doc = fitz.open(str(pdf_path))
    try:
        for pg_idx in range(doc.page_count):
            page = doc[pg_idx]
            for img_meta in page.get_images():
                xref, w_px, h_px = img_meta[0], img_meta[2], img_meta[3]
                if h_px > 80 or w_px > 600:
                    results.append({"page_num": pg_idx + 1, "xref": xref,
                                    "width_px": w_px, "height_px": h_px,
                                    "katex": f"<!-- DIAGRAM_PDF: page={pg_idx+1} xref={xref} -->"})
                    continue
                try:
                    img_bytes = doc.extract_image(xref)["image"]
                except Exception as exc:
                    logger.warning("Extract image xref=%d failed: %s", xref, exc)
                    continue
                katex = extract_latex_from_image(img_bytes, cache_dir=cache_dir, skip_vision=skip_vision)
                results.append({"page_num": pg_idx + 1, "xref": xref,
                                 "width_px": w_px, "height_px": h_px, "katex": katex})
    finally:
        doc.close()
    return results
