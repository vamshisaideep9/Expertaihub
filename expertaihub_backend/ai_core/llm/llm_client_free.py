# ai_core/llm/llm_client.py
import os, logging, itertools
from typing import Generator, Iterable, Union, Any

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from openai.types.chat.chat_completion import ChatCompletion as Response

load_dotenv()
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
#  Global defaults
# ──────────────────────────────────────────────────────────────
DEFAULT_MODEL            = "o4-mini"     # 128 k ctx, reasoning-capable
DEFAULT_REASONING_EFFORT = "medium"      # "low" | "medium" | "high"
DEFAULT_MAX_TOKENS       = 60000        # fits in o4-mini's 128 k ctx

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Typing helper
_OpenAIResult = Union[str, Generator[str, None, None]]

def _stream_to_generator(resp_stream: Iterable[Response]) -> Generator[str, None, None]:
    """
    Convert OpenAI's event stream → single-token generator (`str` tokens).
    """
    try:
        for chunk in resp_stream:
            delta = chunk.output_items[0]            # 1st (and only) item
            token = getattr(delta, "text", "")
            if token:
                yield token
    except Exception as e:
        logger.error("[ask_openai] Streaming error: %s", e, exc_info=True)
        yield ("I'm sorry — an error occurred while streaming the answer. "
               "Please retry in a moment.")

# ──────────────────────────────────────────────────────────────
#  Public helper
# ──────────────────────────────────────────────────────────────
def ask_openai(
    prompt_text: str,
    *,
    model: str                     = DEFAULT_MODEL,
    reasoning_effort: str          = DEFAULT_REASONING_EFFORT,  # "low|medium|high"
    max_tokens: int                = DEFAULT_MAX_TOKENS,
    include_reasoning_summary: bool = False,                    # set True if you want it
    stream: bool                   = False,
) -> _OpenAIResult:
    """
    Thin wrapper over the *Responses* API.

    • `stream=False`  → single string
    • `stream=True`   → generator[str]

    All 4 000-line callers keep working untouched.
    """
    try:
        # 1) Build request
        request: dict = {
            "model"            : model,
            "input"            : [{"role": "user", "content": prompt_text}],
            "max_output_tokens": max_tokens,
            "reasoning"        : {
                "effort": reasoning_effort,
                # ask for a summary if caller wants it
                **({"summary": "auto"} if include_reasoning_summary else {}),
            },
            # streaming handled below
        }

        logger.info("[ask_openai] model=%s, tokens=%s, effort=%s, stream=%s, prompt_len=%s",
                    model, max_tokens, reasoning_effort, stream, len(prompt_text))

        # 2) Fire the request
        if stream:
            request["stream"] = True
            resp_stream = client.responses.create(**request)
            return _stream_to_generator(resp_stream)

        # non-streaming
        resp = client.responses.create(**request)
        out  = resp.output_text or ""
        logger.info("[ask_openai] received %s chars (input=%s, reasoning=%s, output=%s tokens)",
                    len(out),
                    resp.usage.input_tokens,
                    resp.usage.output_tokens_details.reasoning_tokens,
                    resp.usage.output_tokens)
        return out.strip()

    # ── Error handling
    except OpenAIError as e:
        logger.error("[ask_openai] OpenAI API error: %s", e, exc_info=True)
    except Exception as e:
        logger.error("[ask_openai] Unexpected error: %s", e, exc_info=True)

    msg = ("I'm sorry, I couldn't reach the language model. "
           "Please try again in a moment.")
    return (token for token in [msg]) if stream else msg
