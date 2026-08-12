import os
from functools import lru_cache

from openai import OpenAI

from api.config import extraction_model_name


@lru_cache
def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for AI extraction.")
    return OpenAI(api_key=api_key)


def call_vision_model(
    system_prompt: str, user_prompt: str, image_url: str, json_schema: dict
) -> str:
    """Calls the configured vision-capable model and returns its raw JSON string."""
    response = _client().chat.completions.create(
        model=extraction_model_name(),
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "extraction", "schema": json_schema, "strict": True},
        },
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("The model returned an empty response.")
    return content
