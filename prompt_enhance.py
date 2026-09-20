import json
import logging

import requests


LOGGER = logging.getLogger(__name__)

DEFAULT_PROMPT_TEMPLATE = """
You are a prompt-enhancement assistant for text-to-image models. Transform the
user's prompt into one clear, concrete, production-ready visual description.

Preserve every explicit requirement from the original prompt, including the
subject, count, action, state, named characters or IP, colors, and requested
text. If the request needs a visual solution rather than describing a scene,
first decide on a complete, specific visual concept that satisfies the request.

Describe composition, subjects, environment, lighting, materials, color
palette, camera perspective, and spatial depth when they help make the image
unambiguous. For every text element that must appear in the image, reproduce
the exact text in English double quotation marks and describe its placement,
size, typography, and material. Do not invent text unless it is needed by the
user's request.

Use objective visual language. Do not use metaphors, emotional rhetoric, or
quality tags such as "8K", "masterpiece", or "best quality". Output only the
enhanced prompt, with no preamble, explanation, or Markdown.

User prompt: {prompt}
""".strip()


def _format_prompt(template, prompt):
    """Insert the prompt without interpreting other braces in a custom template."""
    if not template or not template.strip():
        template = DEFAULT_PROMPT_TEMPLATE
    if "{prompt}" in template:
        return template.replace("{prompt}", prompt)
    return f"{template}\n\n{prompt}"


def _extract_enhanced_prompt(response):
    """Validate and extract text from an OpenAI-compatible chat response."""
    try:
        result = response.json()
    except (json.JSONDecodeError, ValueError) as error:
        raise ValueError("The API returned invalid JSON") from error

    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError(
            "The API response did not include choices[0].message.content"
        ) from error

    if not isinstance(content, str) or not content.strip():
        raise ValueError("The API returned an empty or non-text prompt")
    return content.strip()


def _request_enhancement(api_endpoint, api_key, payload, timeout,
                         api_key_header="Authorization", api_key_prefix="Bearer "):
    """Send a chat-completions request without exposing prompt or key contents."""
    headers = {
        "Content-Type": "application/json",
        api_key_header: f"{api_key_prefix}{api_key}",
    }
    try:
        response = requests.post(
            api_endpoint,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout as error:
        raise TimeoutError(f"API request timed out after {timeout} seconds") from error
    except requests.exceptions.RequestException as error:
        raise ConnectionError("API request failed; check the endpoint and credentials") from error

    return _extract_enhanced_prompt(response)


class PromptEnhance:
    """Enhance a raw prompt through an OpenAI-compatible chat-completions API."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Enter the prompt to enhance...",
                }),
                "api_endpoint": ("STRING", {
                    "multiline": False,
                    "default": "https://api.deepseek.com/v1/chat/completions",
                    "placeholder": "OpenAI-compatible chat-completions endpoint",
                }),
                "api_key": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "API key (stored in the workflow)",
                }),
                "model": ("STRING", {
                    "multiline": False,
                    "default": "deepseek-chat",
                    "placeholder": "Model ID, for example deepseek-chat or gpt-4o-mini",
                }),
            },
            "optional": {
                "prompt_template": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_PROMPT_TEMPLATE,
                    "placeholder": "Custom template; use {prompt} for the input prompt",
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "display": "slider",
                }),
                "max_tokens": ("INT", {
                    "default": 2048,
                    "min": 100,
                    "max": 8192,
                    "step": 100,
                    "display": "number",
                }),
                "timeout": ("INT", {
                    "default": 60,
                    "min": 10,
                    "max": 300,
                    "step": 10,
                    "display": "number",
                }),
                "api_key_header": ("STRING", {
                    "multiline": False,
                    "default": "Authorization",
                    "placeholder": "API key header, for example Authorization or api-key",
                }),
                "api_key_prefix": ("STRING", {
                    "multiline": False,
                    "default": "Bearer ",
                    "placeholder": "API key prefix; leave empty when not required",
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("enhanced_prompt",)
    FUNCTION = "enhance_prompt"
    CATEGORY = "prompt"
    OUTPUT_NODE = False

    @staticmethod
    def _validate_inputs(prompt, api_endpoint, api_key, model):
        if not prompt or not prompt.strip():
            return False
        missing = [
            name for name, value in {
                "API endpoint": api_endpoint,
                "API key": api_key,
                "model": model,
            }.items() if not value or not value.strip()
        ]
        if missing:
            raise ValueError(f"{', '.join(missing)} is required")
        return True

    def enhance_prompt(self, prompt, api_endpoint, api_key, model,
                       prompt_template=None, temperature=0.7, max_tokens=2048, timeout=60,
                       api_key_header="Authorization", api_key_prefix="Bearer "):
        """Return a single enhanced prompt."""
        if not self._validate_inputs(prompt, api_endpoint, api_key, model):
            return ("",)

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": _format_prompt(prompt_template, prompt)}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        enhanced_prompt = _request_enhancement(
            api_endpoint, api_key, payload, timeout, api_key_header, api_key_prefix
        )
        LOGGER.info("Prompt enhancement completed (%d input characters)", len(prompt))
        return (enhanced_prompt,)


class PromptEnhanceAdvanced(PromptEnhance):
    """Prompt enhancement with optional system instructions and top-p sampling."""

    @classmethod
    def INPUT_TYPES(cls):
        base_types = super().INPUT_TYPES()
        api_key_header = base_types["optional"].pop("api_key_header")
        api_key_prefix = base_types["optional"].pop("api_key_prefix")
        base_types["optional"]["system_prompt"] = ("STRING", {
            "multiline": True,
            "default": "",
            "placeholder": "Optional system instructions for the LLM",
        })
        base_types["optional"]["top_p"] = ("FLOAT", {
            "default": 1.0,
            "min": 0.0,
            "max": 1.0,
            "step": 0.05,
            "display": "slider",
        })
        # Keep the original advanced-node widget order for saved workflows.
        base_types["optional"]["api_key_header"] = api_key_header
        base_types["optional"]["api_key_prefix"] = api_key_prefix
        return base_types

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("enhanced_prompt", "original_prompt")
    FUNCTION = "enhance_prompt_advanced"
    CATEGORY = "prompt"

    def enhance_prompt_advanced(self, prompt, api_endpoint, api_key, model,
                                prompt_template=None, temperature=0.7, max_tokens=2048,
                                timeout=60, system_prompt="", top_p=1.0,
                                api_key_header="Authorization", api_key_prefix="Bearer "):
        """Return both the enhanced prompt and the original input."""
        if not self._validate_inputs(prompt, api_endpoint, api_key, model):
            return ("", prompt)

        messages = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": _format_prompt(prompt_template, prompt)})
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }
        enhanced_prompt = _request_enhancement(
            api_endpoint, api_key, payload, timeout, api_key_header, api_key_prefix
        )
        LOGGER.info("Advanced prompt enhancement completed (%d input characters)", len(prompt))
        return (enhanced_prompt, prompt)


NODE_CLASS_MAPPINGS = {
    "PromptEnhance": PromptEnhance,
    "PromptEnhanceAdvanced": PromptEnhanceAdvanced,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptEnhance": "Prompt Enhance (LLM)",
    "PromptEnhanceAdvanced": "Prompt Enhance Advanced (LLM)",
}
