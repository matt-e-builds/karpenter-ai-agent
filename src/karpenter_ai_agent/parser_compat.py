from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType
from typing import Callable, Tuple, List, Any


def _load_legacy_parser_module() -> ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    legacy_parser_path = repo_root / "parser.py"
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    spec = spec_from_file_location("legacy_root_parser", legacy_parser_path)
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError("Could not load legacy parser.py module.")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_parse_provisioner_yaml() -> Callable[[str], Tuple[List[Any], List[Any]]]:
    try:
        from parser import parse_provisioner_yaml  # type: ignore

        return parse_provisioner_yaml
    except (ModuleNotFoundError, ImportError):
        module = _load_legacy_parser_module()
        parse_fn = getattr(module, "parse_provisioner_yaml", None)
        if parse_fn is None:
            raise ModuleNotFoundError("parse_provisioner_yaml was not found in parser.py.")
        return parse_fn


parse_provisioner_yaml = get_parse_provisioner_yaml()
