import pytest
from unittest.mock import patch, AsyncMock
# Assuming cerebras.cloud.sdk might not be installed in the test runner env for pure unit tests
# so we might need to be careful with direct imports if not mocking them away early.
# However, for testing the wrapper, it's often good to have the SDK types available for spec.
from cerebras.cloud.sdk import AsyncCerebras # For type checking/spec if needed
from cerebras.cloud.sdk.errors import APIConnectionError, APIStatusError, RateLimitError # For simulating errors
from app.services.cerebras_ai_service import CerebrasAIService
# from app.core.config import CEREBRAS_API_KEY # CEREBRAS_API_KEY is loaded by the service itself

# This fixture approach for mock_cerebras_sdk_client was in the prompt,
# but it's often simpler to patch AsyncCerebras directly where needed,
# and then configure its return_value (the instance).
# @pytest.fixture
# def mock_cerebras_sdk_client(self):
#     # This mocks the AsyncCerebras class instance's methods
#     mock_client = AsyncMock(spec=AsyncCerebras)
#     mock_client.chat.completions.create = AsyncMock()
#     return mock_client

@pytest.mark.asyncio
async def test_cerebras_service_initialization_with_key(monkeypatch):
    # Ensure CEREBRAS_API_KEY from config is temporarily set for this test if service relies on it
    # monkeypatch.setenv("CEREBRAS_API_KEY", "fake_key_for_test_init") # Option 1
    # Or, pass key directly, which CerebrasAIService supports
    service = CerebrasAIService(api_key="fake_key_for_test_init")
    assert service.is_active
    assert service.client is not None
    # Test closing (important for async client)
    # If client is a mock, ensure close is also mocked if called by service.close_client()
    if hasattr(service.client, 'close') and callable(service.client.close):
         await service.close_client()
    # If AsyncCerebras itself is patched, ensure the mock has a close method.

@pytest.mark.asyncio
async def test_cerebras_service_initialization_without_key(monkeypatch):
    # Ensure CEREBRAS_API_KEY from config is None
    monkeypatch.setattr("app.services.cerebras_ai_service.CEREBRAS_API_KEY", None)
    service = CerebrasAIService(api_key=None) # Explicitly pass None
    assert not service.is_active
    assert service.client is None
    # No client to close in this case

@pytest.mark.asyncio
@patch("app.services.cerebras_ai_service.AsyncCerebras") # Patch the AsyncCerebras class where it's imported by the service
async def test_get_chat_completion_success(MockAsyncCerebras):
    # Configure the mock instance that AsyncCerebras() will return
    mock_sdk_instance = AsyncMock(spec=AsyncCerebras) # This is what self.client will be
    mock_sdk_instance.chat.completions.create = AsyncMock() # Mock the method we expect to call
    MockAsyncCerebras.return_value = mock_sdk_instance # When new AsyncCerebras() is called, it returns our mock_sdk_instance

    mock_response_data = {"id": "chatcmpl-123", "choices": [{"message": {"content": "Test suggestion"}}], "model": "llama3.1-8b"}

    # Mock for the Pydantic-like model structure if SDK returns such objects
    class MockSdkCompletionResponse:
        def model_dump(self): return mock_response_data
        # If it's just a dict, this class isn't needed and direct dict return is fine.

    mock_sdk_instance.chat.completions.create.return_value = MockSdkCompletionResponse()

    # Instantiate service; it will use the mocked AsyncCerebras
    service = CerebrasAIService(api_key="fake_key_for_test")
    assert service.client == mock_sdk_instance # Check if the mock was injected

    messages = [{"role": "user", "content": "Hello"}]
    kwargs_to_pass = {"temperature": 0.5}
    result = await service.get_chat_completion(messages=messages, model="llama3.1-8b", **kwargs_to_pass)

    assert result == mock_response_data
    mock_sdk_instance.chat.completions.create.assert_awaited_once_with(
        messages=messages, model="llama3.1-8b", temperature=0.5
    )
    await service.close_client()


