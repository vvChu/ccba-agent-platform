"""
Plugin Manager.

Handles discovery and loading of plugins via entry points.
"""

import importlib.metadata
import logging
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class Plugin(Protocol):
    """Protocol that all plugins must implement."""

    def register(self) -> None:
        """Register the plugin components."""
        ...


class PluginManager:
    """Manages plugin discovery and loading."""

    def __init__(self, group: str = "mdconverter.plugins") -> None:
        """Initialize plugin manager."""
        self.group = group
        self.plugins: dict[str, Plugin] = {}

    def load_plugins(self) -> None:
        """Load all registered plugins."""
        entry_points_all = importlib.metadata.entry_points()

        # Python 3.10+ has select method on EntryPoints
        eps: Any
        if hasattr(entry_points_all, "select"):
            eps = entry_points_all.select(group=self.group)
        else:
            # Fallback for older python (pre 3.9 dict-like return)
            eps = entry_points_all.get(self.group, ())

        for ep in eps:
            try:
                plugin_module = ep.load()
                # Check if module follows protocol or has register function
                if hasattr(plugin_module, "register"):
                    plugin_module.register()
                    self.plugins[ep.name] = plugin_module
                    logger.debug(f"Loaded plugin: {ep.name}")
                else:
                    logger.warning(f"Plugin {ep.name} has no register() function.")
            except Exception as e:
                logger.error(f"Failed to load plugin {ep.name}: {e}")

    def get_plugin(self, name: str) -> Plugin | None:
        """Get a loaded plugin by name."""
        return self.plugins.get(name)
