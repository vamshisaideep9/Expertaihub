# ai_core/llm/llm_client.py

import os, logging
from typing import Generator, Iterable, Union

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from openai.types.chat.chat_completion import ChatCompletion as Response

load_dotenv()
logger = logging.getLogger(__name__)

DEFAULT_MODEL            = "o4-mini"
DEFAULT_REASONING_EFFORT = "medium"
DEFAULT_MAX_TOKENS       = 60000

_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    logger.warning("OPENAI_API_KEY missing—ask_openai will fail until it's set.")
    client = None
else:
    client = OpenAI(api_key=_api_key)
_OpenAIResult = Union[str, Generator[str, None, None]]

def _stream_to_generator(resp_stream: Iterable[Response]) -> Generator[str, None, None]:
    try:
        for chunk in resp_stream:
            delta = chunk.output_items[0]
            token = getattr(delta, "text", "")
            if token:
                yield token
    except Exception as e:
        logger.error("[ask_openai] Streaming error: %s", e, exc_info=True)
        yield ("I'm sorry — an error occurred while streaming the answer. "
               "Please retry in a moment.")

def ask_openai(
    prompt_text: str,
    *,
    model: str                      = DEFAULT_MODEL,
    reasoning_effort: str           = DEFAULT_REASONING_EFFORT,
    max_tokens: int                 = DEFAULT_MAX_TOKENS,
    include_reasoning_summary: bool = False,
    stream: bool                    = False,
) -> _OpenAIResult:
    try:
        # Build request payload
        request = {
            "model": model,
            "input": [{"role": "user", "content": prompt_text}],
            "max_output_tokens": max_tokens,
            "reasoning": {"effort": reasoning_effort}
        }
        if include_reasoning_summary:
            request["reasoning"]["summary"] = "auto"

        logger.info("[ask_openai] model=%s, effort=%s, stream=%s, summary=%s",
                    model, reasoning_effort, stream, include_reasoning_summary)

        # Streaming branch
        if stream:
            request["stream"] = True
            resp_stream = client.responses.create(**request)

            def gen_with_summary():
                # 1) Pull off the first event to get the summary
                try:
                    first = next(resp_stream)
                    summary = getattr(first, "reasoning_summary", None)
                    if summary:
                        # emit the summary as Markdown
                        yield f"**Model reasoning:**\n{summary}\n\n"
                    # if that first chunk also has text, emit it
                    delta = first.output_items[0]
                    if getattr(delta, "text", ""):
                        yield delta.text
                except StopIteration:
                    return

                # 2) Now hand off the rest of the tokens
                yield from _stream_to_generator(resp_stream)

            return gen_with_summary()

        # Non-streaming branch
        resp = client.responses.create(**request)
        text = resp.output_text or ""
        if include_reasoning_summary:
            summary = getattr(resp, "reasoning_summary", None)
            if summary:
                text = f"**Model reasoning:**\n{summary}\n\n" + text
        return text.strip()

    except OpenAIError as e:
        logger.error("[ask_openai] OpenAI API error: %s", e, exc_info=True)
    except Exception as e:
        logger.error("[ask_openai] Unexpected error: %s", e, exc_info=True)

    fallback = "I'm sorry, I couldn't reach the language model. Please try again."
    return (token for token in [fallback]) if stream else fallback
