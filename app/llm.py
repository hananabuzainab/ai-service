
import os
import json

from google import genai
from google.genai import types
from dotenv import load_dotenv
from copy import deepcopy

load_dotenv()


# --------------------------------------------------
# Configuration
# --------------------------------------------------

MODEL = os.getenv(
    "LLM_MODEL",
    "gemini-3.5-flash-lite"
)

MAX_OUTPUT_TOKENS = 4000
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
    for the legacy Gemini response_schema parameter.

    Resolve internal references and remove
    additionalProperties recursively.
    """

    if hasattr(response_schema, "model_json_schema"):
        schema = response_schema.model_json_schema()

    elif isinstance(response_schema, dict):
        schema = deepcopy(response_schema)

    else:
        raise TypeError(
            "response_schema must be a Pydantic model "
            "or a JSON schema dictionary."
        )

    definitions = schema.get("$defs", {})

    def resolve_references(value):

        if isinstance(value, dict):

            if "$ref" in value:
                reference = value["$ref"]

                prefix = "#/$defs/"

                if not reference.startswith(prefix):
                    raise ValueError(
                        f"Unsupported schema reference: {reference}"
                    )

                definition_name = reference[len(prefix):]

                if definition_name not in definitions:
                    raise ValueError(
                        f"Schema definition not found: {definition_name}"
                    )

                resolved = deepcopy(
                    definitions[definition_name]
                )

                for key, nested_value in value.items():
                    if key != "$ref":
                        resolved[key] = nested_value

                return resolve_references(resolved)

            return {
                key: resolve_references(nested_value)
                for key, nested_value in value.items()
                if key != "additionalProperties"
                and key not in ("$defs", "$schema")
            }

        if isinstance(value, list):
            return [
                resolve_references(item)
                for item in value
            ]

        return value

    return resolve_references(schema)


# --------------------------------------------------
# Skill extraction JSON schemas
# --------------------------------------------------

SKILL_CATEGORIES = [
    "languages",
    "frameworks",
    "databases",
    "cloud_devops",
    "ml_data",
    "tools",
    "other",
]


def _build_skills_schema(score_field):
    """
    Build a simple JSON schema for Gemini skill extraction.

    score_field can be:
    - confidence_score
    - importance
    """

    return {
        "type": "OBJECT",
        "properties": {
            "skills": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {
                            "type": "STRING",
                        },
                        "category": {
                            "type": "STRING",
                            "enum": SKILL_CATEGORIES,
                        },
                        score_field: {
                            "type": "NUMBER",
                            "minimum": 0,
                            "maximum": 1,
                        },
                    },
                    "required": [
                        "name",
                        "category",
                        score_field,
                    ],
                },
            },
        },
        "required": ["skills"],
    }


def build_resume_skills_schema():
    """
    Build the JSON schema used when extracting
    skills from a resume.
    """

    return _build_skills_schema("confidence_score")


def build_job_skills_schema():
    """
    Build the JSON schema used when extracting
    skills from a job description.
    """

    return _build_skills_schema("importance")


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

    response_schema can be:
    - A dictionary containing a raw JSON schema.
    - A Pydantic model used by the existing workflows.
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

        if isinstance(response_schema, dict):
            # Use response_json_schema for manually
            # defined JSON schemas.
            config_options["response_json_schema"] = (
                response_schema
            )

        elif response_schema is not None:
            # Preserve the existing Pydantic schema path
            # used by the other application workflows.
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
    response_schema=None,
):
    """
    Generate and parse a JSON response.

    No retry is performed.
    Invalid or empty responses raise an error immediately.
    """

    response = _generate_response(
        system_prompt,
        user_message,
        json_mode=True,
        response_schema=response_schema,
    )

    response_text = response.text

    if not response_text:
        raise ValueError(
            "Gemini returned an empty response"
        )

    try:
        result = json.loads(response_text)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Gemini returned invalid JSON: {error}"
        ) from error

    if not isinstance(result, dict):
        raise ValueError(
            "Gemini JSON response must be an object"
        )

    return result
