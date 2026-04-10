import subprocess
import sys
from pathlib import Path
from typing import Tuple


def run_in_sandbox(source_path: str, timeout: int = 10) -> Tuple[int, str, str]:
    """Run a Python source file in a sandboxed subprocess and return output."""
    file_path = Path(source_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    process = subprocess.run(
        [sys.executable, str(file_path)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return process.returncode, process.stdout, process.stderr
