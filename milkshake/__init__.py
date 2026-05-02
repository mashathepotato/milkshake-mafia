"""Orchestrator: glue Photographer → Sommelier in one call.

Photographer captures + embeds a URL; Sommelier projects that embedding into
the cellar's PCA space and emits canonical `Ingredients` JSON for Barista.
"""
from .taste_url import taste_url

__all__ = ["taste_url"]
