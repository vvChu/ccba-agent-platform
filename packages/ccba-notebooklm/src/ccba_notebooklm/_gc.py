import sys
from typing import Any

from ._registry import read_registry


async def run_garbage_collection(client: Any, notebook_id: str, sources: list[Any]) -> None:
    """Quét và dọn dẹp các nguồn không còn liên kết cục bộ để giải phóng Quota."""
    registry = read_registry()
    registered_ids = {
        info["source_id"]
        for info in registry.values()
        if isinstance(info, dict) and "source_id" in info
    }

    print("[Info] Bắt đầu dọn dẹp nguồn mồ côi (Garbage Collection)...")
    for src in sources:
        if src.id not in registered_ids:
            try:
                print(
                    f"[Info] Đang xóa nguồn cũ không còn dùng trên Cloud: Title='{src.title}', ID='{src.id}'..."
                )
                await client.sources.delete(notebook_id, src.id)
            except Exception as e:
                print(f"[Warn] Không thể xóa nguồn '{src.id}': {e}", file=sys.stderr)


async def check_quota_and_warn(client: Any, notebook_id: str) -> None:
    """Kiểm tra Subscription Tier và cảnh báo sớm về Quota."""
    try:
        tier = await client.settings.get_account_tier()
        limits = await client.settings.get_account_limits()
        print(f"[Info] NotebookLM Account Tier: {tier.tier} ({tier.plan_name or 'Standard Plan'})")

        # Hạn mức mặc định nếu không có limit cụ thể
        source_limit = limits.source_limit if limits.source_limit is not None else 50

        sources = await client.sources.list(notebook_id)
        current_sources_count = len(sources)

        print(f"[Info] Hạn mức nguồn tài liệu tối đa của tài khoản: {source_limit}")
        print(
            f"[Info] Số lượng nguồn hiện tại trong Notebook: {current_sources_count}/{source_limit}"
        )

        if current_sources_count >= source_limit * 0.9:
            print(
                f"\n[WARNING] Số lượng nguồn trong notebook sắp đạt giới hạn ({current_sources_count}/{source_limit})!",
                file=sys.stderr,
            )
            await run_garbage_collection(client, notebook_id, sources)
    except Exception as e:
        print(f"[Warn] Không thể kiểm tra quota: {e}", file=sys.stderr)
