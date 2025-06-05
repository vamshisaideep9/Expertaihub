import os
import logging
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

# Set up logging
logger = logging.getLogger(__name__)

# 1. Load environment variables (OPENAI_API_KEY)
load_dotenv()

# 2. Instantiate a synchronous OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DEFAULT_MODEL = "o4-mini"

def ask_openai(
    prompt_text: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024,
    stop_sequences: list[str] | None = None,
    stream: bool = False,
):
    """
    If stream=False, returns a single string.
    If stream=True, returns a generator yielding each token.
    """
    try:
        logger.debug(f"[ask_openai] Calling OpenAI with model={model}, stream={stream}")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt_text}],
            max_completion_tokens=max_tokens,
            stop=stop_sequences,
            stream=stream,
        )
        if stream:
            # Return a generator that yields each token as it arrives
            def token_generator():
                try:
                    for chunk in response:
                        token = getattr(chunk.choices[0].delta, "content", None)
                        if token:
                            yield token
                except Exception as e:
                    logger.error(f"[ask_openai] Error during streaming: {str(e)}", exc_info=True)
                    yield "I apologize, but I encountered an error while generating the response. Please try again."
            return token_generator()
        # Non-streaming path: return the full string
        return response.choices[0].message.content.strip()

    except OpenAIError as e:
        logger.error(f"[ask_openai] OpenAI API error: {str(e)}", exc_info=True)
        error_msg = "I apologize, but I'm having trouble connecting to my language model. Please try again in a moment."
        if stream:
            def error_gen():
                yield error_msg
            return error_gen()
        return error_msg
    except Exception as e:
        logger.error(f"[ask_openai] Unexpected error: {str(e)}", exc_info=True)
        error_msg = "I apologize, but I encountered an unexpected error. Please try again."
        if stream:
            def error_gen():
                yield error_msg
            return error_gen()
        return error_msg
