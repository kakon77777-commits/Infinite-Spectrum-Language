"""Best-effort public-file disclosure guard; never emits matched secret values.

No third-party dependencies. This is not a security audit, history scrub or
proof of non-disclosure. See docs/DATA_PRIVACY_GUIDANCE.md.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re

_TEXT_EXTENSIONS = {
    ".py", ".md", ".txt", ".json", ".jsonl", ".isl", ".mjs",
    ".js", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".sh", ".bat",
}
_EXCLUDED_DIRS = {
    ".git", ".venv", ".pytest_cache", "__pycache__", "node_modules",
    "build", "dist",
}
_SECRET_NAMES = {
    ".npmrc", ".pypirc", "id_rsa", "id_ed25519", "credentials.json",
    "credentials.toml", "secrets.json", "token.json",
}
_SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
_PATTERNS = {
    "personal-email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "credential-token": re.compile(
        r"\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{16,}|"
        r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
        r"(?:AKIA|ASIA)[A-Z0-9]{16}|"
        r"(?:sk_live|rk_live)_[A-Za-z0-9]{18,}|"
        r"xox[baprs]-[A-Za-z0-9-]{12,})\b"
    ),
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "local-user-path": re.compile(
        r"(?:[A-Za-z]:[\\/]+(?:Users|Documents\ and\ Settings|Ai|work)[\\/]+"
        r"|/Users/[A-Za-z0-9_.-]+/|/home/[A-Za-z0-9_.-]+/)", re.IGNORECASE
    ),
    "literal-bearer": re.compile(r"\bBearer\s+[A-Za-z0-9_.-]{24,}\b", re.IGNORECASE),
}


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    line: int
    category: str


def _sensitive_name(path: Path) -> bool:
    n = path.name.lower()
    return (n == ".env" or n.startswith(".env.") and n != ".env.example"
            or n in _SECRET_NAMES or path.suffix.lower() in _SECRET_SUFFIXES
            or any(part.lower() in {".secrets", "secrets", "private-data", "local-data"}
                   for part in path.parts))


def scan(root: Path) -> list[Finding]:
    if not root.is_dir():
        raise ValueError("public working-tree directory is required")
    hits: list[Finding] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in _EXCLUDED_DIRS or part.endswith(".egg-info")
               for part in relative.parts):
            continue
        short = relative.as_posix()
        if path.is_symlink():
            hits.append(Finding(short, 0, "symlink-review-required"))
            continue
        if not path.is_file():
            continue
        if _sensitive_name(relative):
            hits.append(Finding(short, 0, "private-file-name"))
            continue
        if path.suffix.lower() not in _TEXT_EXTENSIONS and path.name not in {
            ".gitignore", "LICENSE", "NOTICE", "Dockerfile"
        }:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="strict")
        except UnicodeError:
            hits.append(Finding(short, 0, "invalid-utf8-text"))
            continue
        for lineno, line in enumerate(content.splitlines(), start=1):
            for category, pattern in _PATTERNS.items():
                if pattern.search(line):
                    hits.append(Finding(short, lineno, category))
    return sorted(set(hits))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check public tree for obvious disclosure patterns")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)
    try:
        findings = scan(args.root)
    except (OSError, ValueError) as exc:
        print(f"PUBLIC SURFACE CHECK ERROR: {type(exc).__name__}")
        return 2
    if findings:
        print(f"PUBLIC SURFACE CHECK FAIL ({len(findings)} findings):")
        for item in findings:
            print(f"{item.path}:{item.line} [{item.category}]")
        return 1
    print("PUBLIC SURFACE CHECK PASS (source files only; Git metadata and binary artifacts not covered)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
