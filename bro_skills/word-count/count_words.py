import sys
from pathlib import Path


def main() -> None:
    path = Path(sys.argv[1])
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        print(f"{i}: {len(line.split())}")


if __name__ == "__main__":
    main()
