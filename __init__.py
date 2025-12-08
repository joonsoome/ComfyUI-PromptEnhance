"""
ComfyUI-PromptEnhance

A ComfyUI custom node for enhancing prompts using OpenAI-compatible APIs (like DeepSeek).
This node takes a raw prompt and uses an LLM to enhance it into a more detailed,
visual description suitable for image generation models.

Author: ComfyUI User
Version: 1.0.0
"""

from .prompt_enhance import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
