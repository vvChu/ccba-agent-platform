import sys
from pathlib import Path

src_dir = Path(__file__).parents[1] / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import pytest

from ccba_notebooklm import (
    check_auth,
    get_client,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]
from ccba_notebooklm.__main__ import (
    map_info_detail,
    map_info_orientation,
    map_info_style,
    map_quiz_difficulty,
    map_quiz_quantity,
    map_report_format,
    map_slide_format,
    map_slide_length,
    map_video_format,
    map_video_style,
)


def test_public_interface_exists():
    """Verify that all core interfaces are exported."""
    assert check_auth is not None
    assert get_client is not None


def test_cli_enum_mappings():
    """Verify mapping functions map strings to correct types/objects."""
    from ccba_notebooklm import HAS_NOTEBOOKLM

    if HAS_NOTEBOOKLM:
        assert map_quiz_quantity("fewer") is not None
        assert map_quiz_difficulty("easy") is not None
        assert map_slide_format("presenter") is not None
        assert map_slide_length("short") is not None
        assert map_info_orientation("landscape") is not None
        assert map_info_detail("summary") is not None
        assert map_info_style("minimal") is not None
        assert map_report_format("blog_post") is not None
        assert map_video_format("brief") is not None
        assert map_video_style("classic") is not None
    else:
        # Fallbacks when library is not available
        assert map_quiz_quantity("fewer") is None
        assert map_quiz_difficulty("easy") is None
