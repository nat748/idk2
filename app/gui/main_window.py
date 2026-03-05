"""Main application window."""
import threading

import customtkinter as ctk

from app.backup.backup_reader import BackupReader
from app.extractors.apps import extract_installed_apps
from app.extractors.device_info import extract_device_info, format_device_info
from app.extractors.restrictions import extract_restrictions_passcode
from app.extractors.screentime import extract_screentime_passcode
from app.extractors.wifi import extract_wifi_networks
from app.gui.apps_frame import AppsFrame
from app.gui.backup_selector import BackupSelector
from app.gui.device_info_frame import DeviceInfoFrame
from app.gui.extras_frame import ExtrasFrame
from app.gui.passcode_frame import PasscodeFrame
from app.gui.styles import COLORS, FONTS, SIZES


class App(ctk.CTk):
    """Main application window for iOS Backup Analyzer."""

    def __init__(self):
        super().__init__()

        self.title("iOS Backup Analyzer")
        self.geometry(f"{SIZES['window_width']}x{SIZES['window_height']}")
        self.minsize(SIZES["min_width"], SIZES["min_height"])

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._reader: BackupReader | None = None

        self._build_ui()
        self.after(200, self._selector.auto_scan)

    def _build_ui(self):
        # Top: Backup selector
        self._selector = BackupSelector(
            self, on_load_callback=self._on_load_backup
        )
        self._selector.pack(fill="x")

        # Separator
        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(fill="x")

        # Tabbed content
        self._tabview = ctk.CTkTabview(
            self,
            fg_color="transparent",
            segmented_button_fg_color=COLORS["bg_card"],
            segmented_button_selected_color=COLORS["primary"],
            segmented_button_unselected_color=COLORS["bg_card"],
        )
        self._tabview.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        # Create tabs
        tab_device = self._tabview.add("Device Info")
        tab_passcode = self._tabview.add("Screen Time")
        tab_apps = self._tabview.add("Apps")
        tab_extras = self._tabview.add("WiFi & More")

        # Tab content frames
        self._device_frame = DeviceInfoFrame(tab_device)
        self._device_frame.pack(fill="both", expand=True)

        self._passcode_frame = PasscodeFrame(tab_passcode)
        self._passcode_frame.pack(fill="both", expand=True)

        self._apps_frame = AppsFrame(tab_apps)
        self._apps_frame.pack(fill="both", expand=True)

        self._extras_frame = ExtrasFrame(tab_extras)
        self._extras_frame.pack(fill="both", expand=True)

        # Status bar
        self._statusbar = ctk.CTkFrame(self, height=28, fg_color=COLORS["bg_card"])
        self._statusbar.pack(fill="x", side="bottom")
        self._statusbar.pack_propagate(False)

        self._status_text = ctk.CTkLabel(
            self._statusbar,
            text="Ready",
            font=FONTS["body_small"],
            text_color=COLORS["text_muted"],
        )
        self._status_text.pack(side="left", padx=12)

    def _on_load_backup(self, path: str, password: str | None):
        """Load backup in background thread."""

        def worker():
            try:
                self._set_status("Loading backup...")

                # Close previous reader
                if self._reader:
                    self._reader.close()

                # Create reader
                self._reader = BackupReader(path, password)

                # Check if encrypted backup needs password
                if self._reader.is_encrypted and not password:
                    self.after(0, lambda: self._selector.set_status(
                        "This backup is encrypted - enter the password and try again",
                        "warning"
                    ))
                    self._set_status("Encrypted backup - password required")
                    return

                # 1. Device Info
                self._set_status("Extracting device info...")
                info = extract_device_info(path)
                info_pairs = format_device_info(info)
                self.after(0, lambda: self._device_frame.populate(info_pairs))

                ios_major = 0
                try:
                    ios_major = int(info.get("product_version", "0").split(".")[0])
                except (ValueError, IndexError):
                    pass

                # 2. Passcode
                self._set_status("Searching for passcode...")
                self.after(0, self._passcode_frame.show_searching)

                def progress_cb(current, total, phase=""):
                    self.after(
                        0,
                        lambda c=current, t=total, p=phase: self._passcode_frame.update_progress(c, t, p),
                    )

                passcode_result = None

                # Try Screen Time first (iOS 12+), then fall back to Restrictions
                if ios_major >= 12 or ios_major == 0:
                    passcode_result = extract_screentime_passcode(
                        self._reader, progress_cb
                    )

                # If Screen Time didn't find it, try Restrictions
                if not passcode_result or not passcode_result.get("found"):
                    restrictions_result = extract_restrictions_passcode(
                        self._reader, progress_cb
                    )
                    if restrictions_result.get("found"):
                        passcode_result = restrictions_result
                    elif not passcode_result:
                        passcode_result = restrictions_result

                # If we still don't have a result, combine info
                if not passcode_result:
                    passcode_result = {
                        "found": False,
                        "error": "No passcode data found in this backup",
                    }

                self.after(
                    0, lambda r=passcode_result: self._passcode_frame.show_result(r)
                )

                # 3. Apps
                self._set_status("Extracting app list...")
                try:
                    apps = extract_installed_apps(self._reader)
                    self.after(0, lambda a=apps: self._apps_frame.populate(a))
                except Exception:
                    self.after(0, lambda: self._apps_frame.populate([]))

                # 4. WiFi & Extras
                self._set_status("Extracting WiFi networks...")
                try:
                    wifi = extract_wifi_networks(self._reader)
                except Exception:
                    wifi = []

                extra = {}
                if self._reader._manifest_db:
                    try:
                        total_files = self._reader._manifest_db.count_files()
                        extra["Total Files in Backup"] = f"{total_files:,}"
                    except Exception:
                        pass

                self.after(
                    0,
                    lambda w=wifi, e=extra: self._extras_frame.populate(w, e),
                )

                # Done
                device_name = info.get("device_name", "Unknown")
                ios_ver = info.get("product_version", "?")
                self._set_status(f"Loaded: {device_name} (iOS {ios_ver})")
                self.after(
                    0,
                    lambda: self._selector.set_status(
                        f"Loaded: {device_name} (iOS {ios_ver})", "success"
                    ),
                )

                # Switch to Screen Time tab
                self.after(0, lambda: self._tabview.set("Screen Time"))

            except Exception as e:
                error_msg = str(e)
                self._set_status(f"Error: {error_msg}")
                self.after(
                    0,
                    lambda msg=error_msg: self._selector.set_status(
                        f"Error: {msg}", "error"
                    ),
                )

        threading.Thread(target=worker, daemon=True).start()

    def _set_status(self, text: str):
        """Update status bar text (thread-safe)."""
        self.after(0, lambda: self._status_text.configure(text=text))
