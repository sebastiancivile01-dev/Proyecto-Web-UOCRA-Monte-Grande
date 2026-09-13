"""Estado local de versiones y claves de cache de hojas."""


def forget_sheet(session: dict, sheet_name: str) -> None:
    session.setdefault("_versiones_hojas", {}).pop(sheet_name, None)
    session.setdefault("_claves_cache_hojas", {}).pop(sheet_name, None)


def remember_sheet(session: dict, sheet_name: str, version: object, cache_key: object) -> None:
    session.setdefault("_versiones_hojas", {})[sheet_name] = version
    session.setdefault("_claves_cache_hojas", {})[sheet_name] = cache_key
