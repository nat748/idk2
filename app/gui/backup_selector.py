"""Backup selection UI component."""
import os
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk

from app.backup.discovery import BackupInfo, discover_backups, probe_backup_path
from app.gui.styles import COLORS, FONTS, PADDING


class BackupSelector(ctk.CTkFrame):
    """
    Header frame for selecting an iOS backup.
    Contains: path entry, browse button, detected backups dropdown,
    password field (if encrypted), and load button.
    """

    def __init__(self, parent, on_load_callback, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_load = on_load_callback
        self._backups: list[BackupInfo] = []
        self._selected_backup: BackupInfo | None = None

        self._build_ui()

    def _build_ui(self):
        # Title
        title = ctk.CTkLabel(
            self,
            text="iOS Backup Analyzer",
            font=FONTS["title"],
            text_color=COLORS["text"],
        )
        title.pack(anchor="w", padx=PADDING["section"], pady=(PADDING["section"], 4))

        subtitle = ctk.CTkLabel(
            self,
            text="Extract Screen Time passcode and device information from Apple device backups",
            font=FONTS["body_small"],
            text_color=COLORS["text_secondary"],
        )
        subtitle.pack(anchor="w", padx=PADDING["section"], pady=(0, PADDING["section"]))

        # Backup path row
        path_frame = ctk.CTkFrame(self, fg_color="transparent")
        path_frame.pack(fill="x", padx=PADDING["section"], pady=PADDING["small"])

        ctk.CTkLabel(
            path_frame,
            text="Backup Path:",
            font=FONTS["label"],
            text_color=COLORS["text_secondary"],
            width=90,
            anchor="w",
        ).pack(side="left")

        self._path_var = tk.StringVar()
        self._path_entry = ctk.CTkEntry(
            path_frame,
            textvariable=self._path_var,
            font=FONTS["body"],
            placeholder_text="Select or browse to an iOS backup...",
            height=34,
        )
        self._path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._browse_btn = ctk.CTkButton(
            path_frame,
            text="Browse",
            font=FONTS["button"],
            width=80,
            height=34,
            command=self._browse,
        )
        self._browse_btn.pack(side="left")

        # Detected backups row
        detected_frame = ctk.CTkFrame(self, fg_color="transparent")
        detected_frame.pack(fill="x", padx=PADDING["section"], pady=PADDING["small"])

        ctk.CTkLabel(
            detected_frame,
            text="Detected:",
            font=FONTS["label"],
            text_color=COLORS["text_secondary"],
            width=90,
            anchor="w",
        ).pack(side="left")

        self._backup_dropdown = ctk.CTkOptionMenu(
            detected_frame,
            values=["Scanning..."],
            font=FONTS["body"],
            height=34,
            command=self._on_backup_selected,
            dynamic_resizing=False,
        )
        self._backup_dropdown.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._refresh_btn = ctk.CTkButton(
            detected_frame,
            text="Refresh",
            font=FONTS["button"],
            width=80,
            height=34,
            command=self._scan_backups,
        )
        self._refresh_btn.pack(side="left")

        # Password row (hidden by default)
        self._password_frame = ctk.CTkFrame(self, fg_color="transparent")

        ctk.CTkLabel(
            self._password_frame,
            text="Password:",
            font=FONTS["label"],
            text_color=COLORS["text_secondary"],
            width=90,
            anchor="w",
        ).pack(side="left")

        self._password_var = tk.StringVar()
        self._password_entry = ctk.CTkEntry(
            self._password_frame,
            textvariable=self._password_var,
            font=FONTS["body"],
            placeholder_text="Enter backup encryption password...",
            show="*",
            height=34,
        )
        self._password_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._show_pw_var = tk.BooleanVar(value=False)
        self._show_pw_btn = ctk.CTkCheckBox(
            self._password_frame,
            text="Show",
            variable=self._show_pw_var,
            font=FONTS["body_small"],
            command=self._toggle_password_visibility,
            width=60,
        )
        self._show_pw_btn.pack(side="left")

        # Load button row
        self._btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._btn_frame.pack(fill="x", padx=PADDING["section"], pady=(PADDING["widget"], PADDING["section"]))
        btn_frame = self._btn_frame

        self._load_btn = ctk.CTkButton(
            btn_frame,
            text="Load Backup",
            font=FONTS["button"],
            height=40,
            width=160,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self._load_backup,
        )
        self._load_btn.pack(side="left")

        self._status_label = ctk.CTkLabel(
            btn_frame,
            text="",
            font=FONTS["body_small"],
            text_color=COLORS["text_muted"],
        )
        self._status_label.pack(side="left", padx=PADDING["section"])

    def _browse(self):
        path = filedialog.askdirectory(title="Select iOS Backup Folder")
        if path:
            self._path_var.set(path)
            info = probe_backup_path(path)
            if info:
                self._selected_backup = info
                if info.is_encrypted:
                    self._show_password_field()
                else:
                    self._hide_password_field()
                self._status_label.configure(
                    text=f"Found: {info.device_name}",
                    text_color=COLORS["success"],
                )
            else:
                self._status_label.configure(
                    text="Not a valid iOS backup directory",
                    text_color=COLORS["error"],
                )

    def _scan_backups(self):
        self._backup_dropdown.configure(values=["Scanning..."])
        self._backup_dropdown.set("Scanning...")
        self._backups = []

        import threading

        def scan():
            backups = discover_backups()
            self.after(0, lambda: self._update_backup_list(backups))

        threading.Thread(target=scan, daemon=True).start()

    def _update_backup_list(self, backups: list[BackupInfo]):
        self._backups = backups
        if backups:
            display_names = [b.display_name for b in backups]
            self._backup_dropdown.configure(values=display_names)
            self._backup_dropdown.set(display_names[0])
            self._on_backup_selected(display_names[0])
        else:
            self._backup_dropdown.configure(values=["No backups found"])
            self._backup_dropdown.set("No backups found")

    def _on_backup_selected(self, choice: str):
        for backup in self._backups:
            if backup.display_name == choice:
                self._selected_backup = backup
                self._path_var.set(backup.path)
                if backup.is_encrypted:
                    self._show_password_field()
                else:
                    self._hide_password_field()
                break

    def _show_password_field(self):
        self._password_frame.pack(
            fill="x",
            padx=PADDING["section"],
            pady=PADDING["small"],
            before=self._btn_frame,
        )

    def _hide_password_field(self):
        self._password_frame.pack_forget()

    def _toggle_password_visibility(self):
        if self._show_pw_var.get():
            self._password_entry.configure(show="")
        else:
            self._password_entry.configure(show="*")

    def _load_backup(self):
        path = self._path_var.get().strip()
        if not path or not os.path.isdir(path):
            self._status_label.configure(
                text="Please select a valid backup path",
                text_color=COLORS["error"],
            )
            return

        password = self._password_var.get() if self._password_var.get() else None
        self._status_label.configure(
            text="Loading...", text_color=COLORS["info"]
        )
        self._load_btn.configure(state="disabled")

        self._on_load(path, password)

    def set_status(self, text: str, color: str = "text_muted"):
        self._status_label.configure(text=text, text_color=COLORS.get(color, color))
        self._load_btn.configure(state="normal")

    def auto_scan(self):
        """Trigger initial scan on startup."""
        self._scan_backups()
