
import os
import json

from google import genai
from google.genai import types
from dotenv import load_dotenv


load_dotenv()


# --------------------------------------------------
# Configuration
# --------------------------------------------------

MODEL = os.getenv(
    "LLM_MODEL",
    "gemini-3.5-flash-lite"
)

MAX_OUTPUT_TOKENS = 4000
DEFAULT_RETRIES = 2
REQUEST_TIMEOUT_MS = 60000

_client = None


# --------------------------------------------------
# Gemini client
# --------------------------------------------------

def get_client():
    """
    Create the Gemini client only when needed.
    This allows the application to start even
    when the API key is not configured.
    """

    global _client

    if _client is not None:
        return _client

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured"
        )

    _client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=REQUEST_TIMEOUT_MS
        ),
    )

    return _client


# --------------------------------------------------
# Response schema preparation
# --------------------------------------------------

def _prepare_response_schema(response_schema):
    """
    Prepare a Pydantic model or JSON schema
    for Gemini structured output.

    Remove additionalProperties recursively
    because Gemini does not support it in
    the response schema.
    """

    if hasattr(response_schema, "model_json_schema"):
        schema = response_schema.model_json_schema()

    elif isinstance(response_schema, dict):
        schema = response_schema.copy()

    else:
        raise TypeError(
            "response_schema must be a Pydantic model "
            "or a JSON schema dictionary."
        )

    def remove_additional_properties(value):
        if isinstance(value, dict):
            value.pop("additionalProperties", None)

            for nested_value in value.values():
                remove_additional_properties(
                    nested_value
                )

        elif isinstance(value, list):
            for item in value:
                remove_additional_properties(item)

    remove_additional_properties(schema)

    return schema


# --------------------------------------------------
# Gemini request
# --------------------------------------------------

def _generate_response(
    system_prompt,
    user_message,
    json_mode=False,
    response_schema=None,
):
    """
    Send a generation request to Gemini.

    response_schema is optional and can be
    a Pydantic model or a supported JSON schema.
    """

    config_options = {
        "system_instruction": system_prompt,
        "temperature": 0,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
    }

    if json_mode:
        config_options["response_mime_type"] = (
            "application/json"
        )

        if response_schema is not None:
            config_options["response_schema"] = (
                _prepare_response_schema(response_schema)
            )

    elif response_schema is not None:
        raise ValueError(
            "response_schema requires json_mode=True"
        )

    response = get_client().models.generate_content(
        model=MODEL,
        contents=user_message,
        config=types.GenerateContentConfig(
            **config_options
        ),
    )

    return response


# --------------------------------------------------
# Text response
# --------------------------------------------------

def ask_llm(system_prompt, user_message):
    """
    Generate a regular text response from Gemini.
    """

    response = _generate_response(
        system_prompt,
        user_message,
    )

    response_text = response.text

    if not response_text:
        raise ValueError(
            "Gemini returned an empty response"
        )

    return response_text


# --------------------------------------------------
# JSON response
# --------------------------------------------------

def ask_llm_json(
    system_prompt,
    user_message,
    retries=DEFAULT_RETRIES,
    response_schema=None,
):
    """
    Generate and parse a JSON response.

    Retries are used for:
    - Empty responses
    - Invalid JSON
    - JSON responses with an invalid root type

    HTTP/network retry handling is delegated
    to the Google GenAI SDK.
    """

    if (
        isinstance(retries, bool)
        or not isinstance(retries, int)
        or retries < 0
    ):
        raise ValueError(
            "retries must be a non-negative integer"
        )

    last_error = None

    for attempt in range(retries + 1):

        response = _generate_response(
            system_prompt,
            user_message,
            json_mode=True,
            response_schema=response_schema,
        )

        response_text = response.text

        if not response_text:
            last_error = ValueError(
                "Gemini returned an empty response"
            )

        else:
            try:
                result = json.loads(response_text)

                if not isinstance(result, dict):
                    raise ValueError(
                        "Gemini JSON response must be an object"
                    )

                return result

            except (json.JSONDecodeError, ValueError) as error:
                last_error = error

        if attempt < retries:
            continue

    raise ValueError(
        f"Gemini did not return valid JSON after "
        f"{retries + 1} attempts: {last_error}"
    ) from last_error
