import argparse
import sys
from pathlib import Path

from broskill.processing.path import find_root


def get_args():
    parser = argparse.ArgumentParser(
        description="Overwrite an existing file's full content. Refuses if the file "
                     "does not exist -- use create_file.py to make it first."
    )
    parser.add_argument(
        "--path",
        required=True,
        type=str,
        help="Exact file path to update, relative to the project root "
             "(e.g. 'scratch/note.md'). Not a glob pattern.",
    )
    parser.add_argument(
        "--content",
        required=True,
        type=str,
        help="New full text content, replacing everything currently in the file.",
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
        print(f"file does not exist: {path} -- use create_file to make it first", file=sys.stderr)
        sys.exit(1)

    if target.is_dir():
        print(f"path is a directory, not a file: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        target.write_text(args.content, encoding="utf-8")
    except OSError as e:
        print(f"could not write {path}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"updated: {path}")


if __name__ == "__main__":
    main()
