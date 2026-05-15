from __future__ import annotations

from abc import ABC, abstractmethod


class Tool(ABC):
    """Abstract base class for all tools.

    Each tool declares its name, description, OpenAI-style JSON Schema,
    and the intent types it can produce. The LLM only sees the schema;
    the policy engine handles actual execution.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def json_schema(self) -> dict[str, object]: ...

    @property
    @abstractmethod
    def produces_intent_types(self) -> list[str]: ...
