"""Explicit guard used by future provider adapters."""

from .adapters import ExternalProviderNotAuthorized, unavailable_provider

__all__ = ["ExternalProviderNotAuthorized", "unavailable_provider"]
