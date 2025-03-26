import pytest
from unittest.mock import patch, MagicMock
from llm_duckduckgo_chat import DuckChatModel, DuckChat


@pytest.fixture
def duckchat_model():
    return DuckChatModel("gpt-4o-mini")


def test_execute_without_conversation(duckchat_model):
    prompt = MagicMock()
    prompt.prompt = "Hello, how are you?"
    prompt.system = None
    prompt.options = MagicMock()

    with (
        patch.object(DuckChat, "fetch_vqd", return_value=["test_vqd", "test_hash"]),
        patch.object(DuckChat, "fetch_response") as mock_fetch_response,
    ):
        mock_response = MagicMock()
        mock_response.headers = {"x-vqd-4": "new_vqd", "x-vqd-hash-1": "new_hash"}
        mock_response.iter_lines.return_value = [
            b'data: {"message": "I am fine."}',
            b"data: [DONE]",
        ]
        mock_fetch_response.return_value = mock_response

        response = duckchat_model.execute(prompt, stream=False, response=MagicMock())

        # Collect the final message
        final_message = list(response)[0]

        assert final_message == "I am fine."
        assert prompt.options.vqd == "new_vqd"
        assert prompt.options.vqdhash == "test_hash"


def test_execute_with_conversation(duckchat_model):
    prompt = MagicMock()
    prompt.prompt = "What is the weather?"
    prompt.options = MagicMock()

    conversation = MagicMock()
    conversation.responses = [
        MagicMock(
            prompt=MagicMock(prompt="What is your name?"),
            text=MagicMock(return_value="My name is DuckChat."),
        ),
    ]

    with (
        patch.object(DuckChat, "fetch_vqd", return_value=["test_vqd", "test_hash"]),
        patch.object(DuckChat, "fetch_response") as mock_fetch_response,
    ):
        mock_response = MagicMock()
        mock_response.headers = {"x-vqd-4": "new_vqd", "x-vqd-hash-1": "new_hash"}
        mock_response.iter_lines.return_value = [
            b'data: {"message": "It is sunny."}',
            b"data: [DONE]",
        ]
        mock_fetch_response.return_value = mock_response

        response = duckchat_model.execute(
            prompt, stream=False, response=MagicMock(), conversation=conversation
        )

        # Collect the final message
        final_message = list(response)[0]

        assert final_message == "It is sunny."
        assert prompt.options.vqd == "new_vqd"


def test_fetch_vqd_success():
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"x-vqd-4": "test_vqd", "x-vqd-hash-1": "hash"}
        mock_get.return_value = mock_response

        vqd, vqdhash = DuckChat.fetch_vqd()
        assert vqd == "test_vqd"
        assert vqdhash == vqdhash


def test_fetch_response_success():
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        response = DuckChat.fetch_response(
            "https://example.com", "test_vqd", "hash", "gpt-4o-mini", []
        )
        assert response == mock_response


def test_fetch_response_failure():
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        with pytest.raises(Exception, match="Failed to send message: 400 Bad Request"):
            DuckChat.fetch_response(
                "https://example.com", "test_vqd", "hash", "gpt-4o-mini", []
            )
