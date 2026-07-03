#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Helper script bọc các tính năng của ccba-notebooklm phục vụ cho CCBA Agent Platform.
Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng
"""
import sys
from ccba_notebooklm.__main__ import main
from ccba_notebooklm import (
    HAS_NOTEBOOKLM,
    NotebookLMClient,
    check_auth,
    get_client,
    get_file_sha256,
    get_notebook_id_from_context,
    save_notebook_id_to_context,
    read_registry,
    update_registry,
    check_quota_and_warn,
    run_garbage_collection,
    run_maskara_gate,
    delete_notebook,
    delete_source,
    extract_and_summarize,
    get_or_create_project_notebook,
    get_source_id_by_path,
    handle_artifact_flow,
    list_notebooks,
    list_sources,
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
    query_rag,
    share_notebook,
)

if __name__ == "__main__":
    sys.exit(main())
