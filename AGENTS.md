# ComfyUI-PromptEnhance contributor guide

## Project overview

This repository is a lightweight ComfyUI custom-node package.  The package
entrypoint is `__init__.py`; it exports the node mappings defined in
`prompt_enhance.py`.  The node calls an OpenAI-compatible chat-completions API
using `requests`.

## Working conventions

- Keep the package dependency-light. `requests` is the only runtime dependency
  currently required by the node.
- Preserve node identifiers in `NODE_CLASS_MAPPINGS` unless a compatibility
  change is explicitly intended. Existing ComfyUI workflows use those keys.
- Keep the input schema, return types, and `RETURN_NAMES` aligned with each
  node method's signature and returned tuple.
- Treat API keys as secrets: never log them, put them in example workflows, or
  commit them. User-facing failures should be useful without including request
  authorization data.
- Retain OpenAI-compatible request behavior (`model`, `messages`, and common
  sampling parameters) unless the change is deliberately provider-specific.
- Update `README.md` and the example workflow when a user-visible node,
  parameter, or setup behavior changes.

## Validation

There is no automated test suite yet. For Python-only changes, run:

```bash
python -m py_compile __init__.py prompt_enhance.py
```

For changes that affect node registration or execution, also install the
directory under `ComfyUI/custom_nodes`, start ComfyUI, and confirm both nodes
appear under the `prompt` category. Use a non-production key and endpoint for
any live API smoke test.

## Repository layout

- `prompt_enhance.py`: node definitions, API requests, and mapping dictionaries.
- `__init__.py`: ComfyUI package entrypoint and exports.
- `examples/`: importable workflow and its usage notes.
