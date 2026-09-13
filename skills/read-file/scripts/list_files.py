import argparse
import sys
from pathlib import Path

from broskill.processing.path import find_root

MAX_RESULTS = 200


def get_args():
    parser = argparse.ArgumentParser(
        description="List every file matching a glob pattern, relative to the project root."
    )
    parser.add_argument(
        "--pattern",
        required=True,
        type=str,
        help="Glob pattern, relative to the project root (e.g. 'skills/*/references/*.md').",
    )
    return parser


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

    matches = sorted(m for m in root.glob(pattern) if m.is_file())

    if not matches:
        print(f"no files match pattern: {pattern}")
        return

    truncated = len(matches) > MAX_RESULTS
    for m in matches[:MAX_RESULTS]:
        print(m.relative_to(root))

    if truncated:
        # printed to stdout, not stderr -- this is a successful (capped) listing,
        # not a failure, and it needs to be seen regardless of exit-code handling
        print(f"\n... {len(matches) - MAX_RESULTS} more matched but were truncated; narrow the pattern.")


if __name__ == "__main__":
    main()
