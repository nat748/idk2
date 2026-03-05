"""
iOS Backup Analyzer
Extract Screen Time passcodes and device information from Apple device backups.
"""
import sys
import os

# Ensure the app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.gui.main_window import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
