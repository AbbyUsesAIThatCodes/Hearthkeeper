"""Entry point for the packaged desktop executable."""
from hearthkeeper.desktop import main

if __name__ == "__main__":
    import sys
    try:
        raise SystemExit(main())
    except Exception:
        if len(sys.argv) == 3 and sys.argv[1] == "--smoke-test":
            from pathlib import Path
            import traceback
            output = Path(sys.argv[2]); output.mkdir(parents=True, exist_ok=True)
            (output / "smoke-error.txt").write_text(traceback.format_exc())
            raise SystemExit(1)
        raise
