"""Configuration loading: ``config/skyscan.yaml`` (+ optional ``config/skyscan.local.yaml``) →
an attribute-access tree (``cfg.mission.stage_a.a2.target_alt_m``)."""
from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any, Iterable

import yaml

from skyscan import REPO_ROOT

DEFAULT_PATH = REPO_ROOT / "config" / "skyscan.yaml"


class Cfg(dict):
    """A dict whose keys are also attributes. Nested dicts are ``Cfg`` too."""

    __slots__ = ()

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"config has no key {name!r}") from None

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def get_path(self, dotted: str, default: Any = None) -> Any:
        node: Any = self
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def to_plain(self) -> dict:
        return _unwrap(self)


def _wrap(obj: Any) -> Any:
    if isinstance(obj, dict):
        return Cfg({str(k): _wrap(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return [_wrap(v) for v in obj]
    return obj


def _unwrap(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _unwrap(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_unwrap(v) for v in obj]
    return obj


def deep_merge(base: dict, over: dict) -> dict:
    """Recursively merge ``over`` into a copy of ``base`` (dicts merge, everything else replaces)."""
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def set_dotted(data: dict, dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    node = data
    for part in parts[:-1]:
        nxt = node.get(part)
        if not isinstance(nxt, dict):
            nxt = node[part] = {}
        node = nxt
    node[parts[-1]] = value


def _expand(obj: Any, subs: dict[str, str]) -> Any:
    if isinstance(obj, str):
        for token, value in subs.items():
            obj = obj.replace(token, value)
        return obj
    if isinstance(obj, dict):
        return {k: _expand(v, subs) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand(v, subs) for v in obj]
    return obj


def load_config(path: str | os.PathLike | None = None, overrides: Iterable[str] | None = None) -> Cfg:
    """Load the YAML config.

    ``path``: explicit file, else ``$SKYSCAN_CONFIG``, else ``config/skyscan.yaml``.
    A sibling ``<stem>.local.yaml`` is merged on top when present (machine-local, gitignored).
    ``overrides``: ``"a.b.c=value"`` strings (value parsed as YAML), applied last.
    ``{world}`` / ``{model}`` in any string expand from ``sim.world_name`` / ``sim.model_name``.
    """
    p = Path(path or os.environ.get("SKYSCAN_CONFIG") or DEFAULT_PATH)
    data = yaml.safe_load(p.read_text()) or {}
    local = p.with_name(p.stem + ".local.yaml")
    if local.exists():
        data = deep_merge(data, yaml.safe_load(local.read_text()) or {})
    for ov in overrides or ():
        key, sep, raw = ov.partition("=")
        if not sep:
            raise ValueError(f"override must look like key.path=value: {ov!r}")
        set_dotted(data, key.strip(), yaml.safe_load(raw))
    sim = data.get("sim") or {}
    data = _expand(data, {"{world}": str(sim.get("world_name", "")), "{model}": str(sim.get("model_name", ""))})
    cfg = _wrap(data)
    cfg["_path"] = str(p)
    return cfg


def repo_path(p: str | os.PathLike) -> Path:
    """Resolve a path from the config: absolute paths stay, relative ones are under the repo root."""
    pp = Path(os.path.expanduser(str(p)))
    return pp if pp.is_absolute() else REPO_ROOT / pp
