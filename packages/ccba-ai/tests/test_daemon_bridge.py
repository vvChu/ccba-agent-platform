"""Unit tests for PersistentStdioDaemon (ccba_ai.daemon_bridge)."""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ccba_ai.daemon_bridge import PersistentStdioDaemon, kill_process_tree


class TestPersistentStdioDaemon:
    """Tests for PersistentStdioDaemon lifecycle and stream synchronization."""

    def test_lazy_boot_not_spawned_initially(self) -> None:
        """Daemon should not spawn any process on initialization."""
        cmd_builder = MagicMock(return_value=["mock-cli", "--daemon"])
        daemon = PersistentStdioDaemon(build_command=cmd_builder, idle_timeout=60.0)

        assert daemon.is_running is False
        cmd_builder.assert_not_called()
        daemon.stop()

    def test_send_turn_sync_success(self) -> None:
        """Daemon should spawn process and send turn through stdin/stdout."""
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stdin = io.StringIO()
        mock_proc.stdout = io.StringIO('{"type":"result","text":"daemon response"}\n')

        daemon = PersistentStdioDaemon(build_command=lambda: ["mock-cli"], idle_timeout=60.0)

        with patch("subprocess.Popen", return_value=mock_proc):
            text, _ = daemon.send_turn_sync(
                prompt="Ping",
                parse_response_fn=lambda raw: (raw.strip(), None),
                fallback_oneshot_fn=lambda p: ("oneshot", None),
            )
            assert '{"type":"result","text":"daemon response"}' in text
            assert daemon.is_running is True

        daemon.stop()

    def test_send_turn_sync_spillover_on_high_contention(self) -> None:
        """Should bypass daemon and call fallback_oneshot_fn if contention >= max_waiting_requests."""
        daemon = PersistentStdioDaemon(
            build_command=lambda: ["mock-cli"],
            max_waiting_requests=1,
        )
        # Simulate active waiting request
        with daemon._state_lock:
            daemon._waiting_count = 1

        oneshot_mock = MagicMock(return_value=("spillover result", None))

        result, _ = daemon.send_turn_sync(
            prompt="High contention prompt",
            parse_response_fn=lambda raw: (raw, None),
            fallback_oneshot_fn=oneshot_mock,
        )

        assert result == "spillover result"
        oneshot_mock.assert_called_once_with("High contention prompt")
        daemon.stop()

    def test_send_turn_sync_handles_exception_and_falls_back(self) -> None:
        """If exception occurs during turn, process is cleaned up and fallback is called."""
        daemon = PersistentStdioDaemon(build_command=lambda: ["mock-cli"])

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stdin = MagicMock()
        mock_proc.stdin.write.side_effect = BrokenPipeError("Pipe closed")

        with patch("subprocess.Popen", return_value=mock_proc):
            oneshot_called = False

            def mock_oneshot(p: str):
                nonlocal oneshot_called
                oneshot_called = True
                return "oneshot recovered", None

            result, _ = daemon.send_turn_sync(
                prompt="Broken pipe prompt",
                parse_response_fn=lambda raw: (raw, None),
                fallback_oneshot_fn=mock_oneshot,
            )
            assert result == "oneshot recovered"
            assert oneshot_called is True
            assert daemon._proc is None  # Should be stopped/cleaned up

        daemon.stop()

    def test_stop_cleans_up_process(self) -> None:
        """Calling stop() should terminate subprocess and kill process tree."""
        mock_proc = MagicMock()
        mock_proc.pid = 99999
        mock_proc.stdin = MagicMock()

        daemon = PersistentStdioDaemon(build_command=lambda: ["mock-cli"])
        daemon._proc = mock_proc

        with patch("ccba_ai.daemon_bridge.kill_process_tree") as mock_kill:
            daemon.stop()
            assert daemon._proc is None
            mock_proc.terminate.assert_called_once()
            mock_kill.assert_called_once_with(99999)

    def test_kill_process_tree_none_safe(self) -> None:
        """kill_process_tree(None) should return silently without error."""
        kill_process_tree(None)

    @pytest.mark.asyncio
    async def test_send_turn_async_success(self) -> None:
        """Async daemon turn should write to stdin and read from stdout."""
        mock_proc = MagicMock()
        mock_proc.returncode = None
        mock_proc.stdin = MagicMock()
        mock_proc.stdin.drain = AsyncMock()
        mock_proc.stdout = MagicMock()
        mock_proc.stdout.readline = AsyncMock(side_effect=[b'{"type":"msg"}\n', b""])

        daemon = PersistentStdioDaemon(build_command=lambda: ["mock-cli"])

        with patch(
            "asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc
        ):
            text, _ = await daemon.send_turn_async(
                prompt="Async prompt",
                parse_response_fn=lambda raw: (raw.strip(), None),
                fallback_oneshot_fn=lambda p: ("async oneshot", None),
            )
            assert text == '{"type":"msg"}'

        daemon.stop()