@pytest.mark.asyncio
@patch("app.services.cerebras_ai_service.AsyncCerebras")
async def test_get_chat_completion_api_connection_error(MockAsyncCerebras):
    mock_sdk_instance = AsyncMock(spec=AsyncCerebras)
    mock_sdk_instance.chat.completions.create = AsyncMock(side_effect=APIConnectionError(request=None)) # Simulate an error
    MockAsyncCerebras.return_value = mock_sdk_instance

    service = CerebrasAIService(api_key="fake_key_for_test")
    messages = [{"role": "user", "content": "Hello"}]
    result = await service.get_chat_completion(messages=messages, model="llama3.1-8b")

    assert result is None # Expect None on error as per service logic
    await service.close_client()

@pytest.mark.asyncio
@patch("app.services.cerebras_ai_service.AsyncCerebras")
async def test_get_chat_completion_rate_limit_error(MockAsyncCerebras):
    mock_sdk_instance = AsyncMock(spec=AsyncCerebras)
    # Simulate RateLimitError; ensure it's a valid exception type the SDK might raise
    mock_sdk_instance.chat.completions.create = AsyncMock(side_effect=RateLimitError("Rate limit exceeded", request=None, response=None))
    MockAsyncCerebras.return_value = mock_sdk_instance

    service = CerebrasAIService(api_key="fake_key_for_test")
    messages = [{"role": "user", "content": "Hello"}]
    result = await service.get_chat_completion(messages=messages, model="llama3.1-8b")

    assert result is None
    await service.close_client()

@pytest.mark.asyncio
@patch("app.services.cerebras_ai_service.AsyncCerebras")
async def test_get_chat_completion_api_status_error(MockAsyncCerebras):
    mock_sdk_instance = AsyncMock(spec=AsyncCerebras)
    # Simulate APIStatusError; ensure it's a valid exception type
    # The constructor for APIStatusError might need specific arguments based on SDK definition
    # For example: APIStatusError(message, request, response, status_code, body)
    # Simplified for this example:
    mock_sdk_instance.chat.completions.create = AsyncMock(side_effect=APIStatusError("API error", response="Mock response", status_code=500, request=None))
    MockAsyncCerebras.return_value = mock_sdk_instance

    service = CerebrasAIService(api_key="fake_key_for_test")
    messages = [{"role": "user", "content": "Hello"}]
    result = await service.get_chat_completion(messages=messages, model="llama3.1-8b")

    assert result is None
    await service.close_client()

@pytest.mark.asyncio
@patch("app.services.cerebras_ai_service.AsyncCerebras")
async def test_get_chat_completion_unexpected_error(MockAsyncCerebras):
    mock_sdk_instance = AsyncMock(spec=AsyncCerebras)
    mock_sdk_instance.chat.completions.create = AsyncMock(side_effect=Exception("Unexpected general error"))
    MockAsyncCerebras.return_value = mock_sdk_instance

    service = CerebrasAIService(api_key="fake_key_for_test")
    messages = [{"role": "user", "content": "Hello"}]
    result = await service.get_chat_completion(messages=messages, model="llama3.1-8b")

    assert result is None
    await service.close_client()

@pytest.mark.asyncio
async def test_service_not_active_get_chat_completion(monkeypatch):
    monkeypatch.setattr("app.services.cerebras_ai_service.CEREBRAS_API_KEY", None)
    service = CerebrasAIService(api_key=None)
    assert not service.is_active

    messages = [{"role": "user", "content": "Hello"}]
    result = await service.get_chat_completion(messages=messages)
    assert result is None
    # No client to close here

# Test for close_client on an inactive service (should not error)
@pytest.mark.asyncio
async def test_close_client_inactive_service(monkeypatch):
    monkeypatch.setattr("app.services.cerebras_ai_service.CEREBRAS_API_KEY", None)
    service = CerebrasAIService(api_key=None)
    assert not service.is_active
    await service.close_client() # Should run without error
    assert True # If it didn't raise, it's a pass for this test's purpose
