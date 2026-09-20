import argparse
import sys
from pathlib import Path

from broskill.processing.path import find_root

MAX_MATCHES_SHOWN = 20


def get_args():
    parser = argparse.ArgumentParser(
        description="Read exactly one file's content, found via a glob pattern that "
                     "must match a single file."
    )
    parser.add_argument(
        "--pattern",
        required=True,
        type=str,
        help="Glob pattern, relative to the project root, that matches exactly one file "
             "(e.g. 'skills/tell-joke/references/dad-joke.md').",
    )
    return parser


def main():
    args = get_args().parse_args()
    pattern = args.pattern

    # Guardrail: a legitimate pattern never needs to leave the project -- reject
    # upfront rather than relying on where glob happens to land.
    if ".." in Path(pattern).parts:
        print(f"pattern resolves outside the project root: {pattern}", file=sys.stderr)
        sys.exit(1)

    try:
        root = find_root()
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    try:
        matches = sorted(root.glob(pattern))
    except ValueError as e:
        # e.g. "**" written as part of a name instead of its own path
        # component ("**foo.md" instead of "**/foo.md") -- a real glob
        # syntax error, not a "nothing matched" case.
        print(f"invalid glob pattern: {pattern} ({e})", file=sys.stderr)
        sys.exit(1)

    if not matches:
        print(f"no file matches pattern: {pattern}", file=sys.stderr)
        sys.exit(1)

    if len(matches) > 1:
        shown = "\n".join(f"- {m.relative_to(root)}" for m in matches[:MAX_MATCHES_SHOWN])
        more = len(matches) - MAX_MATCHES_SHOWN
        if more > 0:
            shown += f"\n... and {more} more"
        print(
            f"pattern matches {len(matches)} files, expected exactly one:\n{shown}",
            file=sys.stderr,
        )
        sys.exit(1)

    target = matches[0]
    if not target.is_file():
        print(f"matched path is a directory, not a file: {target.relative_to(root)}", file=sys.stderr)
        sys.exit(1)

    try:
        print(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as e:
        print(f"could not read {target.relative_to(root)}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
