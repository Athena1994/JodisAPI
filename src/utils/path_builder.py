import os

_root: str = None


def build_path(rel: str) -> str:
    if _root is None:
        raise Exception("Path builder not initialized")
    return os.path.join(_root, rel)


def initialize(root: str) -> None:
    global _root
    _root = root