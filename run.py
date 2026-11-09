#!/usr/bin/env python3
"""Entry point: python <skill>/run.py <command> ... (run it from your project folder)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

if __name__ == '__main__':
    try:
        from stickhistory.cli import main
    except ImportError as e:
        sys.exit(f'Missing dependency ({e}). Install with: pip install -r {pathlib.Path(__file__).resolve().parent / "requirements.txt"}')
    main()
