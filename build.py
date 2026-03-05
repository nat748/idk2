"""
Build script for iOS Backup Analyzer.
Creates platform-specific executables using PyInstaller.

Usage:
    python build.py          # Build for current platform
    python build.py windows  # Force Windows build
    python build.py macos    # Force macOS build
"""
import os
import platform
import subprocess
import sys


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Determine target platform
    if len(sys.argv) > 1:
        target = sys.argv[1].lower()
    else:
        target = "windows" if platform.system() == "Windows" else "macos"

    print(f"Building for: {target}")
    print(f"Python: {sys.executable}")

    # Install dependencies
    print("\nInstalling dependencies...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    )

    # Select spec file
    if target == "windows":
        spec_file = "build_windows.spec"
    elif target == "macos":
        spec_file = "build_macos.spec"
    else:
        print(f"Unknown target: {target}")
        sys.exit(1)

    if not os.path.exists(spec_file):
        print(f"Spec file not found: {spec_file}")
        sys.exit(1)

    # Run PyInstaller
    print(f"\nRunning PyInstaller with {spec_file}...")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", spec_file, "--clean"],
        cwd=os.getcwd(),
    )

    if result.returncode == 0:
        print("\nBuild successful!")
        if target == "windows":
            print("Output: dist/iOS Backup Analyzer.exe")
        else:
            print("Output: dist/iOS Backup Analyzer.app")
    else:
        print(f"\nBuild failed with exit code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
