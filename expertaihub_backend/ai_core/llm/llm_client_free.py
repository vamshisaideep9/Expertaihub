import os
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

# Load key from .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DEFAULT_MODEL = "gpt-4o"

def ask_openai(
    prompt_text: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024,
    temperature: float = 0.3,
    top_p: float = 0.9,
    stop_sequences: list[str] | None = None,
) -> str:
    """
    Send a user prompt to OpenAI Chat Completions and return the assistant's reply.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt_text}],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop_sequences,
        )
        return response.choices[0].message.content.strip()

    except OpenAIError as e:
        print(f"⚠️ OpenAI API error: {e}")
        return "I'm sorry, I encountered an issue processing your request."