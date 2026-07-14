"""Directory-plugin entry point for the Chutes Hermes provider."""

from .hermes_chutes_provider import chutes, register


register()

__all__ = ("chutes", "register")
