from pathlib import Path

from .kernels_config import KernelCatalog, KernelDef, KernelRule, load_catalog
from .dpl_pass import inject_custom_kernels
from .extern_primfunc import make_extern_primfunc

__all__ = [
    "KernelCatalog",
    "KernelDef",
    "KernelRule",
    "load_catalog",
    "inject_custom_kernels",
    "make_extern_primfunc",
    "dump_text",
]


def dump_text(text: str, path: "Path | str") -> None:
    """Write text to path, creating parent dirs, and print the path."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    print(f"  -> {p}")
