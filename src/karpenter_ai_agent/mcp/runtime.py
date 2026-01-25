from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Type
from pydantic import BaseModel, ValidationError


@dataclass(frozen=True)
class ToolSpec:
    name: str
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    handler: Callable[[BaseModel], BaseModel]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Tool already registered: {spec.name}")
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise KeyError(f"Tool not found: {name}")
        return self._tools[name]


class LocalMCPClient:
    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def call(self, name: str, payload: Dict[str, Any]) -> BaseModel:
        spec = self._registry.get(name)
        try:
            parsed = spec.input_model.model_validate(payload)
        except ValidationError as exc:  # noqa: BLE001
            raise ValueError(f"Invalid input for tool '{name}': {exc}") from exc

        result = spec.handler(parsed)
        if not isinstance(result, spec.output_model):
            raise TypeError(f"Tool '{name}' returned invalid output type")
        return result
