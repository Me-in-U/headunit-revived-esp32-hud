from __future__ import annotations

from pathlib import Path, PurePosixPath


def target_path(app_dir: Path, archive_path: str, required_prefix: str) -> Path:
    validate_archive_path(archive_path)
    parts = PurePosixPath(archive_path).parts
    prefix_parts = PurePosixPath(required_prefix).parts
    if len(parts) < len(prefix_parts) or parts[: len(prefix_parts)] != prefix_parts:
        raise ValueError(f"{archive_path} must be under {required_prefix}/")
    relative = Path(*parts)
    target = app_dir / relative
    resolved_app = app_dir.resolve(strict=False)
    resolved_target = target.resolve(strict=False)
    if not is_relative_to(resolved_target, resolved_app):
        raise ValueError(f"target path escapes app dir: {archive_path}")
    return target


def validate_archive_path(path: str) -> None:
    archive_path = PurePosixPath(path)
    if archive_path.is_absolute() or any(part in ("", ".", "..") for part in archive_path.parts):
        raise ValueError(f"unsafe archive path: {path}")
    if "\\" in path:
        raise ValueError(f"archive path must use forward slashes: {path}")


def relative_source(source: Path, repo_root: Path | None) -> str:
    if repo_root is None:
        return str(source)
    try:
        return source.relative_to(repo_root).as_posix()
    except ValueError:
        return str(source)


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
