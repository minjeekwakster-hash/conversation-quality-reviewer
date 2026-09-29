"""Download and extract the ABCD v1.1 dataset."""

import subprocess
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
REPO_URL = "https://github.com/asappresearch/abcd.git"


def main():
    DATA_DIR.mkdir(exist_ok=True)

    # Check if data already exists
    if (DATA_DIR / "abcd_v1.1.json.gz").exists():
        print("Dataset already downloaded.")
        return

    print("Cloning ABCD repository (sparse checkout — data only)...")
    tmp_dir = DATA_DIR / "_abcd_repo"

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", REPO_URL, str(tmp_dir)],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(tmp_dir), "sparse-checkout", "set", "data"],
            check=True,
        )

        # Copy data files (skip subdirectories like images/)
        src_data = tmp_dir / "data"
        if src_data.exists():
            for f in src_data.iterdir():
                if f.is_dir():
                    continue
                dest = DATA_DIR / f.name
                if not dest.exists():
                    print(f"  Copying {f.name}...")
                    dest.write_bytes(f.read_bytes())

        print(f"\nDataset files downloaded to {DATA_DIR}/")
        print("Files:")
        for f in sorted(DATA_DIR.iterdir()):
            if not f.name.startswith("_"):
                size = f.stat().st_size
                print(f"  {f.name} ({size:,} bytes)")

    finally:
        # Clean up cloned repo
        if tmp_dir.exists():
            import shutil
            shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    main()
