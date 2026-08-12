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


def _strict_schema(schema: dict) -> dict:
    """Normalizes a pydantic-generated schema for OpenAI's strict structured-output
    mode, which requires every property key to appear in "required" (nullable
    fields stay optional-in-practice via an "anyOf" null branch instead) and
    forbids "default"/extra properties. Applied recursively, including $defs.
    """
    schema = dict(schema)
    if "properties" in schema:
        properties = {key: _strict_schema(value) for key, value in schema["properties"].items()}
        schema["properties"] = properties
        schema["required"] = list(properties.keys())
        schema["additionalProperties"] = False
    if "items" in schema:
        schema["items"] = _strict_schema(schema["items"])
    if "anyOf" in schema:
        schema["anyOf"] = [_strict_schema(sub) for sub in schema["anyOf"]]
    if "$defs" in schema:
        schema["$defs"] = {name: _strict_schema(value) for name, value in schema["$defs"].items()}
    schema.pop("default", None)
    return schema


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
            "json_schema": {
                "name": "extraction",
                "schema": _strict_schema(json_schema),
                "strict": True,
            },
        },
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("The model returned an empty response.")
    return content
