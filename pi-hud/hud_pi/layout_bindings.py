from __future__ import annotations

from typing import Any


def element_bindings(element: dict[str, Any]) -> list[str]:
    bindings: list[str] = []
    fallback_bindings = element.get("fallback_bindings", [])
    if not isinstance(fallback_bindings, list):
        fallback_bindings = []
    for binding in [element.get("binding", "")] + fallback_bindings:
        if isinstance(binding, str) and binding.strip():
            bindings.append(binding.strip())
    row_bindings = element.get("bindings", [])
    if not isinstance(row_bindings, list):
        row_bindings = []
    for binding in row_bindings:
        if isinstance(binding, str) and binding.strip():
            bindings.append(binding.strip())
    for key in ("event_binding", "side_binding"):
        binding = element.get(key)
        if isinstance(binding, str) and binding.strip():
            bindings.append(binding.strip())
    return bindings


def has_path(root: dict[str, Any], path: str) -> bool:
    node: Any = root
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return True
