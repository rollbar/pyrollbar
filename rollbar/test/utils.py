from __future__ import annotations

from collections.abc import Mapping

def get_public_attrs(obj: Mapping | None) -> dict:
    if obj is None:
        return {}
    return {k: obj[k] for k in obj if not k.startswith('_')}
