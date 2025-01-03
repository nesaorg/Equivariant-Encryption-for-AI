import os
import subprocess
import sys
import argparse
from pathlib import Path
import shutil


def run_cmd(cmd: str, *, assert_success: bool = False, capture_output: bool = False) -> subprocess.CompletedProcess:
    """run a shell command and optionally assert success."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            text=True,
            capture_output=capture_output,
            check=assert_success,
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {cmd}\nExit code: {e.returncode}")
        sys.exit(e.returncode)


def check_env() -> None:

    if not (sys.platform.startswith("linux") or sys.platform.startswith("darwin")):
        print("only supports Linux and macOS.")
        sys.exit(1)

    if not shutil.which("conda"):
        print("Conda is not installed..")
        sys.exit(1)

    conda_env = os.environ.get("CONDA_DEFAULT_ENV")
    if not conda_env or conda_env == "base":
        print("Missing env: create and activate a dedicated Conda environment for this project.")
        sys.exit(1)


def install_requirements(requirements_path: Path) -> None:

    if not requirements_path.is_file():
        print(f"Requirements file not found: {requirements_path}")
        sys.exit(1)

    print(f"installing dependencies from {requirements_path}...")
    run_cmd("python -m pip install --upgrade pip", assert_success=True)
    run_cmd(f"python -m pip install -r {requirements_path}", assert_success=True)


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(description="Setup script for installing dependencies.")
    parser.add_argument(
        "--requirements",
        type=Path,
        default=Path("requirements.txt"),
        help="Path to the requirements file (default: requirements.txt).",
    )
    return parser.parse_args()


def main() -> None:

    args = parse_args()
    check_env()
    install_requirements(args.requirements)

    print("Setup completed successfully!")


if __name__ == "__main__":
    main()
