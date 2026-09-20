import argparse
import sys
from pathlib import Path

from broskill.processing.path import find_root

MAX_RESULTS = 200


def get_args():
    parser = argparse.ArgumentParser(
        description="List every file or folder matching a glob pattern, relative to the "
                     "project root. Folders are included, not just files -- e.g. 'skills/*' "
                     "lists the folders directly under skills/, not just any loose files there."
    )
    parser.add_argument(
        "--pattern",
        required=True,
        type=str,
        help="Glob pattern, relative to the project root (e.g. 'skills/*/references/*.md').",
    )
    return parser


def _is_noise(path: Path, root: Path) -> bool:
    # Build/cache artifacts, never something a user asking "what's in this
    # directory" wants to see -- excluded regardless of pattern, not just on
    # a recursive one, since __pycache__ can appear at any matched depth.
    return any(
        part == "__pycache__" or part.startswith(".")
        for part in path.relative_to(root).parts
    )


def main():
    args = get_args().parse_args()
    pattern = args.pattern

    # Same guardrail as read_file.py -- never search outside the project.
    if ".." in Path(pattern).parts:
        print(f"pattern resolves outside the project root: {pattern}", file=sys.stderr)
        sys.exit(1)

    try:
        root = find_root()
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    try:
        matches = sorted(m for m in root.glob(pattern) if not _is_noise(m, root))
    except ValueError as e:
        print(f"invalid glob pattern: {pattern} ({e})", file=sys.stderr)
        sys.exit(1)

    if not matches:
        print(f"nothing matches pattern: {pattern}")
        return

    truncated = len(matches) > MAX_RESULTS
    for m in matches[:MAX_RESULTS]:
        rel = m.relative_to(root)
        # trailing "/" marks a folder, same convention as `ls -p` -- lets the
        # model (and the user) tell folders and files apart in the listing.
        print(f"{rel}/" if m.is_dir() else str(rel))

    if truncated:
        # printed to stdout, not stderr -- this is a successful (capped) listing,
        # not a failure, and it needs to be seen regardless of exit-code handling
        print(f"\n... {len(matches) - MAX_RESULTS} more matched but were truncated; narrow the pattern.")


if __name__ == "__main__":
    main()
