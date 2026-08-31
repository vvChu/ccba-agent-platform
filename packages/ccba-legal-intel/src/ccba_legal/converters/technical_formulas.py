"""Mathematical constants, Greek maps, and standard formula catalogs (ADR 0030, ADR 0031)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

GREEK_MAP: dict[str, str] = {
    "α": r"\alpha", "β": r"\beta", "γ": r"\gamma", "δ": r"\delta",
    "ε": r"\epsilon", "η": r"\eta", "θ": r"\theta", "λ": r"\lambda",
    "μ": r"\mu", "ν": r"\nu", "ξ": r"\xi", "π": r"\pi", "ρ": r"\rho",
    "σ": r"\sigma", "τ": r"\tau", "φ": r"\varphi", "ψ": r"\psi",
    "ω": r"\omega", "Δ": r"\Delta", "Σ": r"\Sigma", "Ω": r"\Omega",
}

INLINE_SYMBOLS_MAP: dict[str, str] = {
    "rId18": r"\ell",
    "rId19": r"\bar{\epsilon}",
    "rId28": r"\bar{b}",
}

MATH_OPERATORS_MAP: dict[str, str] = {
    "≤": r"\le",
    "≥": r"\ge",
    "≠": r"\ne",
    "≈": r"\approx",
    "±": r"\pm",
    "∓": r"\mp",
    "×": r"\times",
    "·": r"\cdot",
    "÷": r"\div",
    "∞": r"\infty",
    "→": r"\to",
    "ℓ": r"\ell",
}

AERODYNAMIC_FIGURES_GEOMETRY: dict[str, dict[str, Any]] = {}

FORMULAS_MAP: dict[str, tuple[str, str]] = {
    "1": ("F_TCVN2737_TO_HOP_CO_BAN_1", r'C_m = \gamma_n \left( \sum_{i \ge 1} \gamma_{f,i} G_{k,i} \text{ “+” } \sum_{j \ge 1} \gamma_{f,j} \psi_{L,j} Q_{k,L,j} \text{ “+” } \sum_{m \ge 1} \gamma_{f,m} \psi_{t,m} Q_{k,t,m} \right)'),
    "2": ("F_TCVN2737_TO_HOP_DAC_BIET_2", r'C_a = \left( \sum_{i \ge 1} \gamma_{f,i} G_{k,i} \text{ “+” } \sum_{j \ge 1} \gamma_{f,j} \psi_{L,j} Q_{k,L,j} \text{ “+” } \sum_{m \ge 1} \gamma_{f,m} \psi_{t,m} Q_{k,t,m} \right) \text{ “+” } A_d'),
    "3": ("F_TCVN2737_HE_SO_GIAM_DIEN_TICH_1", r"\varphi_1 = 0,4 + \frac{0,6}{\sqrt{A / A_1}} \ge 0,6"),
    "4": ("F_TCVN2737_HE_SO_GIAM_DIEN_TICH_2", r"\varphi_2 = 0,5 + \frac{0,5}{\sqrt{A / A_2}} \ge 0,6"),
    "5": ("F_TCVN2737_HE_SO_GIAM_SO_TANG_1", r"\varphi_3 = 0,4 + \frac{\varphi_1 - 0,4}{\sqrt{n}} \ge 0,5"),
    "6": ("F_TCVN2737_HE_SO_GIAM_SO_TANG_2", r"\varphi_4 = 0,5 + \frac{\varphi_2 - 0,5}{\sqrt{n}} \ge 0,5"),
    "7": ("F_TCVN2737_LUC_BUNG_CAU_TRUC", r"F_{d,up} = \gamma_f \cdot \xi \cdot Q_{k,t}"),
    "8": ("F_TCVN2737_LUC_VA_CHAM_CAU_TRUC", r"F_{d',down} = C \sqrt{m}"),
    "9": ("F_TCVN2737_LUC_HAM_NGANG_CAU_TRUC", r"F_{d,h} = \xi \cdot G_k"),
    "10": ("F_TCVN2737_AP_LUC_GIO_TIEU_CHUAN", r"W_k = W_{3s,10} \cdot k(z_e) \cdot c \cdot G_f"),
    "11": ("F_TCVN2737_VAN_TOC_GIO_3S_10", r"W_0 = 0,0613 \, V_0^2"),
    "12": ("F_TCVN2737_HE_SO_DO_CAO_GIO", r"k(z_e) = 2,01 \left(\frac{z_e}{z_g}\right)^{2/\alpha}"),
    "13": ("F_TCVN2737_HE_SO_GIAT_GF", r"G_f = 0,925 \left( \frac{1 + 1,7 I(z_s) \sqrt{g_Q^2 Q^2 + g_R^2 R^2}}{1 + 1,7 g_v I(z_s)} \right)"),
    "14": ("F_TCVN2737_CUONG_DO_NHIEU_DONG", r"I(z_s) = c_r \left(\frac{10}{z_s}\right)^{1/6}"),
    "15": ("F_TCVN2737_HE_SO_DINH_CONG_HUONG_GR", r"g_R = \sqrt{2 \ln(3\,600 n_1)} + \frac{0,577}{\sqrt{2 \ln(3\,600 n_1)}}"),
    "16": ("F_TCVN2737_HE_SO_PHAN_UNG_NEN", r"Q = \sqrt{\frac{1}{1 + 0,63 \left(\frac{b + h}{L(z_s)}\right)^{0,63}}}"),
    "17": ("F_TCVN2737_TY_LE_CHIEU_DAI_TICH_PHAN", r"L(z_s) = \ell \left(\frac{z_s}{10}\right)^{\bar{\epsilon}}"),
    "18": ("F_TCVN2737_HE_SO_PHAN_UNG_CONG_HUONG_R", r"R = \sqrt{\frac{1}{\beta} R_n R_h R_b (0,53 + 0,47 R_d)}"),
    "19": ("F_TCVN2737_HAM_MAT_DO_PHO_NANG_LUONG", r"R_n = \frac{7,47 N_1}{(1 + 10,3 N_1)^{5/3}}"),
    "20": ("F_TCVN2737_TAN_SO_KHONG_THU_NGUYEN", r"N_1 = \frac{n_1 L(z_s)}{V(z_s)_{3\,600\text{s},50}}"),
    "21": ("F_TCVN2737_VAN_TOC_GIO_TRUNG_BINH_3600S", r"V(z_s)_{3\,600\text{s},50} = \bar{b} \left(\frac{z_s}{10}\right)^{\bar{\alpha}} V_{3s,50}"),
    "22": ("F_TCVN2737_HAM_TUONG_QUAN_CHIEU_CAO", r"R_h = \frac{1}{\eta_h} - \frac{1}{2\eta_h^2}\left(1 - e^{-2\eta_h}\right); \quad R_h = 1 \text{ khi } \eta_h = 0"),
    "23": ("F_TCVN2737_HAM_TUONG_QUAN_CHIEU_RONG", r"R_b = \frac{1}{\eta_b} - \frac{1}{2\eta_b^2}\left(1 - e^{-2\eta_b}\right); \quad R_b = 1 \text{ khi } \eta_b = 0"),
    "24": ("F_TCVN2737_HAM_TUONG_QUAN_CHIEU_SAU", r"R_d = \frac{1}{\eta_d} - \frac{1}{2\eta_d^2}\left(1 - e^{-2\eta_d}\right); \quad R_d = 1 \text{ khi } \eta_d = 0"),
    "25": ("F_TCVN2737_DO_VONG_GIOI_HAN", r"f \le f_u"),
    "B.1": ("F_TCVN2737_LUC_VA_CHAM_B1", r"F_k = \frac{m v^2}{f}"),
    "B.2": ("F_TCVN2737_KHOI_LUONG_QUY_DOI_B2", r"m = \frac{m_b}{2} + (m_c + k m_q) \frac{L - L_1}{L}"),
    "B.3": ("F_TCVN2737_LUC_VA_CHAM_TINH_TOAN_B3", r"F_d = \gamma_f F_k"),
    "E.1": ("F_TCVN2737_HE_SO_AP_LUC_KHONG_KHI_E1", r"k_n = 1 - 0,1 \cdot \dots"),
    "E.2": ("F_TCVN2737_HE_SO_DO_CAO_E2", r"\dots"),
    "F.1": ("F_TCVN2737_SO_REYNOLD_F1", r"\text{Re} = \frac{d \cdot V(z_e)_{3\,600\text{s},50}}{\nu}"),
    "F.2": ("F_TCVN2737_VAN_TOC_GIO_F2", r"V(z_e)_{3\,600\text{s},50} = \bar{b} \left(\frac{z_e}{10}\right)^{\bar{\alpha}} V_{3\text{s},50}"),
    "F.3": ("F_TCVN2737_HE_SO_KHI_DONG_F3", r"c_{e1} = k_{\lambda 1} c_\beta"),
    "F.4": ("F_TCVN2737_HE_SO_KHI_DONG_F4", r"c_x = k_\lambda c_{x\infty}"),
    "F.5": ("F_TCVN2737_HE_SO_KHI_DONG_F5", r"c_{x\beta} = c_x \sin^2 \beta"),
    "F.6": ("F_TCVN2737_HE_SO_KHI_DONG_F6", r"c_x = k_\lambda c_{x\infty}"),
    "F.7": ("F_TCVN2737_HE_SO_KHI_DONG_F7", r"c_x = \frac{\sum c_{xi} A_i}{A_c}"),
    "F.8": ("F_TCVN2737_HE_SO_KHI_DONG_F8", r"c_t = c_x (1 + \eta) k_1"),
    "F.9": ("F_TCVN2737_HE_SO_KHI_DONG_F9", r"\varphi = \frac{\sum A_i}{A_c} = \frac{A}{A_c}"),
    "G.1": ("F_TCVN2737_DO_VONG_GIOI_HAN_G1", r"f_u = \frac{g(p + p_1 + q)}{30n^2 (bp + p_1 + q)}"),
}


def load_bundle_formula_overrides(bundle_dir: Path) -> dict[str, tuple[str, str]]:
    """Load bundle-level formula overrides from `formulas_override.yaml` if present."""
    override_file = bundle_dir / "formulas_override.yaml"
    if not override_file.exists():
        return {}

    try:
        data = yaml.safe_load(override_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}

        res: dict[str, tuple[str, str]] = {}
        for tag, val in data.items():
            str_tag = str(tag)
            if isinstance(val, dict):
                fid = val.get("formula_id", f"F_OVERRIDE_{str_tag.upper()}")
                latex = val.get("latex", "")
                res[str_tag] = (fid, latex)
            elif isinstance(val, tuple) and len(val) == 2:
                res[str_tag] = (str(val[0]), str(val[1]))
            elif isinstance(val, str):
                res[str_tag] = (f"F_OVERRIDE_{str_tag.upper()}", val)
        return res
    except Exception:
        return {}

