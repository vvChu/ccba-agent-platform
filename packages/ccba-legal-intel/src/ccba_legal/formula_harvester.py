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
import zipfile
from pathlib import Path
from typing import Any

from ccba_legal.converters.mtef_parser import decode_ole_mathtype

logger = logging.getLogger(__name__)

_FORMULA_CONTEXT_KEYWORDS = (
    "theo cong thuc",
    "theo c\u00f4ng th\u1ee9c",
    "Trong \u0111\u00f3:",
    "trong \u0111\u00f3:",
    "\u0111\u01b0\u1ee3c x\u00e1c \u0111\u1ecbnh",
    "\u0111\u01b0\u1ee3c t\u00ednh theo",
    "t\u00ednh theo c\u00f4ng th\u1ee9c",
    "x\u00e1c \u0111\u1ecbnh theo",
    "theo bi\u1ec3u th\u1ee9c",
    "bi\u1ec3u th\u1ee9c",
    "ph\u01b0\u01a1ng tr\u00ecnh",
    "h\u1ec7 th\u1ee9c",
    "h\u1ec7 s\u1ed1",
    "t\u1ec9 s\u1ed1",
    "t\u1ef7 s\u1ed1",
    "c\u00e1c c\u00f4ng th\u1ee9c",
    "c\u00f4ng th\u1ee9c sau",
    "\u1ee9ng su\u1ea5t",
    "bi\u1ebfn d\u1ea1ng",
    "quan h\u1ec7",
    "khi \u0111\u00f3",
    "khi",
    "\u0111i\u1ec1u ki\u1ec7n",
)


def is_formula_image(
    height_pt: float,
    width_pt: float,
    surrounding_text: str,
    forward_text: str = "",
) -> bool:
    """Phan loai anh nhung: cong thuc toan hoc hay so do ky thuat.

    Args:
        height_pt: Chieu cao anh tinh bang point (pt).
        width_pt: Chieu rong anh tinh bang point (pt).
        surrounding_text: Van ban xung quanh doan chua anh (truoc va sau).
        forward_text: Van ban ngay sau doan chua anh de kiem tra chu thich hinh.

    Returns:
        True neu anh la cong thuc toan hoc; False neu la so do/hinh ve ky thuat.
    """
    # 1. Inline math symbols (e.g. \ell, \bar{\epsilon}, \bar{b})
    if height_pt <= 35.0 and width_pt <= 120.0:
        return True

    # Check if this is an actual diagram/figure (accompanied by figure caption or CHÚ DẪN immediately following)
    caption_check_text = forward_text if forward_text else surrounding_text
    has_figure_caption = bool(
        re.search(
            r"^(?:Hình|HÌNH)\s+[0-9A-Z]+(?:\.[0-9]+)*\s*[-–—:]", caption_check_text, re.MULTILINE
        )
    )
    has_chu_dan = bool(re.search(r"\b(?:CHÚ\s+DẪN|Chú\s+dẫn)\b", caption_check_text))
    if (has_figure_caption or has_chu_dan) and height_pt > 75.0:
        return False

    has_context = any(kw.lower() in surrounding_text.lower() for kw in _FORMULA_CONTEXT_KEYWORDS)

    # 2. Multi-line stacked formula blocks with mathematical context
    if height_pt <= 320.0 and width_pt <= 650.0 and has_context:
        return True

    # 3. Compact single-line formula without explicit context
    if height_pt <= 75.0 and width_pt <= 450.0:
        return True

    return False


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


