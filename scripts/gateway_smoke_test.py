#!/usr/bin/env python3
"""Gateway Smoke-Test -- Kiem Chung 3 Gia Thuyet Tu Phan Bien.

Mục tiêu: Thay thế giả thuyết lý thuyết bằng dữ liệu thực từ AI Gateway.

Giả thuyết cần kiểm chứng:
  H1: LiteLLM có silently cap max_tokens không? (vd: gửi 16384 nhưng gateway chỉ cho 4096?)
  H2: Trường usage (prompt_tokens / completion_tokens / total_tokens) có được forward không?
  H3: Response từ reasoning model có bị truncate think-tags không? (strip_thinking hoạt động)

Không phải integration test — đây là diagnostic / observability script.
Chạy thủ công: python scripts/gateway_smoke_test.py
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GATEWAY_URL = os.getenv("AI_GATEWAY_URL", "http://100.83.192.30:8090/v1")
GATEWAY_KEY = os.getenv("AI_GATEWAY_KEY", "ccba-platform")
TIMEOUT = 60.0

# Models to probe — chọn lightweight để giảm cost
STANDARD_MODEL = "gemini-3.7-flash"
REASONING_MODEL = "gemini-3.7-flash-high"

# Token budgets to probe
PROBE_MAX_TOKENS = 16_384  # H1: ta request 16384, gateway có honor không?


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class HypothesisResult:
    """Kết quả kiểm chứng 1 giả thuyết."""

    name: str
    hypothesis: str
    verdict: str = "UNKNOWN"  # CONFIRMED | REFUTED | INCONCLUSIVE
    evidence: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def passed(self) -> bool:
        """Giả thuyết ban đầu là LO NGẠI — REFUTED = lo ngại không có thật = tốt."""
        return self.verdict == "REFUTED"


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------
def make_client() -> OpenAI:
    return OpenAI(
        base_url=GATEWAY_URL,
        api_key=GATEWAY_KEY,
        timeout=TIMEOUT,
    )


def call_chat(
    client: OpenAI,
    model: str,
    prompt: str,
    max_tokens: int = 256,
) -> tuple[Any, float]:
    """Gọi API và trả về (response, latency_ms)."""
    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    latency_ms = (time.perf_counter() - t0) * 1000
    return resp, latency_ms


# ---------------------------------------------------------------------------
# H1: max_tokens cap detection
# ---------------------------------------------------------------------------
def check_h1_max_tokens_cap(client: OpenAI) -> HypothesisResult:
    """H1: Gateway có silently cap max_tokens < 16384 không?

    Cách kiểm chứng:
      - Gửi request max_tokens=16384 đến reasoning model
      - So sánh completion_tokens với max_tokens đã request
      - Nếu completion_tokens bị cap tại một ngưỡng thấp hơn nhiều (vd 4096)
        trong khi prompt đơn giản có thể trả dài hơn -> nghi ngờ có cap
      - Thực tế: ta dùng prompt yêu cầu response ngắn để phân biệt
        "model tự chọn ngắn" vs "bị cap"
    """
    result = HypothesisResult(
        name="H1",
        hypothesis="LiteLLM silently cap max_tokens < 16384 cho reasoning models",
    )

    # Sub-test A: Request 16384, prompt đơn giản -> xem completion_tokens thực tế
    try:
        resp_a, lat_a = call_chat(
            client,
            REASONING_MODEL,
            prompt="Tra loi dung 1 cau: So Pi xap xi bang bao nhieu?",
            max_tokens=PROBE_MAX_TOKENS,
        )
        usage_a = resp_a.usage
        raw_usage = {
            "prompt_tokens": getattr(usage_a, "prompt_tokens", None),
            "completion_tokens": getattr(usage_a, "completion_tokens", None),
            "total_tokens": getattr(usage_a, "total_tokens", None),
        }

        # Nếu có finish_reason = "length" -> chắc chắn bị cap
        finish_reason = resp_a.choices[0].finish_reason
        result.raw["sub_a"] = {
            "model": REASONING_MODEL,
            "requested_max_tokens": PROBE_MAX_TOKENS,
            "finish_reason": finish_reason,
            "latency_ms": round(lat_a, 1),
            **raw_usage,
        }
        result.evidence.append(
            f"Sub-A [{REASONING_MODEL}]: finish_reason={finish_reason!r}, "
            f"completion_tokens={raw_usage['completion_tokens']}, latency={lat_a:.0f}ms"
        )

        # Sub-test B: Cùng model nhưng request max_tokens=256 để so sánh
        resp_b, lat_b = call_chat(
            client,
            REASONING_MODEL,
            prompt="Tra loi dung 1 cau: So Pi xap xi bang bao nhieu?",
            max_tokens=256,
        )
        usage_b = resp_b.usage
        finish_b = resp_b.choices[0].finish_reason
        result.raw["sub_b"] = {
            "model": REASONING_MODEL,
            "requested_max_tokens": 256,
            "finish_reason": finish_b,
            "completion_tokens": getattr(usage_b, "completion_tokens", None),
            "latency_ms": round(lat_b, 1),
        }
        result.evidence.append(
            f"Sub-B [max=256]: finish_reason={finish_b!r}, "
            f"completion_tokens={usage_b.completion_tokens}, latency={lat_b:.0f}ms"
        )

        # Phan quyet
        if finish_reason == "length":
            result.verdict = "INCONCLUSIVE"
            result.evidence.append(
                "finish_reason='length' -- co the bi cap HOAC model thuc su dung du 16384. "
                "Can them probe voi prompt dai hon."
            )
        else:
            # finish_reason = 'stop' -> model tu ket thuc, khong bi cat
            result.verdict = "REFUTED"
            result.evidence.append(
                "finish_reason='stop' -> Gateway KHONG cap max_tokens. "
                "Model tu dung theo ngu nghia, khong bi truncate cung."
            )
    except Exception as exc:
        result.verdict = "INCONCLUSIVE"
        result.evidence.append(f"Exception khi goi Gateway: {exc}")

    return result


# ---------------------------------------------------------------------------
# H2: usage field forwarding
# ---------------------------------------------------------------------------
def check_h2_usage_forwarding(client: OpenAI) -> HypothesisResult:
    """H2: Gateway co forward du truong usage khong?

    Cach kiem chung:
      - Goi standard model voi prompt don gian
      - Kiem tra usage.prompt_tokens, completion_tokens, total_tokens deu > 0
      - Kiem tra tinh nhat quan: prompt_tokens + completion_tokens ~ total_tokens
    """
    result = HypothesisResult(
        name="H2",
        hypothesis="Gateway khong forward truong usage (prompt/completion/total_tokens = 0 hoac None)",
    )

    try:
        resp, lat = call_chat(
            client,
            STANDARD_MODEL,
            prompt="Xin chao! Ban co the giup toi khong?",
            max_tokens=128,
        )
        usage = resp.usage
        pt = getattr(usage, "prompt_tokens", None)
        ct = getattr(usage, "completion_tokens", None)
        tt = getattr(usage, "total_tokens", None)

        result.raw["usage"] = {"prompt_tokens": pt, "completion_tokens": ct, "total_tokens": tt}
        result.evidence.append(
            f"prompt_tokens={pt}, completion_tokens={ct}, total_tokens={tt}, latency={lat:.0f}ms"
        )

        if pt is None or ct is None or tt is None:
            result.verdict = "CONFIRMED"
            result.evidence.append(
                "FAIL: Mot hoac nhieu truong usage la None -> Gateway KHONG forward du."
            )
        elif pt == 0 or ct == 0 or tt == 0:
            result.verdict = "CONFIRMED"
            result.evidence.append("FAIL: Truong usage = 0 -> Gateway co the dang drop usage data.")
        else:
            # Kiem tra tinh nhat quan
            expected_total = pt + ct
            delta = abs(tt - expected_total)
            result.raw["usage"]["consistency_delta"] = delta
            if delta > 10:  # tolerance cho cached tokens hoac thinking tokens
                result.verdict = "INCONCLUSIVE"
                result.evidence.append(
                    f"WARN: total_tokens={tt} != prompt+completion={expected_total} (delta={delta}). "
                    "Co the Gateway dang tinh them thinking tokens."
                )
            else:
                result.verdict = "REFUTED"
                result.evidence.append(
                    f"OK: Tat ca usage fields deu hop le. "
                    f"Consistency OK (delta={delta} <= 10 tokens)."
                )
    except Exception as exc:
        result.verdict = "INCONCLUSIVE"
        result.evidence.append(f"Exception khi goi Gateway: {exc}")

    return result


# ---------------------------------------------------------------------------
# H3: Think-tag stripping (SDK-level, khong phu thuoc Gateway)
# ---------------------------------------------------------------------------
def check_h3_think_tag_strip(client: OpenAI) -> HypothesisResult:
    """H3: Raw response tu reasoning model co chua <think> tags khong?

    Muc dich: Xac dinh xem Gateway co tu strip think-tags phia server khong,
    hay ta phai lam dieu do hoan toan phia client (SDK).
    Dieu nay quyet dinh ai chiu trach nhiem sanitization.
    """
    result = HypothesisResult(
        name="H3",
        hypothesis="Gateway tu strip <think> tags -> SDK khong can lam them",
    )

    try:
        resp, lat = call_chat(
            client,
            REASONING_MODEL,
            prompt="Tinh 17 x 13 va giai thich tung buoc ngan gon.",
            max_tokens=1024,
        )
        content = resp.choices[0].message.content or ""
        has_open_tag = "<think>" in content.lower()
        has_close_tag = "</think>" in content.lower()

        result.raw["think_tags"] = {
            "has_open_tag": has_open_tag,
            "has_close_tag": has_close_tag,
            "content_length": len(content),
            "content_preview": content[:300],
            "latency_ms": round(lat, 1),
        }
        result.evidence.append(
            f"Content length={len(content)}, has <think>={has_open_tag}, has </think>={has_close_tag}"
        )
        result.evidence.append(f"Preview: {content[:200]!r}")

        if not has_open_tag and not has_close_tag:
            result.verdict = "CONFIRMED"
            result.evidence.append(
                "Gateway DA strip think-tags phia server -> "
                "SDK strip_thinking=True la defense-in-depth them (tot, khong redundant)."
            )
        else:
            result.verdict = "REFUTED"
            result.evidence.append(
                "Think-tags VAN CON trong raw response -> "
                "SDK PHAI tu strip (strip_thinking=True trong client.py la bat buoc)."
            )
    except Exception as exc:
        result.verdict = "INCONCLUSIVE"
        result.evidence.append(f"Exception khi goi Gateway: {exc}")

    return result


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def print_report(results: list[HypothesisResult]) -> None:
    """In bao cao ket qua ra stdout."""
    sep = "=" * 70
    print(f"\n{sep}")
    print("  GATEWAY SMOKE-TEST REPORT")
    print(f"  Gateway: {GATEWAY_URL}")
    print(f"  Thoi gian: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(sep)

    for r in results:
        icon = {"REFUTED": "[OK]", "CONFIRMED": "[FAIL]", "INCONCLUSIVE": "[WARN]"}.get(
            r.verdict, "[?]"
        )
        print(f"\n[{r.name}] {r.hypothesis}")
        print(f"  Verdict: {icon} {r.verdict}")
        for ev in r.evidence:
            print(f"  - {ev}")

    print(f"\n{sep}")
    print("TONG KET:")
    refuted = sum(1 for r in results if r.verdict == "REFUTED")
    confirmed = sum(1 for r in results if r.verdict == "CONFIRMED")
    inconclusive = sum(1 for r in results if r.verdict == "INCONCLUSIVE")
    print(f"  [OK]   Gia thuyet lo ngai KHONG CO THAT: {refuted}/{len(results)}")
    print(f"  [FAIL] Gia thuyet lo ngai CO THAT:       {confirmed}/{len(results)}")
    print(f"  [WARN] Can dieu tra them:                {inconclusive}/{len(results)}")
    print(sep)

    # Dump raw JSON de audit
    raw_dump = {r.name: r.raw for r in results}
    print("\nRAW DATA (JSON):")
    print(json.dumps(raw_dump, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Chay toan bo smoke-test."""
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print(f"Connecting to Gateway: {GATEWAY_URL} ...")
    client = make_client()

    results: list[HypothesisResult] = []

    print("\n[H1] Kiem tra max_tokens cap ...")
    results.append(check_h1_max_tokens_cap(client))

    print("[H2] Kiem tra usage field forwarding ...")
    results.append(check_h2_usage_forwarding(client))

    print("[H3] Kiem tra think-tag stripping (Gateway vs SDK) ...")
    results.append(check_h3_think_tag_strip(client))

    print_report(results)


if __name__ == "__main__":
    main()
