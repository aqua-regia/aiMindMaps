"""Load DeepSeek prompt templates from config/prompts/*.json."""

import json
import os
from typing import Any, Dict

from config import Config

_CACHE: Dict[str, Dict[str, Any]] = {}
_MTIMES: Dict[str, float] = {}


def _prompts_dir() -> str:
    return Config.PROMPTS_DIR


def _fill(template: str, **kwargs: str) -> str:
    result = template
    for key, value in kwargs.items():
        result = result.replace("{" + key + "}", value)
    return result


def _load_prompt_file(name: str) -> Dict[str, Any]:
    path = os.path.join(_prompts_dir(), f"{name}.json")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Prompt config not found: {path}")

    mtime = os.path.getmtime(path)
    if name in _CACHE and _MTIMES.get(name) == mtime:
        return _CACHE[name]

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    _CACHE[name] = data
    _MTIMES[name] = mtime
    return data


def _operation(name: str, operation: str) -> Dict[str, str]:
    data = _load_prompt_file(name)
    try:
        return data["operations"][operation]
    except KeyError as exc:
        raise KeyError(
            f"Missing operations.{operation} in {name}.json"
        ) from exc


def _user_prompt(name: str, operation: str, **kwargs: str) -> str:
    op = _operation(name, operation)
    if name == "architecture":
        data = _load_prompt_file(name)
        kwargs.setdefault("hld_rules", data.get("rules", ""))
    return _fill(op["user"], **kwargs)


def _system_prompt(name: str, operation: str) -> str:
    return _operation(name, operation)["system"]


# --- Mind map ---

def system_mindmap_generate() -> str:
    return _system_prompt("mindmap", "generate")


def system_mindmap_update() -> str:
    return _system_prompt("mindmap", "update")


def system_mindmap_expand() -> str:
    return _system_prompt("mindmap", "expand")


def prompt_mindmap_generate(text_input: str) -> str:
    return _user_prompt("mindmap", "generate", text_input=text_input)


def prompt_mindmap_update(current_structure: str, user_prompt: str) -> str:
    return _user_prompt(
        "mindmap",
        "update",
        current_structure=current_structure,
        user_prompt=user_prompt,
    )


def prompt_expand_node(node_label: str, context: str) -> str:
    return _user_prompt(
        "mindmap",
        "expand",
        node_label=node_label,
        context=context,
    )


# --- Sequence diagram ---

def system_sequence_generate() -> str:
    return _system_prompt("sequence", "generate")


def system_sequence_update() -> str:
    return _system_prompt("sequence", "update")


def prompt_sequence_generate(text_input: str) -> str:
    return _user_prompt("sequence", "generate", text_input=text_input)


def prompt_sequence_update(current_mermaid: str, user_prompt: str) -> str:
    return _user_prompt(
        "sequence",
        "update",
        current_mermaid=current_mermaid,
        user_prompt=user_prompt,
    )


# --- Flowchart ---

def system_flowchart_generate() -> str:
    return _system_prompt("flowchart", "generate")


def system_flowchart_update() -> str:
    return _system_prompt("flowchart", "update")


def prompt_flowchart_generate(text_input: str) -> str:
    return _user_prompt("flowchart", "generate", text_input=text_input)


def prompt_flowchart_update(current_mermaid: str, user_prompt: str) -> str:
    return _user_prompt(
        "flowchart",
        "update",
        current_mermaid=current_mermaid,
        user_prompt=user_prompt,
    )


# --- Architecture / HLD ---

def hld_architecture_rules() -> str:
    return _load_prompt_file("architecture").get("rules", "")


def system_hld_generate() -> str:
    return _system_prompt("architecture", "generate")


def system_hld_update() -> str:
    return _system_prompt("architecture", "update")


def prompt_hld_generate(text_input: str) -> str:
    return _user_prompt("architecture", "generate", text_input=text_input)


def prompt_hld_update(current_mermaid: str, user_prompt: str) -> str:
    return _user_prompt(
        "architecture",
        "update",
        current_mermaid=current_mermaid,
        user_prompt=user_prompt,
    )