_VISION_PROMPT = (
    "Chuyển đổi hình ảnh công thức toán học kỹ thuật này sang mã LaTeX KaTeX chính xác 100%.\n\n"
    "Quy tắc bắt buộc:\n"
    "- BẮT BUỘC giữ lại số hiệu công thức ở góc phải ảnh nếu có dưới dạng \\tag{...} hoặc \\qquad (...) (ví dụ: \\tag{120} hoặc \\qquad (120)).\n"
    "- Bảo tồn nguyên vẹn: ký tự Hy Lạp (\\tau, \\mu, \\zeta, \\gamma, \\varepsilon, \\sigma, \\sigma_{b1}, \\Delta\\sigma), "
    "phân số (\\frac{}{}), căn bậc hai (\\sqrt{}), chỉ số dưới (_{...}), số mũ (^{...}).\n"
    "- Nếu ảnh chứa nhiều dòng công thức hoặc hệ công thức, dùng \\begin{aligned} ... \\end{aligned} hoặc nhiều dòng riêng biệt, và gắn số hiệu \\qquad (...) hoặc \\tag{...} cho từng dòng nếu ảnh có số hiệu riêng cho từng dòng.\n"
    "- Đơn vị đo lường bọc trong \\text{...} (ví dụ: \\text{m/s}, \\text{MPa}).\n"
    "- Chỉ số dưới tiếng Việt bọc trong \\text{...} (ví dụ: P_{\\text{DĐ}1}, P_{\\text{CB2}}).\n"
    "- Chỉ trả về duy nhất khối công thức bắt đầu bằng $$ và kết thúc bằng $$, không có bất kỳ văn bản giải thích nào khác.\n\n"
    "Ví dụ đầu ra hợp lệ:\n"
    "$$q_1 = 10 \\cdot K \\cdot \\sqrt{P} \\tag{1}$$\n"
    "$$\\begin{aligned} \\sigma_b &= E_b \\varepsilon_b \\qquad (8) \\\\ \\sigma_b &= R_b \\qquad (10) \\end{aligned}$$"
)

_VISION_PROMPT_STRICT = (
    "Convert this math formula image to LaTeX. "
    "Return ONLY 1 block in the format $$FORMULA$$. "
    "No other text allowed before or after the $$ delimiters."
)


def _validate_katex(result: str) -> bool:
    """Kiem tra output co dung format $$...$$ va cu phap LaTeX hop le (can bang dau ngoac)."""
    s = result.strip()
    if not (s.startswith("$$") and s.endswith("$$") and len(s) > 4):
        return False
    # 1. Bat buoc can bang dau ngoac nhon {...}
    if s.count("{") != s.count("}"):
        return False
    # 2. Bat buoc can bang cac moi truong \\begin{...} va \\end{...}
    begins = len(re.findall(r"\\begin\{([^}]+)\}", s))
    ends = len(re.findall(r"\\end\{([^}]+)\}", s))
    if begins != ends:
        return False
    return True


def _clean_and_extract_katex(raw: str) -> str:
    """Lam sach va trích xuất duy nhất khối $$...$$ từ chuỗi raw model trả về."""
    # 1. Tim block $$...$$ dau tien
    m = re.search(r"\$\$(.*?)\$\$", raw, re.DOTALL)
    if m:
        content = m.group(1).strip()
        return f"$${content}$$"

    # 2. Fallback: markdown code block ```latex ... ```
    m_code = re.search(r"```(?:latex|katex|math)?\s*(.*?)\s*```", raw, re.DOTALL)
    if m_code:
        content = m_code.group(1).strip().strip("$")
        return f"$${content}$$"

    # 3. Fallback: inline $...$
    m_inline = re.search(r"\$([^$]+)\$", raw)
    if m_inline:
        content = m_inline.group(1).strip()
        return f"$${content}$$"

    # 4. Fallback: toàn bộ chuỗi (sau khi strip)
    clean = raw.strip().strip("`$").strip()
    return f"$${clean}$$"


