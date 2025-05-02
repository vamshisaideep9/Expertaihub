import os
from together import Together
from dotenv import load_dotenv
load_dotenv()

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
DEFAULT_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
client = Together(api_key=TOGETHER_API_KEY)

def ask_together(prompt_text: str, 
                 model: str = DEFAULT_MODEL,
                 max_tokens: int = 1024,
                 temperature: float = 0.3,
                 top_p: float = 0.9,
                 stop_sequences: list = None) -> str:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt_text}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop_sequences or [],
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"⚠️ Error querying Together API: {e}")
        return "I'm sorry, I encountered an issue processing your request."

