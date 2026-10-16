#!/usr/bin/env python3
"""QRIS Parser and ASPI Validator entry point.

Backward-compatible launcher that routes to qris_parser.cli.main().
"""

from qris_parser.cli import main

if __name__ == "__main__":
    main()
