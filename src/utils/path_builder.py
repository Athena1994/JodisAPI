import os

_root: str = None
_paths: dict[str: str] = {}


def build_path(rel: str, domain: (str | None) = None) -> str:
    if _root is None:
        raise Exception("Path builder not initialized")

    if domain is None:
        return os.path.join(_root, rel)

    if domain not in _paths:
        raise KeyError(f"Domain '{domain}' not found in path builder")

    return os.path.join(_root, _paths[domain], rel)


def initialize(root: str) -> None:
    global _root
    _root = root


def add_domain(name: str, rel_path: str):
    _paths[name] = rel_path
