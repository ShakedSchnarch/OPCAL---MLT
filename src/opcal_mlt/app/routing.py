"""
Routing Utilities
=================

Router that dispatches to Streamlit pages based on the active stage in OPCAL-Labeler.
Maintains a registry of render functions keyed by workflow stage.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict

from opcal_mlt.domain.enums import Stage


RenderFn = Callable[..., None]


@dataclass
class Route:
    stage: Stage
    render: RenderFn


class Router:
    """
    Maintain a registry of render functions keyed by Stage.

    Methods:
        register: Register a render function for a workflow stage.
        dispatch: Dispatch to the render function for the given stage.
    """

    def __init__(self) -> None:
        self._routes: Dict[Stage, RenderFn] = {}

    def register(self, stage: Stage, render_fn: RenderFn) -> None:
        self._routes[stage] = render_fn

    def dispatch(self, stage: Stage, *args, **kwargs) -> None:
        render_fn = self._routes.get(stage)
        if render_fn is None:
            raise KeyError(f"No route registered for stage: {stage}")
        render_fn(*args, **kwargs)


__all__ = ["Router", "Route", "RenderFn"]
