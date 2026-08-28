"""Apply process resource limits before replacing this process with Semgrep."""

from __future__ import annotations

import argparse
import os
import resource
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--memory-bytes", type=int, required=True)
    parser.add_argument("--cpu-seconds", type=int, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if not args.command or args.command[0] != "--" or len(args.command) == 1:
        return 64
    resource.setrlimit(resource.RLIMIT_AS, (args.memory_bytes, args.memory_bytes))
    resource.setrlimit(resource.RLIMIT_CPU, (args.cpu_seconds, args.cpu_seconds))
    os.execvp(args.command[1], args.command[1:])
    return 127


if __name__ == "__main__":
    sys.exit(main())
