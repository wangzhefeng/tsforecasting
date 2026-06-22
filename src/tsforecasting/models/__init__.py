"""Model registry and backend adapters."""

from tsforecasting.models.registry import (
    REGISTRY,
    BuiltModel,
    RegistryEntry,
    RegistryError,
    build_model,
    build_models,
    get_entry,
)

__all__ = [
    "REGISTRY",
    "BuiltModel",
    "RegistryEntry",
    "RegistryError",
    "build_model",
    "build_models",
    "get_entry",
]
