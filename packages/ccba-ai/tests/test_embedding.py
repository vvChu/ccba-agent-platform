import pytest

from ccba_ai import ai, async_ai


@pytest.mark.fast
@pytest.mark.unit
def test_embedding_sync():
    ai.mock_mode = True
    embeddings = ai.embed("Kiểm tra nhúng văn bản")
    assert len(embeddings) == 1
    assert len(embeddings[0]) == 3072

@pytest.mark.fast
@pytest.mark.unit
def test_embedding_list_sync():
    ai.mock_mode = True
    embeddings = ai.embed(["Text 1", "Text 2"])
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 3072
    assert len(embeddings[1]) == 3072

@pytest.mark.fast
@pytest.mark.unit
@pytest.mark.asyncio
async def test_embedding_async():
    async_ai.mock_mode = True
    embeddings = await async_ai.embed("Kiểm tra nhúng văn bản async")
    assert len(embeddings) == 1
    assert len(embeddings[0]) == 3072


@pytest.mark.fast
@pytest.mark.unit
def test_embedding_arguments_sync():
    from unittest.mock import MagicMock, patch

    from ccba_ai import AIClient

    client = AIClient(base_url="http://fake:1/v1", api_key="fake", mock_mode=False)
    mock_resp = MagicMock()
    mock_item = MagicMock()
    mock_item.embedding = [0.2] * 3072
    mock_resp.data = [mock_item]

    with patch.object(client._client.embeddings, "create", return_value=mock_resp) as mock_create:
        res = client.embed("test text")
        assert len(res) == 1
        assert len(res[0]) == 3072
        mock_create.assert_called_once()
        assert mock_create.call_args.kwargs["model"] == "gemini-embedding-2"
        assert mock_create.call_args.kwargs["extra_body"] == {"drop_params": True}

