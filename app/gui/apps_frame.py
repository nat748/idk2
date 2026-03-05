"""Installed apps display tab."""
import tkinter as tk

import customtkinter as ctk

from app.gui.styles import COLORS, FONTS, PADDING


class AppsFrame(ctk.CTkFrame):
    """Tab displaying the list of installed apps."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._build_placeholder()

    def _build_placeholder(self):
        self._placeholder = ctk.CTkLabel(
            self,
            text="Load a backup to see installed apps",
            font=FONTS["body"],
            text_color=COLORS["text_muted"],
        )
        self._placeholder.pack(expand=True)

    def populate(self, apps: list[dict]):
        """Populate with list of app dicts (bundle_id, name, version)."""
        for widget in self.winfo_children():
            widget.destroy()

        if not apps:
            ctk.CTkLabel(
                self,
                text="No apps found in this backup",
                font=FONTS["body"],
                text_color=COLORS["text_muted"],
            ).pack(expand=True)
            return

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=PADDING["section"], pady=(PADDING["section"], 4))

        ctk.CTkLabel(
            header_frame,
            text=f"Installed Apps ({len(apps)})",
            font=FONTS["subheading"],
            text_color=COLORS["text"],
        ).pack(side="left")

        # Search
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter_apps())
        search = ctk.CTkEntry(
            header_frame,
            textvariable=self._search_var,
            placeholder_text="Search apps...",
            font=FONTS["body"],
            width=250,
            height=30,
        )
        search.pack(side="right")

        # App list
        self._all_apps = apps
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0
        )
        self._scroll.pack(fill="both", expand=True, padx=PADDING["section"], pady=PADDING["small"])

        self._scroll.grid_columnconfigure(0, weight=0, minsize=50)
        self._scroll.grid_columnconfigure(1, weight=1)
        self._scroll.grid_columnconfigure(2, weight=2)

        # Column headers
        for col, (text, weight) in enumerate([("#", 0), ("Name", 1), ("Bundle ID", 2)]):
            ctk.CTkLabel(
                self._scroll,
                text=text,
                font=FONTS["label"],
                text_color=COLORS["text_muted"],
                anchor="w",
            ).grid(row=0, column=col, sticky="w", padx=(0, 12), pady=(0, 4))

        self._render_apps(apps)

    def _render_apps(self, apps: list[dict]):
        """Render app rows in the scroll frame."""
        # Clear existing rows (keep headers at row 0)
        for widget in self._scroll.winfo_children():
            info = widget.grid_info()
            if info and int(info.get("row", 0)) > 0:
                widget.destroy()

        for idx, app in enumerate(apps):
            row = idx + 1
            ctk.CTkLabel(
                self._scroll,
                text=str(row),
                font=FONTS["body_small"],
                text_color=COLORS["text_muted"],
                anchor="w",
            ).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=1)

            ctk.CTkLabel(
                self._scroll,
                text=app.get("name", ""),
                font=FONTS["body"],
                text_color=COLORS["text"],
                anchor="w",
            ).grid(row=row, column=1, sticky="w", padx=(0, 12), pady=1)

            ctk.CTkLabel(
                self._scroll,
                text=app.get("bundle_id", ""),
                font=FONTS["mono"],
                text_color=COLORS["text_secondary"],
                anchor="w",
            ).grid(row=row, column=2, sticky="w", pady=1)

    def _filter_apps(self):
        """Filter displayed apps based on search text."""
        query = self._search_var.get().lower().strip()
        if not query:
            self._render_apps(self._all_apps)
            return
        filtered = [
            app
            for app in self._all_apps
            if query in app.get("name", "").lower()
            or query in app.get("bundle_id", "").lower()
        ]
        self._render_apps(filtered)

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()
        self._build_placeholder()