def _call_vision_model(img_bytes: bytes, prompt: str) -> str:
    """Goi AI Gateway de chuyen doi anh cong thuc sang LaTeX.

    Args:
        img_bytes: Binary cua anh cong thuc (PNG/JPEG/WMF/EMF).
        prompt: Prompt huong dan model.

    Returns:
        Chuoi tra ve tu model (chua validate).
    """
    import base64
    import io

    from PIL import Image

    from ccba_ai import ModelArchetype, ai

    try:
        pil_img = Image.open(io.BytesIO(img_bytes))
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG", optimize=True)
        b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        b64_img = base64.b64encode(img_bytes).decode("utf-8")

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}},
            ],
        }
    ]

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
            raw = _call_vision_model(img_bytes, prompt)
            cleaned = _clean_and_extract_katex(raw)

            if cleaned and _validate_katex(cleaned):
                if cache_dir is not None:
                    _write_cache(cache_dir, sha256, cleaned)
                logger.info("Formula extracted (attempt %d): %s", attempt + 1, cleaned[:60])
                return cleaned
            logger.warning(
                "Vision attempt %d invalid format (sha256=%s): %s",
                attempt + 1,
                sha256[:8],
                raw.strip()[:80],
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


def _get_forward_caption_text(paragraphs: list[Any], center: int, window: int = 2) -> str:
    parts: list[str] = []
    for idx in range(center + 1, min(len(paragraphs), center + window + 1)):
        txt = "".join(el.text or "" for el in paragraphs[idx].iter() if el.tag.endswith("}t"))
        parts.append(txt.strip())
    return "\n".join(parts)


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
    ns_w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

    with zipfile.ZipFile(docx_path, "r") as z:
        rels_xml = z.read("word/_rels/document.xml.rels")
        rels_tree = ET.fromstring(rels_xml)
        r_map: dict[str, str] = {}
        for rel in rels_tree:
            rid = rel.attrib.get("Id")
            target = rel.attrib.get("Target", "")
            if rid and ("media/" in target or "embeddings/" in target):
                r_map[rid] = "word/" + target.replace("../", "")
        media_files = {f for f in z.namelist() if f.startswith("word/media/")}

        doc_xml = z.read("word/document.xml")
        doc_tree = ET.fromstring(doc_xml)
        paragraphs = doc_tree.findall(
            ".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"
        )

        fig_overrides_file = docx_path.parent.parent / "figures_override.yaml"
        if not fig_overrides_file.exists():
            fig_overrides_file = docx_path.parent / "figures_override.yaml"
        override_figures_media: dict[str, tuple[str, str]] = {}
        if fig_overrides_file.exists():
            try:
                import yaml

                f_data = yaml.safe_load(fig_overrides_file.read_text(encoding="utf-8"))
                if isinstance(f_data, dict):
                    for f_tag, f_val in f_data.items():
                        if isinstance(f_val, dict) and "media" in f_val:
                            m_p = f_val["media"].replace("../", "")
                            if not m_p.startswith("word/"):
                                m_p = f"word/{m_p}"
                            f_slug = str(f_tag).lower().replace(".", "_").replace("-", "_")
                            f_title = f_val.get("title", f"Sơ đồ / Hình {f_tag}")
                            override_figures_media[m_p] = (f_slug, f_title)
            except Exception:
                pass

        form_overrides_file = docx_path.parent.parent / "formulas_override.yaml"
        if not form_overrides_file.exists():
            form_overrides_file = docx_path.parent / "formulas_override.yaml"
        override_formulas: dict[str, str] = {}
        if form_overrides_file.exists():
            try:
                import yaml

                form_data = yaml.safe_load(form_overrides_file.read_text(encoding="utf-8"))
                if isinstance(form_data, dict):
                    for k_id, k_val in form_data.items():
                        if isinstance(k_val, dict):
                            l_val = k_val.get("latex", "").strip()
                            f_id = k_val.get("formula_id", "")

                            # Determine proper tag: never use 'rId...' as tag
                            has_tag = "\\tag" in l_val or "\\qquad" in l_val or "\\hfill" in l_val
                            is_multiline_env = any(
                                env in l_val
                                for env in ("aligned", "cases", "gather", "matrix", "split")
                            )
                            if not has_tag and not is_multiline_env:
                                if not str(k_id).lower().startswith("rid"):
                                    tag_to_use = str(k_id)
                                elif f_id and "FORMULA_" in f_id:
                                    tag_to_use = f_id.split("FORMULA_")[-1].replace("_", ".")
                                else:
                                    tag_to_use = None

                                if tag_to_use:
                                    l_val = f"{l_val} \\tag{{{tag_to_use}}}"

                            override_formulas[str(k_id)] = (
                                f'$${l_val}$$\n<!-- formula_id: "{f_id}" -->'
                                if f_id
                                else f"$${l_val}$$"
                            )
                        elif isinstance(k_val, str):
                            override_formulas[str(k_id)] = k_val
            except Exception:
                pass

        import concurrent.futures

        rid_to_katex: dict[str, str] = {}
        pending_rids: dict[str, bytes] = {}

        # Build image_rid -> ole_rid mapping from <w:object> (ADR 0040)
        ns_o = "urn:schemas-microsoft-com:office:office"
        image_rid_to_ole_rid: dict[str, str] = {}
        for obj_el in doc_tree.findall(f".//{{{ns_w}}}object"):
            img_el = obj_el.find(f".//{{{ns_v}}}imagedata")
            ole_el = obj_el.find(f".//{{{ns_o}}}OLEObject")
            if img_el is not None and ole_el is not None:
                img_rid = img_el.attrib.get(f"{{{ns_r}}}id")
                ole_rid = ole_el.attrib.get(f"{{{ns_r}}}id")
                if img_rid and ole_rid:
                    image_rid_to_ole_rid[img_rid] = ole_rid

        for p_idx, para in enumerate(paragraphs):
            # 1. Check legacy VML shapes (v:shape)
            for shape in para.findall(f".//{{{ns_v}}}shape"):
                img_el = shape.find(f"{{{ns_v}}}imagedata")
                if img_el is None:
                    continue
                rid = img_el.attrib.get(f"{{{ns_r}}}id")
                if not rid or rid not in r_map:
                    continue

                media_path = r_map[rid]
                if media_path in override_figures_media:
                    f_slug, f_title = override_figures_media[media_path]
                    rid_to_katex[rid] = f"<!-- FIGURE: hinh_{f_slug}|{f_title} -->"
                    continue

                if rid in override_formulas:
                    rid_to_katex[rid] = override_formulas[rid]
                    continue
                if media_path in override_formulas:
                    rid_to_katex[rid] = override_formulas[media_path]
                    continue

                # Tier 1 (ADR 0040): Deterministic MathType MTEF Binary decoding
                if rid in image_rid_to_ole_rid:
                    ole_rid = image_rid_to_ole_rid[rid]
                    if ole_rid in r_map:
                        ole_path = r_map[ole_rid]
                        if ole_path in z.namelist():
                            ole_bytes = z.read(ole_path)
                            mtef_latex = decode_ole_mathtype(ole_bytes)
                            if mtef_latex:
                                rid_to_katex[rid] = f"$${mtef_latex}$$"
                                logger.info(
                                    "Decoded formula for rid=%s via Tier 1 MTEF parser: %s",
                                    rid,
                                    mtef_latex[:40],
                                )
                                continue

                style_str = shape.attrib.get("style", "")
                height_pt = _parse_pt(style_str, "height")
                width_pt = _parse_pt(style_str, "width")
                surrounding = _get_surrounding_text(paragraphs, p_idx, window=3)
                forward_txt = _get_forward_caption_text(paragraphs, p_idx, window=2)

                if not is_formula_image(height_pt, width_pt, surrounding, forward_text=forward_txt):
                    rid_to_katex[rid] = f"<!-- DIAGRAM: {r_map[rid]} -->"
                    continue

                media_path = r_map[rid]
                if media_path not in media_files:
                    continue

                img_bytes = z.read(media_path)
                sha256 = _compute_sha256(img_bytes)
                if sha256[:8] in override_formulas:
                    rid_to_katex[rid] = override_formulas[sha256[:8]]
                    continue
                if sha256 in override_formulas:
                    rid_to_katex[rid] = override_formulas[sha256]
                    continue
                cached = _read_cache(cache_dir, sha256) if cache_dir is not None else None
                if cached is not None:
                    rid_to_katex[rid] = cached
                elif skip_vision:
                    rid_to_katex[rid] = f"<!-- FORMULA_PLACEHOLDER: {sha256[:8]} -->"
                else:
                    pending_rids[rid] = img_bytes

            # 2. Check modern DrawingML (w:drawing)
            for drawing in para.findall(
                ".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing"
            ):
                blip = drawing.find(f".//{{{ns_a}}}blip")
                if blip is None:
                    continue
                rid = blip.attrib.get(f"{{{ns_r}}}embed")
                if not rid or rid not in r_map or rid in rid_to_katex or rid in pending_rids:
                    continue

                media_path = r_map[rid]
                if media_path in override_figures_media:
                    f_slug, f_title = override_figures_media[media_path]
                    rid_to_katex[rid] = f"<!-- FIGURE: hinh_{f_slug}|{f_title} -->"
                    continue

                if rid in override_formulas:
                    rid_to_katex[rid] = override_formulas[rid]
                    continue
                if media_path in override_formulas:
                    rid_to_katex[rid] = override_formulas[media_path]
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
                forward_txt = _get_forward_caption_text(paragraphs, p_idx, window=2)

                if not is_formula_image(height_pt, width_pt, surrounding, forward_text=forward_txt):
                    rid_to_katex[rid] = f"<!-- DIAGRAM: {r_map[rid]} -->"
                    continue

                media_path = r_map[rid]
                if media_path not in media_files:
                    continue

                img_bytes = z.read(media_path)
                sha256 = _compute_sha256(img_bytes)
                if sha256[:8] in override_formulas:
                    rid_to_katex[rid] = override_formulas[sha256[:8]]
                    continue
                if sha256 in override_formulas:
                    rid_to_katex[rid] = override_formulas[sha256]
                    continue
                cached = _read_cache(cache_dir, sha256) if cache_dir is not None else None
                if cached is not None:
                    rid_to_katex[rid] = cached
                elif skip_vision:
                    rid_to_katex[rid] = f"<!-- FORMULA_PLACEHOLDER: {sha256[:8]} -->"
                else:
                    pending_rids[rid] = img_bytes

        # Concurrently process pending formula images if any
        if pending_rids:
            unique_shas: dict[str, bytes] = {}
            for _r_id, b_data in pending_rids.items():
                sha = _compute_sha256(b_data)
                unique_shas[sha] = b_data

            sha_to_katex: dict[str, str] = {}
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=min(6, len(unique_shas))
            ) as executor:
                future_to_sha = {
                    executor.submit(extract_latex_from_image, b_data, cache_dir, False): sha
                    for sha, b_data in unique_shas.items()
                }
                for future in concurrent.futures.as_completed(future_to_sha):
                    sha = future_to_sha[future]
                    try:
                        sha_to_katex[sha] = future.result()
                    except Exception as exc:
                        logger.error("Concurrent extraction error (sha=%s): %s", sha[:8], exc)
                        sha_to_katex[sha] = f"<!-- FORMULA_ERROR: {sha[:8]} -->"

            for r_id, b_data in pending_rids.items():
                sha = _compute_sha256(b_data)
                rid_to_katex[r_id] = sha_to_katex.get(sha, f"<!-- FORMULA_ERROR: {sha[:8]} -->")

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
                    results.append(
                        {
                            "page_num": pg_idx + 1,
                            "xref": xref,
                            "width_px": w_px,
                            "height_px": h_px,
                            "katex": f"<!-- DIAGRAM_PDF: page={pg_idx + 1} xref={xref} -->",
                        }
                    )
                    continue
                try:
                    img_bytes = doc.extract_image(xref)["image"]
                except Exception as exc:
                    logger.warning("Extract image xref=%d failed: %s", xref, exc)
                    continue
                katex = extract_latex_from_image(
                    img_bytes, cache_dir=cache_dir, skip_vision=skip_vision
                )
                results.append(
                    {
                        "page_num": pg_idx + 1,
                        "xref": xref,
                        "width_px": w_px,
                        "height_px": h_px,
                        "katex": katex,
                    }
                )
    finally:
        doc.close()
    return results
