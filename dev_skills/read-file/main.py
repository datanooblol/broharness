import argparse
import sys
from pathlib import Path

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f', '--file', required=True, help='File to read', type=str,
    )
    return parser

def main():
    parser = get_args()
    args = parser.parse_args()
    path = Path(args.file)
    if not path.is_file():
        print(f"no such file: {path}", file=sys.stderr)
        sys.exit(1)  # nonzero exit -- run_script folds this into tool_result as a refusal/error, same as delete_file's guardrail would
    print(path.read_text(encoding="utf-8"))  # <-- this is the "return value"

if __name__=='__main__':
    main()
