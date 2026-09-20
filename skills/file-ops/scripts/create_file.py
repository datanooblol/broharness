import argparse
import sys
from pathlib import Path

from broskill.processing.path import find_root


def get_args():
    parser = argparse.ArgumentParser(
        description="Create a new file with the given content. Refuses if the file "
                     "already exists -- use update_file.py to modify an existing file."
    )
    parser.add_argument(
        "--path",
        required=True,
        type=str,
        help="Exact file path to create, relative to the project root "
             "(e.g. 'scratch/note.md'). Not a glob pattern.",
    )
    parser.add_argument(
        "--content",
        required=True,
        type=str,
        help="Text content to write to the new file.",
    )
    return parser


def main():
    args = get_args().parse_args()
    path = args.path

    # Guardrail: a legitimate path never needs to leave the project -- reject
    # upfront rather than relying on where the write happens to land.
    if ".." in Path(path).parts:
        print(f"path resolves outside the project root: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        root = find_root()
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    target = root / path

    if target.exists():
        print(f"file already exists: {path} -- use update_file to modify it", file=sys.stderr)
        sys.exit(1)

    if not target.parent.is_dir():
        # No silent mkdir -p -- an LLM-driven tool creating directory
        # structure the user never asked for is a surprising side effect.
        print(f"parent directory does not exist: {target.parent.relative_to(root)}", file=sys.stderr)
        sys.exit(1)

    try:
        target.write_text(args.content, encoding="utf-8")
    except OSError as e:
        print(f"could not write {path}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"created: {path}")


if __name__ == "__main__":
    main()
