"""Unit tests for GoogleDriveIngestor and drive_client (Hermetic Isolated Tests)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from ccba_legal.sync.drive_client import (
    get_credentials_dir,
    migrate_drive_credentials,
)
from ccba_legal.sync.drive_ingestor import (
    GOOGLE_DOC_MIME,
    GOOGLE_FOLDER_MIME,
    GOOGLE_SHORTCUT_MIME,
    DriveItem,
    GoogleDriveIngestor,
)
from ccba_legal.sync.utils import calculate_sha256


class TestDriveItem:
    """Test DriveItem dataclass and support filters."""

    def test_drive_item_attributes_and_supported(self) -> None:
        pdf_item = DriveItem(
            id="pdf_1",
            name="tieu_chuan.pdf",
            mime_type="application/pdf",
            modified_time="2026-09-22T00:00:00Z",
            md5_checksum="md5_abc",
        )
        assert pdf_item.is_supported() is True
        assert pdf_item.is_folder is False

        gdoc_item = DriveItem(
            id="gdoc_1",
            name="Huong Dan Thiet Ke",
            mime_type=GOOGLE_DOC_MIME,
        )
        assert gdoc_item.is_supported() is True

        docx_item = DriveItem(
            id="docx_1",
            name="ho_so.docx",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        assert docx_item.is_supported() is True

        unsupported_item = DriveItem(
            id="bin_1",
            name="setup.exe",
            mime_type="application/octet-stream",
        )
        assert unsupported_item.is_supported() is False


class TestDriveClientSeams:
    """Test drive_client module infrastructure seams."""

    def test_import_and_credentials_dir(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setenv("CCBA_CREDENTIALS_DIR", str(tmp_path / "creds"))
        cred_dir = get_credentials_dir()
        assert cred_dir == tmp_path / "creds"

    def test_migrate_drive_credentials(self, tmp_path: Path) -> None:
        scratch_dir = Path(".md/scratch")
        scratch_dir.mkdir(parents=True, exist_ok=True)
        token_file = scratch_dir / "drive_token.json"
        token_file.write_text('{"token": "test"}', encoding="utf-8")

        target_dir = tmp_path / "migrated_creds"
        migrate_drive_credentials(target_dir=target_dir)

        dest_file = target_dir / "drive_token.json"
        assert dest_file.exists()
        assert dest_file.read_text(encoding="utf-8") == '{"token": "test"}'


class TestGoogleDriveIngestor:
    """Test GoogleDriveIngestor with fully mocked Google API service."""

    @pytest.fixture
    def mock_service(self) -> MagicMock:
        service = MagicMock()
        return service

    @pytest.fixture
    def ingestor(self, mock_service: MagicMock, tmp_path: Path) -> GoogleDriveIngestor:
        reg_path = tmp_path / "registry.yaml"
        out_dir = tmp_path / "downloads"
        return GoogleDriveIngestor(
            service=mock_service,
            registry_path=reg_path,
            output_dir=out_dir,
        )

    def test_scan_my_drive_with_subfolder_recursion(
        self, ingestor: GoogleDriveIngestor, mock_service: MagicMock
    ) -> None:
        # First call lists root folder content (contains a file and a subfolder)
        root_files = [
            {
                "id": "file_1",
                "name": "root_doc.pdf",
                "mimeType": "application/pdf",
                "size": 1024,
                "modifiedTime": "2026-09-22T01:00:00Z",
                "md5Checksum": "md5_file1",
            },
            {
                "id": "folder_sub",
                "name": "SubFolder",
                "mimeType": GOOGLE_FOLDER_MIME,
            },
        ]
        # Second call lists subfolder content
        sub_files = [
            {
                "id": "file_2",
                "name": "sub_doc.docx",
                "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "size": 2048,
                "modifiedTime": "2026-09-22T01:10:00Z",
                "md5Checksum": "md5_file2",
            }
        ]

        def list_side_effect(**kwargs: Any) -> MagicMock:
            q = kwargs.get("q", "")
            req_mock = MagicMock()
            if "folder_root" in q:
                req_mock.execute.return_value = {"files": root_files}
            elif "folder_sub" in q:
                req_mock.execute.return_value = {"files": sub_files}
            else:
                req_mock.execute.return_value = {"files": []}
            return req_mock

        mock_service.files().list.side_effect = list_side_effect

        items = ingestor.scan_my_drive(folder_id="folder_root", recursive=True)
        assert len(items) == 3
        ids = [i.id for i in items]
        assert "file_1" in ids
        assert "folder_sub" in ids
        assert "file_2" in ids
        assert all(i.scope == "my-drive" for i in items)

    def test_scan_shared_with_me_recursive(
        self, ingestor: GoogleDriveIngestor, mock_service: MagicMock
    ) -> None:
        shared_root = [
            {
                "id": "shared_doc_1",
                "name": "shared_doc.pdf",
                "mimeType": "application/pdf",
                "size": 512,
                "modifiedTime": "2026-09-22T02:00:00Z",
                "md5Checksum": "md5_shared1",
            },
            {
                "id": "shared_folder_1",
                "name": "TeamFolder",
                "mimeType": GOOGLE_FOLDER_MIME,
            },
        ]
        folder_contents = [
            {
                "id": "nested_doc_2",
                "name": "nested_file.xlsx",
                "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "size": 4096,
                "modifiedTime": "2026-09-22T02:30:00Z",
                "md5Checksum": "md5_nested2",
            }
        ]

        def list_side_effect(**kwargs: Any) -> MagicMock:
            q = kwargs.get("q", "")
            req_mock = MagicMock()
            if "sharedWithMe = true" in q:
                req_mock.execute.return_value = {"files": shared_root}
            elif "shared_folder_1" in q:
                req_mock.execute.return_value = {"files": folder_contents}
            else:
                req_mock.execute.return_value = {"files": []}
            return req_mock

        mock_service.files().list.side_effect = list_side_effect

        items = ingestor.scan_shared_with_me()
        assert len(items) == 3
        ids = [i.id for i in items]
        assert "shared_doc_1" in ids
        assert "shared_folder_1" in ids
        assert "nested_doc_2" in ids
        assert all(i.scope == "shared-with-me" for i in items)

    def test_resolve_shortcut(
        self, ingestor: GoogleDriveIngestor, mock_service: MagicMock
    ) -> None:
        shortcut_item = DriveItem(
            id="shortcut_01",
            name="Shortcut to Decree",
            mime_type=GOOGLE_SHORTCUT_MIME,
            is_shortcut=True,
            target_id="real_target_doc",
        )

        mock_get = MagicMock()
        mock_get.execute.return_value = {
            "id": "real_target_doc",
            "name": "NghiDinh_217_2026.pdf",
            "mimeType": "application/pdf",
            "size": 8192,
            "modifiedTime": "2026-09-22T03:00:00Z",
            "md5Checksum": "md5_target",
        }
        mock_service.files().get.return_value = mock_get

        resolved = ingestor.resolve_shortcut(shortcut_item)
        assert resolved.id == "real_target_doc"
        assert resolved.name == "NghiDinh_217_2026.pdf"
        assert resolved.mime_type == "application/pdf"
        assert resolved.is_shortcut is False

    def test_export_google_docs_appends_pdf(
        self, ingestor: GoogleDriveIngestor, mock_service: MagicMock, tmp_path: Path
    ) -> None:
        gdoc_item = DriveItem(
            id="gdoc_456",
            name="Quy Trinh Tham Tra PCCC",
            mime_type=GOOGLE_DOC_MIME,
            modified_time="2026-09-22T04:00:00Z",
        )

        mock_export = MagicMock()
        mock_export.execute.return_value = b"%PDF-1.4 Mock Exported PDF Data"
        mock_service.files().export_media.return_value = mock_export

        out_path = ingestor.download_item(gdoc_item)
        assert out_path is not None
        assert out_path.name == "Quy Trinh Tham Tra PCCC.pdf"
        assert out_path.exists()
        assert out_path.read_bytes() == b"%PDF-1.4 Mock Exported PDF Data"
        mock_service.files().export_media.assert_called_once_with(
            fileId="gdoc_456",
            mimeType="application/pdf",
        )

    def test_deduplication_pre_download_skip_and_post_download_sha256(
        self, ingestor: GoogleDriveIngestor, mock_service: MagicMock
    ) -> None:
        binary_item = DriveItem(
            id="bin_doc_789",
            name="TaiLieuKiemDinh.pdf",
            mime_type="application/pdf",
            size_bytes=100,
            modified_time="2026-09-22T05:00:00Z",
            md5_checksum="md5_exact_match",
        )

        mock_get_media = MagicMock()
        mock_get_media.execute.return_value = b"Mock PDF Content Stamped With SHA256"
        mock_service.files().get_media.return_value = mock_get_media

        # Pass 1: Download item (not in registry yet)
        dl_path = ingestor.download_item(binary_item)
        assert dl_path is not None
        assert dl_path.exists()

        expected_sha = calculate_sha256(dl_path)
        assert binary_item.sha256 == expected_sha
        assert binary_item.id in ingestor.registry["files"]
        assert ingestor.registry["files"][binary_item.id]["sha256"] == expected_sha

        # Reset mock to verify it's NOT called again on second pass
        mock_service.files().get_media.reset_mock()

        # Pass 2: Pre-download should detect match and skip
        assert ingestor.should_download(binary_item, dl_path) is False
        skipped_path = ingestor.download_item(binary_item, force=False)
        assert skipped_path == dl_path
        mock_service.files().get_media.assert_not_called()

        # Pass 3: Force flag bypasses pre-download check
        forced_path = ingestor.download_item(binary_item, force=True)
        assert forced_path == dl_path
        mock_service.files().get_media.assert_called_once()

    def test_ingest_dry_run_and_execution(
        self, ingestor: GoogleDriveIngestor, mock_service: MagicMock
    ) -> None:
        files = [
            {
                "id": "item_pdf",
                "name": "ThietKe.pdf",
                "mimeType": "application/pdf",
                "size": 2048,
                "modifiedTime": "2026-09-22T06:00:00Z",
                "md5Checksum": "md5_pdf",
            },
            {
                "id": "item_unsupported",
                "name": "archive.zip",
                "mimeType": "application/zip",
                "size": 5000,
            },
        ]
        mock_list = MagicMock()
        mock_list.execute.return_value = {"files": files}
        mock_service.files().list.return_value = mock_list

        mock_media = MagicMock()
        mock_media.execute.return_value = b"Mock PDF Payload"
        mock_service.files().get_media.return_value = mock_media

        # Dry Run
        dry_stats = ingestor.ingest(scope="my-drive", dry_run=True)
        assert dry_stats["total_scanned"] == 2
        assert dry_stats["supported_found"] == 1
        assert dry_stats["downloaded"] == 0

        # Real Ingestion
        real_stats = ingestor.ingest(scope="my-drive", dry_run=False)
        assert real_stats["downloaded"] == 1
        assert real_stats["skipped"] == 0
        assert real_stats["failed"] == 0

    def test_drive_item_folder_not_supported_even_with_doc_extension(self) -> None:
        folder_item = DriveItem(
            id="f1",
            name="Documents.pdf",
            mime_type=GOOGLE_FOLDER_MIME,
            is_folder=True,
        )
        assert folder_item.is_supported() is False

    def test_sanitize_drive_filename(self) -> None:
        from ccba_legal.sync.drive_ingestor import sanitize_drive_filename

        assert sanitize_drive_filename("Nghi_dinh_15/2021/ND-CP.pdf") == "Nghi_dinh_15_2021_ND-CP.pdf"
        assert sanitize_drive_filename('Invalid:<>*?"|name.docx') == "Invalid_______name.docx"
        assert sanitize_drive_filename("   ...   ") == "unnamed_document"

    def test_download_item_sanitizes_slashes(
        self, ingestor: GoogleDriveIngestor, mock_service: MagicMock
    ) -> None:
        item = DriveItem(
            id="slash_doc_1",
            name="NghiDinh_15/2021/ND-CP.pdf",
            mime_type="application/pdf",
            size_bytes=100,
        )
        mock_media = MagicMock()
        mock_media.execute.return_value = b"Mock PDF with slash in name"
        mock_service.files().get_media.return_value = mock_media

        downloaded_path = ingestor.download_item(item)
        assert downloaded_path is not None
        assert downloaded_path.exists()
        assert downloaded_path.name == "NghiDinh_15_2021_ND-CP.pdf"
        assert "/" not in downloaded_path.name

    def test_download_item_folder_shortcut_skipped(
        self, ingestor: GoogleDriveIngestor, mock_service: MagicMock
    ) -> None:
        shortcut = DriveItem(
            id="sc_folder",
            name="Shortcut to Folder",
            mime_type=GOOGLE_SHORTCUT_MIME,
            is_shortcut=True,
            target_id="folder_target",
        )
        mock_get = MagicMock()
        mock_get.execute.return_value = {
            "id": "folder_target",
            "name": "RealFolder",
            "mimeType": GOOGLE_FOLDER_MIME,
        }
        mock_service.files().get.return_value = mock_get

        result = ingestor.download_item(shortcut)
        assert result is None
        mock_service.files().get_media.assert_not_called()

    def test_ingest_deduplicates_shortcuts_pointing_to_same_file(
        self, ingestor: GoogleDriveIngestor, mock_service: MagicMock
    ) -> None:
        files = [
            {
                "id": "real_file_001",
                "name": "Standard.pdf",
                "mimeType": "application/pdf",
                "size": 1024,
                "modifiedTime": "2026-09-22T07:00:00Z",
                "md5Checksum": "md5_std",
            },
            {
                "id": "shortcut_002",
                "name": "Shortcut to Standard",
                "mimeType": GOOGLE_SHORTCUT_MIME,
                "shortcutDetails": {"targetId": "real_file_001"},
            },
        ]
        mock_list = MagicMock()
        mock_list.execute.return_value = {"files": files}
        mock_service.files().list.return_value = mock_list

        mock_get = MagicMock()
        mock_get.execute.return_value = {
            "id": "real_file_001",
            "name": "Standard.pdf",
            "mimeType": "application/pdf",
            "size": 1024,
            "modifiedTime": "2026-09-22T07:00:00Z",
            "md5Checksum": "md5_std",
        }
        mock_service.files().get.return_value = mock_get

        mock_media = MagicMock()
        mock_media.execute.return_value = b"Binary data"
        mock_service.files().get_media.return_value = mock_media

        stats = ingestor.ingest(scope="my-drive", dry_run=False)
        assert stats["total_scanned"] == 2
        assert stats["supported_found"] == 1
        assert stats["downloaded"] == 1

    def test_download_filename_collision_disambiguation(
        self, ingestor: GoogleDriveIngestor, mock_service: MagicMock
    ) -> None:
        f1 = DriveItem(
            id="id_first_111",
            name="Report.pdf",
            mime_type="application/pdf",
            size_bytes=100,
            modified_time="2026-09-22T08:00:00Z",
        )
        f2 = DriveItem(
            id="id_second_222",
            name="Report.pdf",
            mime_type="application/pdf",
            size_bytes=200,
            modified_time="2026-09-22T08:10:00Z",
        )

        mock_media = MagicMock()
        mock_media.execute.return_value = b"Content"
        mock_service.files().get_media.return_value = mock_media

        p1 = ingestor.download_item(f1)
        p2 = ingestor.download_item(f2)

        assert p1 is not None and p2 is not None
        assert p1 != p2
        assert p1.name == "Report.pdf"
        assert p2.name == "Report_id_secon.pdf"
        assert p1.exists() and p2.exists()

    def test_should_download_corrupted_empty_file_redownloads(
        self, ingestor: GoogleDriveIngestor, tmp_path: Path
    ) -> None:
        item = DriveItem(
            id="empty_test_id",
            name="valid.pdf",
            mime_type="application/pdf",
            size_bytes=5000,
            modified_time="2026-09-22T09:00:00Z",
        )
        empty_local = tmp_path / "valid.pdf"
        empty_local.write_bytes(b"")

        ingestor.registry["files"][item.id] = {
            "modified_time": "2026-09-22T09:00:00Z",
            "local_path": str(empty_local),
        }
        assert ingestor.should_download(item, empty_local) is True
