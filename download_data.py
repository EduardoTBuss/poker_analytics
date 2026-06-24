"""Download the raw Pluribus .phh hand histories used by this project.

The raw dataset (~10k `.phh` files) is NOT tracked in this repository. The
already-parsed output lives in `data/` so a fresh clone runs out of the box.
Run this script only if you want to reprocess everything from scratch with
`Poker_parser.py`.

Dataset source
--------------
phh-dataset by the University of Toronto Computer Poker Research Group:
    https://github.com/uoftcprg/phh-dataset
The relevant subdirectory upstream is `data/pluribus/`, which holds one folder
per session (e.g. `100/`, `100b/`, ...) with individual hands `0.phh`, `1.phh`...
Dataset license: MIT.

This script does a shallow, sparse `git clone` of phh-dataset into a temporary
directory and copies `data/pluribus/*` into a local `./pluribus/` folder, which
is exactly the layout `Poker_parser.py` expects.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PHH_REPO = "https://github.com/uoftcprg/phh-dataset.git"
# Subdirectory inside the upstream repo that contains the Pluribus sessions.
UPSTREAM_SUBDIR = "data/pluribus"
# Local destination expected by Poker_parser.py.
DEST_DIR = Path(__file__).resolve().parent / "pluribus"


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    """Run a subprocess, raising a clear error if it fails."""
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def download_data(dest: Path = DEST_DIR) -> Path:
    """Fetch the raw .phh dataset into ``dest`` (default: ./pluribus).

    Returns the destination path on success. Raises on failure so the caller
    can report a non-zero exit code.
    """
    if shutil.which("git") is None:
        raise RuntimeError(
            "git was not found on PATH. Install git and try again."
        )

    if dest.exists() and any(dest.iterdir()):
        print(f"'{dest}' already exists and is not empty -- nothing to do.")
        print("Delete it first if you want to re-download.")
        return dest

    print(f"Downloading raw .phh dataset from {PHH_REPO}")
    with tempfile.TemporaryDirectory(prefix="phh-dataset-") as tmp:
        clone_dir = Path(tmp) / "phh-dataset"

        print("[1/3] Shallow sparse clone (metadata only, no blobs yet)...")
        _run(
            [
                "git",
                "-c",
                "core.longpaths=true",
                "clone",
                "--depth",
                "1",
                "--filter=blob:none",
                "--sparse",
                PHH_REPO,
                str(clone_dir),
            ]
        )

        print(f"[2/3] Checking out only '{UPSTREAM_SUBDIR}'...")
        _run(["git", "sparse-checkout", "set", UPSTREAM_SUBDIR], cwd=clone_dir)

        src = clone_dir / UPSTREAM_SUBDIR
        if not src.is_dir():
            raise RuntimeError(
                f"Expected '{UPSTREAM_SUBDIR}' in the cloned repo but it was "
                f"not found. Upstream layout may have changed."
            )

        print(f"[3/3] Copying sessions into '{dest}'...")
        # Copy each session folder so the final layout is pluribus/<session>/*.phh
        sessions = sorted(p for p in src.iterdir() if p.is_dir())
        dest.mkdir(parents=True, exist_ok=True)
        for i, session in enumerate(sessions, start=1):
            shutil.copytree(session, dest / session.name, dirs_exist_ok=True)
            print(f"  copied {i}/{len(sessions)}: {session.name}", end="\r")
        print()

    phh_count = sum(1 for _ in dest.rglob("*.phh"))
    print(
        f"Done. {len(sessions)} sessions, {phh_count} .phh files in '{dest}'."
    )
    print("Now run the parser, e.g.:  python main.py")
    return dest


if __name__ == "__main__":
    try:
        download_data()
    except subprocess.CalledProcessError as exc:
        print(f"\nERROR: a git command failed (exit {exc.returncode}).", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001 - top-level CLI guard
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)
