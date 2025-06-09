import os
from cerebras.cloud.sdk import AsyncCerebras, APIConnectionError, APIStatusError, RateLimitError # Assuming these are the correct exception imports
from app.core.config import CEREBRAS_API_KEY
import logging
from typing import List, Dict, Any, Optional # For type hinting

logger = logging.getLogger(__name__)

# Configure basic logging if not already configured elsewhere (e.g., in main.py or logging_config.py)
# This is just for standalone usability of the service if it were run separately.
# In FastAPI, logging is usually configured globally.
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class CerebrasAIService:
    def __init__(self, api_key: Optional[str] = None):
        # Prioritize passed api_key, then env var from config, then SDK's internal env var reading
        effective_api_key = api_key or CEREBRAS_API_KEY

        if not effective_api_key:
            logger.warning("Cerebras API key is not configured. CerebrasAIService will not be functional.")
            self.client: Optional[AsyncCerebras] = None # Ensure type hint for client
            self.is_active = False
        else:
            try:
                # The SDK defaults to reading CEREBRAS_API_KEY from env if api_key is not passed to AsyncCerebras constructor.
                # Passing it explicitly is also fine.
                self.client = AsyncCerebras(api_key=effective_api_key, max_retries=3) # Set some defaults
                self.is_active = True
                logger.info("CerebrasAIService initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize AsyncCerebras client: {e}")
                self.client = None
                self.is_active = False

    async def close_client(self):
        """Closes the AsyncCerebras client session. Should be called on application shutdown."""
        if self.client:
            try:
                await self.client.close()
                logger.info("AsyncCerebras client closed successfully.")
            except Exception as e:
                logger.error(f"Error closing AsyncCerebras client: {e}")


    async def get_chat_completion(self, messages: List[Dict[str, str]], model: str = "llama3.1-8b", **kwargs) -> Optional[Dict[str, Any]]:
        """
        Gets a chat completion from the Cerebras API.
        :param messages: A list of message dictionaries, e.g., [{"role": "user", "content": "Hello!"}]
        :param model: The model name to use.
        :param kwargs: Additional parameters for the API call (e.g., temperature, max_tokens).
        :return: The API response as a dictionary, or None if an error occurs.
        """
        if not self.is_active or not self.client:
            logger.error("CerebrasAIService is not active or client not initialized. Cannot get chat completion.")
            return None

        try:
            # Ensure client.chat.completions.create is the correct SDK method
            chat_completion_response = await self.client.chat.completions.create(
                messages=messages,
                model=model,
                **kwargs
            )
            # The SDK response object might have a method like .model_dump() or .to_dict()
            # Assuming .model_dump() for Pydantic-based models from SDK
            if hasattr(chat_completion_response, 'model_dump'):
                return chat_completion_response.model_dump()
            elif isinstance(chat_completion_response, dict): # Or if it's already a dict
                return chat_completion_response
            else: # Fallback or log if structure is unexpected
                logger.warning(f"Cerebras API response format unexpected: {type(chat_completion_response)}")
                # Attempt to convert to dict if it has a __dict__ or similar, or just return as is if necessary
                return dict(chat_completion_response) if hasattr(chat_completion_response, '__dict__') else None

        except APIConnectionError as e:
            logger.error(f"Cerebras API Connection Error: {e}")
        except RateLimitError as e:
            logger.error(f"Cerebras API Rate Limit Error: {e}")
        except APIStatusError as e: # Assuming APIStatusError is correctly imported and used by SDK
            logger.error(f"Cerebras API Status Error - Status {e.status_code}: {getattr(e, 'response', 'No response body')}")
        except Exception as e:
            logger.error(f"An unexpected error occurred with Cerebras API during chat completion: {e}")
        return None

# Example of how this service might be managed with FastAPI lifespan events:
#
# global_cerebras_service: Optional[CerebrasAIService] = None
#
# async def lifespan(app: FastAPI):
#     global global_cerebras_service
#     print("FastAPI app starting up...")
#     global_cerebras_service = CerebrasAIService()
#     yield
#     print("FastAPI app shutting down...")
#     if global_cerebras_service:
#         await global_cerebras_service.close_client()
#
# app = FastAPI(lifespan=lifespan)
#
# This would make global_cerebras_service available for dependency injection if needed.
# For now, the service can be instantiated where needed.
# If used in Celery tasks, client closing needs careful management per task or worker lifecycle.
# Celery tasks are often synchronous, so an async client might need an event loop (e.g. asyncio.run).
# Or, use a synchronous Cerebras SDK if available and tasks are not async.
# For now, this service is async.
# If using with Celery, tasks calling this would need to be async or use asyncio.run().
# For example:
# @celery_app.task
# def some_celery_task():
#     service = CerebrasAIService()
#     if service.is_active:
#         response = asyncio.run(service.get_chat_completion(...))
#         asyncio.run(service.close_client()) # Or manage client lifecycle per worker
#     return response
