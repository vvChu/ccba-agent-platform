"""Converter registry for automatic discovery and selection.

Provides a centralized registry for document converters with
automatic selection based on file extension and availability.
"""

from pathlib import Path
from typing import Any

from mdconverter.core.base import BaseConverter


class ConverterRegistry:
    """Registry for document converters.

    Allows converters to be registered by name and provides
    automatic selection based on file extension.
    """

    _converters: dict[str, type[BaseConverter]] = {}
    _priority: dict[str, int] = {}  # Lower number = higher priority

    @classmethod
    def register(
        cls,
        name: str,
        priority: int = 100,
    ) -> Any:
        """Decorator to register a converter class.

        Args:
            name: Unique name for the converter (e.g., 'pandoc', 'llm').
            priority: Selection priority (lower = preferred). Default 100.

        Returns:
            Decorator function.
        """

        def decorator(converter_class: type[BaseConverter]) -> type[BaseConverter]:
            cls._converters[name] = converter_class
            cls._priority[name] = priority
            return converter_class

        return decorator

    @classmethod
    def get(cls, name: str) -> type[BaseConverter] | None:
        """Get a converter class by name.

        Args:
            name: Registered name of the converter.

        Returns:
            Converter class or None if not found.
        """
        return cls._converters.get(name)

    @classmethod
    def create(cls, name: str, output_dir: Path | None = None, **kwargs: Any) -> BaseConverter:
        """Create a converter instance by name.

        Args:
            name: Registered name of the converter.
            output_dir: Optional output directory.
            **kwargs: Additional arguments for converter.

        Returns:
            Converter instance.

        Raises:
            ValueError: If converter name not registered.
        """
        converter_class = cls._converters.get(name)
        if not converter_class:
            raise ValueError(
                f"Unknown converter: {name}. Available: {list(cls._converters.keys())}"
            )
        return converter_class(output_dir=output_dir, **kwargs)

    @classmethod
    def auto_select(
        cls,
        extension: str,
        output_dir: Path | None = None,
        **kwargs: Any,
    ) -> BaseConverter:
        """Automatically select best converter for file extension.

        Args:
            extension: File extension (e.g., '.pdf', '.docx').
            output_dir: Optional output directory.
            **kwargs: Additional arguments for converter.

        Returns:
            Best available converter instance.

        Raises:
            ValueError: If no converter supports the extension.
        """
        extension = extension.lower()

        # Find all converters that support this extension
        candidates: list[tuple[str, int]] = []
        for name, converter_class in cls._converters.items():
            # Create temp instance to check support
            temp = converter_class()
            if temp.supports(extension):
                candidates.append((name, cls._priority.get(name, 100)))

        if not candidates:
            raise ValueError(f"No converter supports extension: {extension}")

        # Sort by priority (lower = better) and select first
        candidates.sort(key=lambda x: x[1])
        best_name = candidates[0][0]

        return cls.create(best_name, output_dir=output_dir, **kwargs)

    @classmethod
    def list_all(cls) -> list[dict[str, Any]]:
        """List all registered converters.

        Returns:
            List of converter info dictionaries.
        """
        result: list[dict[str, Any]] = []
        for name, converter_class in cls._converters.items():
            result.append(
                {
                    "name": name,
                    "class": converter_class.__name__,
                    "priority": cls._priority.get(name, 100),
                    "supported_extensions": getattr(converter_class, "SUPPORTED_EXTENSIONS", set()),
                }
            )
        return result

    @classmethod
    def clear(cls) -> None:
        """Clear all registered converters. Mainly for testing."""
        cls._converters.clear()
        cls._priority.clear()


# Convenience function for registration
def register_converter(name: str, priority: int = 100) -> Any:
    """Convenience decorator for registering converters.

    Args:
        name: Unique name for the converter.
        priority: Selection priority (lower = preferred).

    Returns:
        Decorator function.
    """
    return ConverterRegistry.register(name, priority)
