#!/usr/bin/env python3
import compileall
import re
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    ROOT_DIR / "main.py",
    ROOT_DIR / "dashboard_server.py",
    ROOT_DIR / "requirements.txt",
    ROOT_DIR / "models" / "shape_predictor_68_face_landmarks.dat",
    ROOT_DIR / "yolov8n.pt",
    ROOT_DIR / "modules" / "dashboard.html",
]
RUNTIME_DIRS = [
    ROOT_DIR / "drivers",
    ROOT_DIR / "logs",
    ROOT_DIR / "reports",
]


def check_required_files():
    missing = [path for path in REQUIRED_FILES if not path.exists()]
    if not missing:
        print("Required files: OK")
        return True

    print("Required files: FAILED")
    for path in missing:
        print(f"  Missing: {path.relative_to(ROOT_DIR)}")
    return False


def check_runtime_dirs():
    for path in RUNTIME_DIRS:
        path.mkdir(exist_ok=True)
    print("Runtime directories: OK")
    return True


def check_source_compiles():
    excluded = re.compile(r"(^|/)(venv|venv310|__pycache__|\.git)(/|$)")
    ok = compileall.compile_dir(
        str(ROOT_DIR),
        quiet=1,
        rx=excluded,
    )

    if ok:
        print("Python source compile: OK")
    else:
        print("Python source compile: FAILED")
    return ok


def main():
    checks = [
        check_required_files(),
        check_runtime_dirs(),
        check_source_compiles(),
    ]

    if all(checks):
        print("Smoke check passed.")
        return 0

    print("Smoke check failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
