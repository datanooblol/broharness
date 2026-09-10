import argparse
import sys
from pathlib import Path

DESCRIPTION = "Read a file's contents. Use when the user needs to see what's in a specific file."
ARGS = '{"file": "str"}'  # a plain string here on purpose -- see below

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', required=True, help='File to read')
    return parser.parse_args()

def main():
    args = get_args()
    path = Path(args.file)
    if not path.is_file():
        print(f"no such file: {path}", file=sys.stderr)
        sys.exit(1)  # nonzero exit -- run_script folds this into tool_result as a refusal/error, same as delete_file's guardrail would
    print(path.read_text(encoding="utf-8"))  # <-- this is the "return value"

if __name__=='__main__':
    main()
