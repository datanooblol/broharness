import argparse
import sys
from pathlib import Path

from broskill.processing.path import find_root


def get_args():
    parser = argparse.ArgumentParser(
        description="Delete exactly one existing file, given its exact path. Does not "
                     "accept a glob pattern -- pattern-driven deletion is out of scope, "
                     "on purpose, to keep this from ever deleting more than one file."
    )
    parser.add_argument(
        "--path",
        required=True,
        type=str,
        help="Exact file path to delete, relative to the project root "
             "(e.g. 'scratch/note.md'). Not a glob pattern.",
    )
    return parser


def main():
    args = get_args().parse_args()
    path = args.path

    if ".." in Path(path).parts:
        print(f"path resolves outside the project root: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        root = find_root()
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    target = root / path

    if not target.exists():
        print(f"file does not exist: {path}", file=sys.stderr)
        sys.exit(1)

    if target.is_dir():
        # Directories are out of scope for this pass -- deleting a whole
        # tree is a much bigger blast radius than this tool should have.
        print(f"will not delete a directory: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        target.unlink()
    except OSError as e:
        print(f"could not delete {path}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"deleted: {path}")


if __name__ == "__main__":
    main()
