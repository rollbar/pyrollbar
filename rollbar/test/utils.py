from collections.abc import Mapping

def get_public_attrs(obj: Mapping) -> dict:
    return {k: obj[k] for k in obj if not k.startswith('_')}
